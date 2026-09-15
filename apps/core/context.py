from django.conf import settings
from wagtail.models import Site

def site_context(request):
    site = Site.find_for_request(request)
    home = site.root_page.specific if site else None
    return {"publication_name": "The Liberty Articulator", "public_origin": settings.PUBLIC_ORIGIN, "branding": home}
