import time
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from redis import Redis
from redis.exceptions import LockNotOwnedError, ConnectionError as RedisConnectionError

@shared_task(autoretry_for=(RedisConnectionError,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def publish_scheduled_pages():
    client = Redis.from_url(f"{settings.REDIS_BASE_URL}/3", socket_timeout=5)
    lock = client.lock("liberty:scheduled-publishing-lock", timeout=330, blocking=False)
    if not lock.acquire(blocking=False):
        return
    try:
        call_command("publish_scheduled", verbosity=0)
        cache.set("scheduler_last_success", time.time(), timeout=600)
    finally:
        try:
            lock.release()
        except LockNotOwnedError:
            pass
        client.close()

@shared_task
def clear_expired_sessions():
    call_command("clearsessions", verbosity=0)
