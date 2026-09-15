"""Resolve publication artwork without database writes or network requests.

The template tag supplies Django's static() callable, so manifest-based URLs
remain authoritative. This module itself needs only the Python standard library.
"""
from collections.abc import Callable
from typing import Any
from urllib.parse import urljoin, urlsplit

BRAND_FILES = {"og.png": "branding/og.png", "favicon.svg": "branding/favicon.svg"}
DEFAULT_ARTWORK_ALT = (
    "The Liberty Articulator title over faint engraved telescope and microscope motifs"
)


def web_image_url(value: str, origin: str) -> str | None:
    """Accept HTTP(S) or root-relative image URLs, never scripts or credentials."""
    if not value or any(ord(char) <= 32 or ord(char) == 127 or char == "\\" for char in value):
        return None
    try:
        parts = urlsplit(value)
        if parts.fragment:
            return None
        if value.startswith("/") and not value.startswith("//"):
            return urljoin(origin.rstrip("/") + "/", value)
        if parts.scheme in {"http", "https"} and parts.hostname and not (parts.username or parts.password):
            _ = parts.port  # Reject malformed ports rather than emitting an invalid URL.
            return value
    except ValueError:
        return None
    return None


def resolve_branding(home: Any, origin: str, static_url: Callable[[str], str]) -> dict[str, Any]:
    """Preserve a valid editor override; otherwise use the uploaded default artwork.

    Blank fields are not written back to Wagtail. Unknown custom-image dimensions
    and MIME types are omitted rather than borrowed from the bundled PNG.
    """
    candidate = getattr(home, "artwork_url", "") or ""
    custom_url = web_image_url(candidate, origin)
    default_aliases = {"/og.png", "/static/branding/og.png"}
    use_default = not custom_url or candidate in default_aliases
    if use_default:
        local_url = static_url(BRAND_FILES["og.png"])
        image_url = urljoin(origin.rstrip("/") + "/", local_url)
        alt = getattr(home, "artwork_alt", "") or DEFAULT_ARTWORK_ALT
    else:
        image_url = custom_url
        alt = getattr(home, "artwork_alt", "") or "The Liberty Articulator editorial artwork"
    return {
        "image_url": image_url,
        "image_alt": alt,
        "image_width": 1200 if use_default else None,
        "image_height": 630 if use_default else None,
        "image_type": "image/png" if use_default else None,
        "favicon_url": static_url(BRAND_FILES["favicon.svg"]),
        "is_default": use_default,
    }


def public_page_url(page_url: str, origin: str) -> str:
    """Use the configured public origin, not a preview/editor or request Host."""
    path = urlsplit(page_url or "/").path
    # Repeated leading slashes must not be interpreted as another host.
    return origin.rstrip("/") + "/" + path.lstrip("/")
