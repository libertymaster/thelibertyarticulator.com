from django.urls import include, path
from django.contrib import admin
from wagtail.admin import urls as admin_urls
from django.contrib.sitemaps.views import sitemap
from wagtail import urls as wagtail_urls
from wagtail.contrib.sitemaps import Sitemap
from wagtail.documents import urls as document_urls
from apps.core import views as core
from apps.core.branding_views import branding_asset
from apps.journal.views import archive_api

urlpatterns = [
    path("og.png", branding_asset, {"filename": "og.png"}, name="branding-og"),
    path("favicon.svg", branding_asset, {"filename": "favicon.svg"}, name="branding-favicon"),
    # Registered for reverse() during management commands; HostBoundaryMiddleware
    # rejects these routes on every production host except EDITOR_HOST.
    path("admin/", include(admin_urls)),
    path("django-admin/", admin.site.urls),
    path("health/", core.health, name="health"),
    path("ready/", core.ready, name="ready"),
    path("metrics/", core.metrics, name="metrics"),
    path("api/v1/archive/", archive_api, name="archive-api"),
    path("media/<path:path>", core.media_image, name="media-image"),
    path("documents/", include(document_urls)),
    path("sitemap.xml", sitemap, {"sitemaps": {"pages": Sitemap}}, name="sitemap"),
    path("", include(wagtail_urls)),
]
