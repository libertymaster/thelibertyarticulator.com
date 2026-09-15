import logging
import mimetypes
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.utils._os import safe_join
from django.views.decorators.http import require_GET
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, CollectorRegistry, generate_latest, multiprocess

log = logging.getLogger(__name__)

@require_GET
def health(request):
    return JsonResponse({"status": "alive"})

@require_GET
def ready(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        cache.set("readiness", "ok", 10)
        if cache.get("readiness") != "ok":
            raise RuntimeError("cache check failed")
    except Exception:
        log.exception("Readiness dependency failure")
        return JsonResponse({"status": "not_ready"}, status=503)
    return JsonResponse({"status": "ready"})

@require_GET
def metrics(request):
    import os
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
    else:
        registry = REGISTRY
    text = generate_latest(registry)
    try:
        stamp = float(cache.get("scheduler_last_success", 0))
    except Exception:
        stamp = 0
    text += ("# HELP liberty_scheduler_last_success_timestamp_seconds Last successful scheduled publishing task.\n"
             "# TYPE liberty_scheduler_last_success_timestamp_seconds gauge\n"
             f"liberty_scheduler_last_success_timestamp_seconds {stamp}\n").encode()
    return HttpResponse(text, content_type=CONTENT_TYPE_LATEST)

@require_GET
def media_image(request, path):
    """Serve registered images only. Documents use Wagtail's permission-aware serve view."""
    from wagtail.images import get_image_model
    image_model = get_image_model()
    is_editor = request.user.is_authenticated and request.user.has_perm("wagtailadmin.access_admin")
    if path.startswith("original_images/"):
        allowed = is_editor and image_model.objects.filter(file=path).exists()
    elif path.startswith("images/"):
        allowed = image_model.get_rendition_model().objects.filter(file=path).exists()
    else:
        allowed = False
    if not allowed or Path(path).suffix.lower() not in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"}:
        raise Http404
    filename = Path(safe_join(str(settings.MEDIA_ROOT), path))
    if not filename.is_file():
        raise Http404
    response = FileResponse(filename.open("rb"), content_type=mimetypes.guess_type(path)[0] or "application/octet-stream")
    response["X-Content-Type-Options"] = "nosniff"
    return response
