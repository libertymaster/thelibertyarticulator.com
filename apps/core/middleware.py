import logging
from functools import lru_cache
from time import perf_counter

from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.utils.cache import patch_cache_control
from jwt import PyJWKClient, decode
from jwt.exceptions import PyJWTError
from prometheus_client import Counter, Histogram

log = logging.getLogger(__name__)
REQUESTS = Counter("liberty_http_requests_total", "HTTP responses", ["view", "method", "status"])
LATENCY = Histogram("liberty_http_request_duration_seconds", "HTTP response time", ["view"],
                    buckets=(.025, .05, .1, .25, .5, 1, 2.5, 5))

@lru_cache(maxsize=1)
def access_keys():
    return PyJWKClient(f"https://{settings.CF_ACCESS_TEAM_DOMAIN}/cdn-cgi/access/certs", timeout=5)

class HostBoundaryMiddleware:
    """Separate public rendering from the editor URLconf; never trust identity headers alone."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()
        internal = host in {"web", "localhost", "127.0.0.1", "testserver"}
        if host == settings.EDITOR_HOST:
            if settings.REQUIRE_CF_ACCESS and not request.path.startswith("/static/"):
                token = request.headers.get("Cf-Access-Jwt-Assertion", "")
                if not token:
                    return HttpResponseForbidden("Cloudflare Access authentication required.")
                try:
                    key = access_keys().get_signing_key_from_jwt(token)
                    decode(token, key.key, algorithms=["RS256"], audience=settings.CF_ACCESS_AUD,
                           issuer=f"https://{settings.CF_ACCESS_TEAM_DOMAIN}",
                           options={"require": ["exp", "iat", "aud", "iss"]}, leeway=30)
                except (PyJWTError, OSError, ValueError):
                    log.warning("Editor Access assertion rejected")
                    return HttpResponseForbidden("Cloudflare Access assertion rejected.")
            request.urlconf = "config.urls_editor"
        elif internal:
            if not settings.DEBUG and host != "testserver" and request.path not in {"/health/", "/ready/", "/metrics/"}:
                return HttpResponseNotFound()
        elif request.path.startswith(("/admin/", "/django-admin/", "/metrics/")):
            return HttpResponseNotFound()
        # The dev server deliberately exposes the editor on localhost only.
        if settings.DEBUG and internal:
            request.urlconf = "config.urls_development"
        return self.get_response(request)

class ResponsePolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = perf_counter()
        response = self.get_response(request)
        match = request.resolver_match
        name = (match.view_name if match else "unresolved") or "unnamed"
        REQUESTS.labels(name, request.method, str(response.status_code)).inc()
        LATENCY.labels(name).observe(perf_counter() - start)
        if not request.path.startswith("/static/"):
            # Publication visibility remains authoritative at Django; no stale HTML/draft payloads.
            patch_cache_control(response, private=True, no_store=True, max_age=0)
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response
