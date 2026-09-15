import os
from pathlib import Path
from urllib.parse import quote

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parents[2]

def secret(name: str, default: str = "") -> str:
    """Read a mounted secret without printing it. Environment fallback is dev-only."""
    filename = os.environ.get(f"{name}_FILE")
    if filename:
        value = Path(filename).read_text().strip()
    else:
        value = os.environ.get(name, default)
    return value

DEBUG = False
SECRET_KEY = secret("DJANGO_SECRET_KEY")
PUBLIC_HOST = os.environ.get("PUBLIC_HOST", "thelibertyarticulator.com")
EDITOR_HOST = os.environ.get("EDITOR_HOST", "editor.thelibertyarticulator.com")
PUBLIC_ORIGIN = os.environ.get("PUBLIC_ORIGIN", f"https://{PUBLIC_HOST}").rstrip("/")
ALLOWED_HOSTS = [PUBLIC_HOST, EDITOR_HOST, "web", "localhost", "127.0.0.1", "testserver"]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
INSTALLED_APPS = [
    "apps.core", "apps.journal", "wagtail.contrib.forms", "wagtail.contrib.redirects",
    "wagtail.sites", "wagtail.users", "wagtail.snippets", "wagtail.documents",
    "wagtail.images", "wagtail.embeds", "wagtail.search", "wagtail.admin", "wagtail",
    "modelcluster", "taggit", "django.contrib.admin", "django.contrib.auth",
    "django.contrib.contenttypes", "django.contrib.sessions", "django.contrib.messages",
    "django.contrib.staticfiles", "django.contrib.sitemaps",
    "django.contrib.postgres",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.core.middleware.HostBoundaryMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
    "apps.core.middleware.ResponsePolicyMiddleware",
]
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug", "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages",
        "apps.core.context.site_context",
    ]},
}]
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.environ.get("POSTGRES_DB", "liberty_articulator"),
    "USER": os.environ.get("POSTGRES_APP_USER", "liberty_app"),
    "PASSWORD": secret("POSTGRES_APP_PASSWORD"),
    "HOST": os.environ.get("POSTGRES_HOST", "postgres"), "PORT": "5432",
    "CONN_MAX_AGE": 60, "CONN_HEALTH_CHECKS": True,
    "OPTIONS": {"connect_timeout": 5, "options": "-c statement_timeout=15000 -c lock_timeout=5000"},
}}
_redis_password = quote(secret("REDIS_APP_PASSWORD"), safe="")
REDIS_BASE_URL = f"redis://app:{_redis_password}@{os.environ.get('REDIS_HOST', 'redis')}:6379"
CACHES = {"default": {
    "BACKEND": "django.core.cache.backends.redis.RedisCache",
    "LOCATION": f"{REDIS_BASE_URL}/3", "KEY_PREFIX": "liberty",
    "OPTIONS": {"socket_connect_timeout": 3, "socket_timeout": 3},
}}
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
CELERY_BROKER_URL = f"{REDIS_BASE_URL}/1"
CELERY_RESULT_BACKEND = None
CELERY_TASK_IGNORE_RESULT = True
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_TRANSPORT_OPTIONS = {"visibility_timeout": 600, "socket_timeout": 5}
CELERY_TASK_SOFT_TIME_LIMIT = 240
CELERY_TASK_TIME_LIMIT = 300
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
CELERY_TIMEZONE = "UTC"
CELERY_BEAT_SCHEDULE = {
    "publish-and-expire-pages": {
        "task": "apps.journal.tasks.publish_scheduled_pages", "schedule": 60.0,
        "options": {"expires": 55},
    },
    "clear-expired-sessions": {
        "task": "apps.journal.tasks.clear_expired_sessions", "schedule": 86400.0,
    },
}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 14}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Vite handles JS/CSS hashing. Avoid rewriting its module import graph a second time.
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
WHITENOISE_MAX_AGE = 3600
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"
FILE_UPLOAD_PERMISSIONS = 0o640
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
WAGTAIL_SITE_NAME = "The Liberty Articulator"
WAGTAILADMIN_BASE_URL = f"https://{EDITOR_HOST}"
WAGTAILSEARCH_BACKENDS = {"default": {"BACKEND": "wagtail.search.backends.database"}}
WAGTAILIMAGES_MAX_UPLOAD_SIZE = 10 * 1024 * 1024
WAGTAILIMAGES_EXTENSIONS = ["gif", "jpg", "jpeg", "png", "webp", "avif"]
WAGTAILDOCS_SERVE_METHOD = "serve_view"
WAGTAILDOCS_EXTENSIONS = ["pdf", "txt", "csv"]
WAGTAIL_ALLOW_UNICODE_SLUGS = False
X_FRAME_OPTIONS = "SAMEORIGIN"
REQUIRE_CF_ACCESS = False
CF_ACCESS_TEAM_DOMAIN = os.environ.get("CF_ACCESS_TEAM_DOMAIN", "")
CF_ACCESS_AUD = os.environ.get("CF_ACCESS_AUD", "")
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = secret("EMAIL_PASSWORD")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", f"editor@{PUBLIC_HOST}")
LOGGING = {
    "version": 1, "disable_existing_loggers": False,
    "formatters": {"json": {"()": "apps.core.logging.JsonFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "INFO")},
    "loggers": {"django.server": {"handlers": ["console"], "level": "INFO", "propagate": False}},
}
