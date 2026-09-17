"""Curated founding-portfolio presentation for the public archive.

The ten cards are a dated source snapshot from the supplied founding edition.
They are intentionally separate from the live archive query, which remains
permission-filtered and model-driven.
"""
import json
from functools import lru_cache

from .source_layout import CONTENT
from .services import public_articles


@lru_cache(maxsize=1)
def founding_source_records():
    """Return the immutable source-controlled commissioning snapshot."""
    data = json.loads((CONTENT / "journal_data.json").read_text())
    return tuple(data["publications"])


def founding_portfolio(request):
    """Build archive cards without exposing draft-only Wagtail page data.

    Card copy comes only from the reviewed source JSON. A Read URL is attached
    only to a non-planned record whose corresponding ArticlePage is currently
    live, public, and beneath the active site root.
    """
    source_records = founding_source_records()
    slugs = [record["slug"] for record in source_records]
    visible_urls = {
        page.slug: page.get_url(request=request) or ""
        for page in public_articles(request).filter(slug__in=slugs)
    }

    cards = []
    for index, record in enumerate(source_records, start=1):
        card = dict(record)
        card["index"] = f"{index:02d}"
        card["url"] = (
            visible_urls.get(record["slug"], "")
            if record["status"] != "Planned"
            else ""
        )
        cards.append(card)
    return cards
