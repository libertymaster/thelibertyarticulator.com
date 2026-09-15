"""Compatibility URLs for the two original, bundled branding filenames."""
from django.http import Http404, HttpResponseRedirect
from django.templatetags.static import static
from django.views.decorators.http import require_safe

from .branding import BRAND_FILES


@require_safe
def branding_asset(request, filename):
    """Redirect GET/HEAD to the configured static asset; never accept an arbitrary path."""
    try:
        asset = BRAND_FILES[filename]
    except KeyError as exc:
        raise Http404("Unknown branding asset") from exc
    response = HttpResponseRedirect(static(asset))
    # Avoid caching this alias across releases. Static-file caching remains controlled by the existing storage/server.
    response["Cache-Control"] = "no-store, max-age=0"
    return response
