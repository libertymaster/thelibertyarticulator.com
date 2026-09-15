"""Asset-integrity and pure resolver checks; no Django installation required."""
import hashlib
import json
import struct
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree

import pytest

from apps.core.branding import DEFAULT_ARTWORK_ALT, public_page_url, resolve_branding, web_image_url

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = "https://staging.example.org"


def static_url(name):
    return "/static/" + name


@pytest.mark.parametrize("name", ["og.png", "favicon.svg"])
def test_uploaded_bytes_match_provenance(name):
    entries = json.loads((ROOT / "content/branding/assets.json").read_text())["assets"]
    entry = next(item for item in entries if item["filename"] == name)
    data = (ROOT / entry["path"]).read_bytes()
    assert len(data) == entry["bytes"]
    assert hashlib.sha256(data).hexdigest() == entry["sha256"]
    assert entry["transformation"] == "None; original bytes retained"


def test_png_has_the_advertised_dimensions_and_format():
    data = (ROOT / "static/branding/og.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert data[12:16] == b"IHDR"
    assert struct.unpack(">II", data[16:24]) == (1200, 630)


def test_svg_is_a_self_contained_shape_icon():
    data = (ROOT / "static/branding/favicon.svg").read_text()
    assert "<!DOCTYPE" not in data and "<!ENTITY" not in data
    svg = ElementTree.fromstring(data)
    assert svg.attrib["viewBox"] == "0 0 64 64"
    for node in svg.iter():
        assert node.tag.split("}")[-1] in {"svg", "rect", "circle", "path"}
        for key, value in node.attrib.items():
            assert not key.lower().startswith("on")
            assert "href" not in key.lower() and "url(" not in value.lower()


@pytest.mark.parametrize("home", [None, SimpleNamespace(), SimpleNamespace(artwork_url="", artwork_alt="")])
def test_blank_branding_uses_defaults_without_mutation(home):
    before = vars(home).copy() if home else None
    result = resolve_branding(home, ORIGIN, static_url)
    assert result["image_url"] == ORIGIN + "/static/branding/og.png"
    assert result["image_alt"] == DEFAULT_ARTWORK_ALT
    assert result["image_width"] == 1200 and result["image_height"] == 630
    assert result["image_type"] == "image/png"
    assert result["favicon_url"] == "/static/branding/favicon.svg"
    if home:
        assert vars(home) == before


def test_manifest_hashed_urls_are_not_hardcoded():
    result = resolve_branding(None, ORIGIN, lambda name: "/static/" + name.replace(".", ".abc123."))
    assert result["image_url"].endswith("/og.abc123.png")
    assert result["favicon_url"].endswith("/favicon.abc123.svg")


def test_absolute_static_cdn_is_retained():
    result = resolve_branding(None, ORIGIN, lambda name: "https://static.example.net/" + name)
    assert result["image_url"] == "https://static.example.net/branding/og.png"


@pytest.mark.parametrize("url", ["/og.png", "/static/branding/og.png"])
def test_original_alias_uses_versioned_bundled_file(url):
    result = resolve_branding(SimpleNamespace(artwork_url=url), ORIGIN, static_url)
    assert result["is_default"]
    assert result["image_url"] == ORIGIN + "/static/branding/og.png"


@pytest.mark.parametrize("url, expected", [
    ("/media/custom.png", ORIGIN + "/media/custom.png"),
    ("https://assets.example.org/custom.webp", "https://assets.example.org/custom.webp"),
])
def test_valid_editor_override_retained_without_invented_dimensions(url, expected):
    home = SimpleNamespace(artwork_url=url, artwork_alt="Owner-supplied alternate description")
    result = resolve_branding(home, ORIGIN, static_url)
    assert result["image_url"] == expected
    assert result["image_alt"] == home.artwork_alt
    assert not result["is_default"]
    assert result["image_width"] is None and result["image_height"] is None
    assert result["image_type"] is None


@pytest.mark.parametrize("url", [
    "javascript:alert(1)", "data:image/svg+xml,bad", "//evil.example/p.png", "#fragment",
    "relative.png", "https://name:secret@example.org/image.png", "https://example.org:bad/i.png",
    "/\\evil.example/image.png", " /media/image.png", "/media/image.png\n",
    "https://[broken", "https://example.org/image.png#fragment",
])
def test_unsafe_or_non_image_location_falls_back(url):
    assert web_image_url(url, ORIGIN) is None
    assert resolve_branding(SimpleNamespace(artwork_url=url), ORIGIN, static_url)["is_default"]


def test_default_artwork_alt_can_be_edited():
    result = resolve_branding(SimpleNamespace(artwork_url="", artwork_alt="Edited alt text"), ORIGIN, static_url)
    assert result["image_alt"] == "Edited alt text"


def test_canonical_uses_public_not_editor_origin_and_omits_query():
    assert public_page_url("https://editor.example.org/article/a/?preview=1", ORIGIN) == ORIGIN + "/article/a/"
    assert public_page_url("/archive/?q=history", ORIGIN) == ORIGIN + "/archive/"
    assert public_page_url("", ORIGIN) == ORIGIN + "/"


def test_one_shared_asset_resolver_and_responsive_figure():
    base = (ROOT / "templates/base.html").read_text()
    metadata = (ROOT / "templates/journal/includes/branding_metadata.html").read_text()
    figure = (ROOT / "templates/journal/includes/editorial_artwork.html").read_text()
    body = (ROOT / "templates/imported/layouts/article-04.html").read_text()
    assert 'includes/branding_metadata.html' in base
    assert metadata.count('property="og:image"') == 1
    assert 'name="twitter:image"' in metadata and 'sizes="any"' in metadata
    assert 'publication_branding' in metadata and 'publication_branding' in figure
    assert 'includes/editorial_artwork.html' in body and 'missing-asset' not in body
    assert '.article-figure img { height: auto; }' in (ROOT / "static/css/integration.css").read_text()
