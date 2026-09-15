from collections import defaultdict
from urllib.parse import urlencode

from django import forms
from django.core.paginator import Paginator
from django.db.models import Q, F
from wagtail.models import Site

from .contracts import (ArchiveFilters, ArchivePayload, ArticleCard, Choice, CitationLink,
                        ChronologyPayload, Facets, SourceItem, SourcesPayload, TimelineEvent)
from .forms import ArchiveForm
from .models import ArticleAuthor, ArticlePage, Series, Subject

PAGE_SIZE = 12

def public_articles(request):
    """Never use latest_revision here. Honor Wagtail live flags and ancestor restrictions."""
    site = Site.find_for_request(request)
    pages = ArticlePage.objects.live().public()
    if site is None:
        return pages.none()
    return pages.descendant_of(site.root_page).select_related("series").prefetch_related("subjects", "authors")

def year_label(year):
    return f"{abs(year)} BCE" if year < 0 else f"{year} CE"

def article_context(page, request):
    # Use this page instance and its clustered children, including unsaved preview revisions.
    sources = list(page.sources.all())
    by_key = {s.key: s for s in sources}
    citations_by_key = defaultdict(list)
    sections, footnotes = [], []
    for block in page.body:
        section = {"kind": block.block_type, "value": block.value, "id": f"passage-{block.id}", "references": []}
        if block.block_type in {"paragraph", "quote"}:
            for offset, ref in enumerate(block.value["references"]):
                source = by_key.get(ref["source_key"])
                if source is None:
                    # Defensive rendering: missing evidence must be visible, not silently discarded.
                    section["references"].append({"missing": True, "source_key": ref["source_key"]})
                    continue
                number = len(footnotes) + 1
                anchor = f"note-{block.id}-{offset}"
                backlink = f"cite-{block.id}-{offset}"
                entry = {"number": number, "anchor": anchor, "backlink": backlink,
                         "source": source, "locator": ref.get("locator", ""), "note": ref.get("note", "")}
                footnotes.append(entry)
                section["references"].append(entry)
                citations_by_key[source.key].append(CitationLink(
                    number=number, anchor=f"#{anchor}", passage_anchor=f"#{section['id']}",
                    locator=entry["locator"], note=entry["note"]))
        sections.append(section)
    for citation in page.imported_citations.all():
        if citation.source_key in by_key:
            citations_by_key[citation.source_key].append(CitationLink(
                number=citation.number, anchor="#" + citation.note_anchor,
                passage_anchor="#" + citation.passage_anchor,
                locator=citation.locator, note=citation.note,
            ))
    payload = SourcesPayload(article_title=page.title, sources=[SourceItem(
        key=s.key, kind=s.kind, title=s.title, authors=s.authors, year=s.year,
        bibliography=s.bibliography, annotation=" | ".join(x for x in [s.use_description, s.verification_status, s.annotation] if x), url=s.url,
        citations=citations_by_key[s.key],
    ) for s in sources])
    return {"sections": sections, "footnotes": footnotes, "bibliography": sources,
            "sources_payload": payload.model_dump(mode="json"),
            "imported_notes": [{"citation": c, "source": by_key.get(c.source_key)} for c in page.imported_citations.all()],
            "canonical_url": page.get_full_url(request), "article_authors": list(page.authors.all())}

def archive_response(request):
    form = ArchiveForm(request.GET)
    valid = form.is_valid()
    data = form.cleaned_data if valid else {}
    base = public_articles(request)
    # Facets derive only from publicly visible pages, never from draft-only metadata.
    facets = Facets(
        subjects=[Choice(value=s.slug, label=s.name) for s in Subject.objects.filter(articles__in=base).distinct()],
        authors=[Choice(value=n, label=n) for n in ArticleAuthor.objects.filter(page__in=base).order_by("name").values_list("name", flat=True).distinct()],
        series=[Choice(value=s.slug, label=s.name) for s in Series.objects.filter(articles__in=base).distinct()],
    )
    for field, choices in [("subject", facets.subjects), ("author", facets.authors), ("series", facets.series)]:
        form.fields[field].widget = forms.Select(choices=[("", "All")] + [(choice.value, choice.label) for choice in choices])
    qs = base
    if data.get("q"):
        qs = qs.filter(Q(title__icontains=data["q"]) | Q(abstract__icontains=data["q"]))
    for field, lookup in [("subject", "subjects__slug"), ("author", "authors__name"), ("series", "series__slug"), ("source_kind", "sources__kind")]:
        if data.get(field):
            qs = qs.filter(**{lookup: data[field]})
    if data.get("status"):
        qs = qs.filter(record_status=data["status"])
    if data.get("published_from"):
        qs = qs.filter(publication_date__gte=data["published_from"])
    if data.get("published_to"):
        qs = qs.filter(publication_date__lte=data["published_to"])
    if data.get("historical_from") is not None:
        qs = qs.filter(historical_end__gte=data["historical_from"])
    if data.get("historical_to") is not None:
        qs = qs.filter(historical_start__lte=data["historical_to"])
    order = {"newest": (F("publication_date").desc(nulls_last=True), "-id"), "oldest": (F("publication_date").asc(nulls_last=True), "id"), "title": ("title", "id")}
    sort = data.get("sort") or "newest"
    qs = qs.order_by(*order[sort]).distinct() if valid else qs.none()
    paginator = Paginator(qs, PAGE_SIZE)
    page = paginator.get_page(data.get("page") or 1)
    cards = [ArticleCard(
        id=a.pk, title=a.title, url=a.get_url(request=request) or "", abstract=a.abstract,
        publication_date=a.publication_date.isoformat() if a.publication_date else "", authors=[x.name for x in a.authors.all()],
        subjects=[s.name for s in a.subjects.all()], series=a.series.name if a.series else "",
        historical_period=(f"{year_label(a.historical_start)} to {year_label(a.historical_end)}" if a.historical_start is not None else ""),
        is_demonstration=a.is_demonstration, discipline=a.discipline,
        article_type=a.article_type, record_status=a.record_status, status_label=a.get_record_status_display(),
        review_status=a.review_status, sources_summary=a.sources_summary, method=a.method,
        display_date=a.display_date, read_time=a.read_time,
    ) for a in page.object_list]
    filters = {k: str(data[k]) if data.get(k) is not None else "" for k in ArchiveFilters.model_fields if k != "sort"}
    errors = [f"{field}: {message}" for field, messages in form.errors.items() for message in messages]
    payload = ArchivePayload(filters=ArchiveFilters(**filters, sort=sort), facets=facets,
                             results=cards, total=paginator.count, page=page.number,
                             pages=paginator.num_pages, page_size=PAGE_SIZE, errors=errors)
    return payload, form

def chronology_payload(page):
    events = list(page.events.all())
    article_ids = {e.related_article_id for e in events if e.related_article_id}
    # Do not expose the title or URL of a related unpublished/restricted page.
    public = {a.pk: a for a in ArticlePage.objects.live().public().filter(pk__in=article_ids)}
    result = []
    for event in sorted(events, key=lambda e: (e.year, e.sort_order or 0, e.key)):
        article = public.get(event.related_article_id)
        result.append(TimelineEvent(
            key=event.key, year=event.year, date_label=event.date_label, person=event.person,
            theme=event.theme, title=event.title, description=event.description,
            source_citation=event.source_citation, source_url=event.source_url,
            article_url=(article.get_url() or "") if article else "", article_title=article.title if article else "",
        ))
    return ChronologyPayload(title=page.title, events=result)
