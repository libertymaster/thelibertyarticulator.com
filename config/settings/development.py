import os
from .base import *  # noqa: F403

DEBUG = True
SECRET_KEY = SECRET_KEY or "development-only-not-for-production-" * 3  # noqa: F405
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "web", "testserver", PUBLIC_HOST, EDITOR_HOST]  # noqa: F405
PUBLIC_ORIGIN = "http://localhost:8080"
WAGTAILADMIN_BASE_URL = "http://localhost:8080"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
REQUIRE_CF_ACCESS = False
CSRF_TRUSTED_ORIGINS = ["http://localhost:8080", "http://127.0.0.1:8080"]
if os.environ.get("USE_SQLITE", "0") == "1":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "dev.sqlite3"}}  # noqa: F405
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    CELERY_TASK_ALWAYS_EAGER = True
