import os
from django.core.exceptions import ImproperlyConfigured
from .base import *  # noqa: F403

if len(SECRET_KEY) < 50:  # noqa: F405
    raise ImproperlyConfigured("DJANGO_SECRET_KEY_FILE must contain at least 50 characters")
for name in ("POSTGRES_APP_PASSWORD", "REDIS_APP_PASSWORD"):
    if not secret(name):  # noqa: F405
        raise ImproperlyConfigured(f"{name}_FILE must contain a non-empty secret")
ALLOWED_HOSTS = [PUBLIC_HOST, EDITOR_HOST, "web", "localhost", "127.0.0.1"]  # noqa: F405
REQUIRE_CF_ACCESS = os.environ.get("REQUIRE_CF_ACCESS", "1") == "1"
if REQUIRE_CF_ACCESS and (not CF_ACCESS_AUD or not CF_ACCESS_TEAM_DOMAIN):  # noqa: F405
    raise ImproperlyConfigured("Set CF_ACCESS_AUD and CF_ACCESS_TEAM_DOMAIN for the editor Access application")
if CF_ACCESS_TEAM_DOMAIN and not CF_ACCESS_TEAM_DOMAIN.endswith(".cloudflareaccess.com"):  # noqa: F405
    raise ImproperlyConfigured("CF_ACCESS_TEAM_DOMAIN must be the team's cloudflareaccess.com hostname")
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r"^health/$", r"^ready/$", r"^metrics/$"]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_TRUSTED_ORIGINS = [f"https://{PUBLIC_HOST}", f"https://{EDITOR_HOST}"]  # noqa: F405
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Narrow, documented exceptions: Wagtail preview needs same-origin framing, and
# domain-wide HSTS/preload requires the domain owner's explicit commitment.
# Revisit on 2026-12-13; see docs/SECURITY.md. All other deployment warnings fail.
SILENCED_SYSTEM_CHECKS = ["security.W005", "security.W019", "security.W021"]
