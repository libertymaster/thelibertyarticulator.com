from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from wagtail.admin import urls as admin_urls
from wagtail.documents import urls as document_urls
from apps.core.views import media_image

urlpatterns = [
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
    path("admin/", include(admin_urls)),
    path("django-admin/", admin.site.urls),
    path("documents/", include(document_urls)),
    path("media/<path:path>", media_image, name="media-image"),
]
