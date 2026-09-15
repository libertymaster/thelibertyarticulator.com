import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlencode

from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

register = template.Library()

@lru_cache(maxsize=1)
def manifest():
    path = settings.BASE_DIR / "static" / "islands" / "manifest.json"
    return json.loads(path.read_text()) if path.exists() else {}

@register.simple_tag
def vite_entry(name):
    data = manifest()
    entry = data.get(name)
    if not entry:
        # Server-rendered content still works before assets are built.
        return ""
    seen, css = set(), []
    def visit(key):
        if key in seen:
            return
        seen.add(key)
        chunk = data[key]
        for child in chunk.get("imports", []):
            visit(child)
        css.extend(chunk.get("css", []))
    visit(name)
    styles = format_html_join("", '<link rel="stylesheet" href="{}">', ((static("islands/" + x),) for x in dict.fromkeys(css)))
    script = format_html('<script type="module" src="{}"></script>', static("islands/" + entry["file"]))
    return format_html("{}{}", styles, script)

@register.simple_tag(takes_context=True)
def page_query(context, number):
    query = context["request"].GET.copy()
    query["page"] = str(number)
    return "?" + query.urlencode()

@register.filter
def era(year):
    from apps.journal.services import year_label
    return year_label(year) if year is not None else ""


@register.simple_tag(takes_context=True)
def source_chrome(context, section):
    """Use published branding, or the verbatim supplied defaults before import."""
    if section not in {"header", "footer"}:
        raise ValueError("Unknown chrome section")
    from apps.journal.source_layout import SourceLayoutStreamBlock, source_pages
    home = context.get("branding")
    value = getattr(home, section + "_layout", None)
    if value:
        return value.render_as_block(context=context.flatten())
    block = SourceLayoutStreamBlock()
    return block.render(block.to_python(source_pages()[section]["sections"]), context=context.flatten())


@register.simple_tag
def article_structured_data(page, canonical_url):
    """Emit model-derived metadata, never an unchecked HTML string from source files."""
    from django.utils.html import json_script
    if page.record_status == "planned":
        return ""
    data = {
        "@context": "https://schema.org", "@type": "ScholarlyArticle",
        "headline": page.title, "description": page.search_description or page.abstract,
        "url": canonical_url, "inLanguage": "en",
        "author": [{"@type": "Organization" if author.name == "The Editors" else "Person", "name": author.name} for author in page.authors.all()],
        "isPartOf": {"@type": "Periodical", "name": "The Liberty Articulator"},
        "creativeWorkStatus": page.get_record_status_display(),
    }
    if page.publication_date:
        data["datePublished"] = page.publication_date.isoformat()
    if page.version_label:
        data["version"] = page.version_label
    # json_script escapes angle brackets and ampersands to prevent closing-tag injection.
    return mark_safe(str(json_script(data)).replace('type="application/json"', 'type="application/ld+json"', 1))


@register.simple_tag(takes_context=True)
def publication_branding(context):
    """Resolve assets at render time, including the home-page preview context."""
    from apps.core.branding import public_page_url, resolve_branding
    assets = resolve_branding(context.get("branding"), settings.PUBLIC_ORIGIN, static)
    page = context.get("page")
    page_url = context.get("canonical_url") or getattr(page, "url", "/") or "/"
    assets["page_url"] = public_page_url(page_url, settings.PUBLIC_ORIGIN)
    return assets
