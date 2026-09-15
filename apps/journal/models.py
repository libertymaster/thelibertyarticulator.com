from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from .blocks import ArticleBodyBlock
from .editor_forms import ArticlePageForm
from .source_layout import SourceLayoutStreamBlock, safe_editorial_url

KEY_VALIDATOR = RegexValidator(r"^[a-z0-9][a-z0-9-]{0,59}$", "Use lowercase letters, digits, and hyphens; begin with a letter or digit.")
ORCID_VALIDATOR = RegexValidator(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$", "Enter an ORCID in its hyphenated 16-character form.")
SOURCE_KINDS = [("primary", "Primary"), ("secondary", "Secondary"), ("unclassified", "Not classified")]
RECORD_STATUSES = [("public_draft", "Public draft"), ("planned", "Planned"), ("under_review", "Under review"), ("version_of_record", "Version of record")]
THEMES = [("life", "Life"), ("writing", "Writings"), ("politics", "Political activity"), ("context", "Historical context")]

def validate_year(value):
    if value == 0 or value < -10000 or value > 10000:
        raise ValidationError("Use -10000 through -1 for BCE, or 1 through 10000 for CE. There is no year zero.")

@register_snippet
class Subject(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    panels = [FieldPanel("name"), FieldPanel("slug")]
    class Meta:
        abstract = False
        ordering = ["name"]
    def __str__(self):
        return self.name

@register_snippet
class Series(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    panels = [FieldPanel("name"), FieldPanel("slug"), FieldPanel("description")]
    class Meta:
        abstract = False
        ordering = ["name"]
        verbose_name_plural = "series"
    def __str__(self):
        return self.name

class HomePage(Page):
    class Meta:
        abstract = False
    introduction = RichTextField(blank=True, features=["bold", "italic", "link"])
    reference_layout = StreamField(SourceLayoutStreamBlock(), blank=True)
    header_layout = StreamField(SourceLayoutStreamBlock(), blank=True)
    footer_layout = StreamField(SourceLayoutStreamBlock(), blank=True)
    artwork_url = models.CharField(max_length=2000, blank=True, validators=[safe_editorial_url])
    artwork_alt = models.CharField(max_length=300, blank=True)
    content_panels = Page.content_panels + [FieldPanel("introduction"), FieldPanel("reference_layout")]
    settings_panels = Page.settings_panels + [FieldPanel("header_layout"), FieldPanel("footer_layout"), FieldPanel("artwork_url"), FieldPanel("artwork_alt")]
    subpage_types = ["journal.ArticlePage", "journal.ResearchArchivePage", "journal.ChronologyPage", "journal.StandardPage", "journal.SectionIndexPage"]
    max_count = 1
    def get_context(self, request, *args, **kwargs):
        from .services import public_articles
        context = super().get_context(request, *args, **kwargs)
        context["latest_articles"] = public_articles(request).exclude(record_status="planned").order_by("-publication_date", "-id")[:6]
        context["branding"] = self
        return context

class StandardPage(Page):
    class Meta:
        abstract = False
    body = RichTextField(blank=True, features=["h2", "h3", "h4", "bold", "italic", "ol", "ul", "link"])
    reference_layout = StreamField(SourceLayoutStreamBlock(), blank=True)
    content_panels = Page.content_panels + [FieldPanel("body"), FieldPanel("reference_layout")]
    parent_page_types = ["journal.HomePage", "journal.SectionIndexPage"]
    subpage_types = []

class ArticlePage(Page):
    base_form_class = ArticlePageForm
    abstract = models.TextField(max_length=3000)
    publication_date = models.DateField(null=True, blank=True)
    dek = models.TextField(blank=True)
    discipline = models.CharField(max_length=20, blank=True, choices=[("History", "History"), ("Philosophy", "Philosophy"), ("Politics", "Politics")])
    article_type = models.CharField(max_length=100, default="Article")
    record_status = models.CharField(max_length=30, choices=RECORD_STATUSES, default="public_draft")
    review_status = models.CharField(max_length=200, default="Review status not declared")
    version_label = models.CharField(max_length=50, blank=True)
    sources_summary = models.CharField(max_length=500, blank=True)
    method = models.CharField(max_length=200, blank=True)
    display_date = models.CharField(max_length=100, blank=True)
    read_time = models.CharField(max_length=80, blank=True)
    reference_layout = StreamField(SourceLayoutStreamBlock(), blank=True)
    historical_start = models.IntegerField(null=True, blank=True, validators=[validate_year])
    historical_end = models.IntegerField(null=True, blank=True, validators=[validate_year])
    series = models.ForeignKey(Series, null=True, blank=True, on_delete=models.SET_NULL, related_name="articles")
    subjects = ParentalManyToManyField(Subject, blank=True, related_name="articles")
    license_label = models.CharField(max_length=160, default="All rights reserved")
    body = StreamField(ArticleBodyBlock(), blank=True)
    is_demonstration = models.BooleanField(default=False, help_text="Show a prominent non-scholarly demonstration label.")
    parent_page_types = ["journal.HomePage", "journal.SectionIndexPage"]
    subpage_types = []
    content_panels = Page.content_panels + [
        FieldPanel("abstract"), FieldPanel("publication_date"), FieldPanel("body"),
        MultiFieldPanel([FieldPanel(n) for n in ["dek", "discipline", "article_type", "record_status", "review_status", "version_label", "sources_summary", "method", "display_date", "read_time"]], heading="Public scholarly record"),
        FieldPanel("reference_layout"),
        InlinePanel("imported_citations", label="Imported citation anchors"),
        MultiFieldPanel([FieldPanel("historical_start"), FieldPanel("historical_end")], heading="Historical period covered"),
        FieldPanel("subjects"), FieldPanel("series"), FieldPanel("license_label"), FieldPanel("is_demonstration"),
        InlinePanel("authors", label="Authors"),
        InlinePanel("sources", label="Sources", help_text="Article-owned source snapshots are included in Wagtail revisions."),
    ]
    search_fields = Page.search_fields + [index.SearchField("abstract"), index.SearchField("body")]
    class Meta:
        abstract = False
        indexes = [models.Index(fields=["publication_date"], name="article_pub_date_idx")]
    def clean(self):
        super().clean()
        errors = {}
        if (self.historical_start is None) != (self.historical_end is None):
            errors["historical_start"] = "Provide both ends of the historical period, or leave both blank."
        elif self.historical_start is not None and self.historical_start > self.historical_end:
            errors["historical_end"] = "The end must not precede the start."
        if self.record_status != "planned" and self.publication_date is None:
            errors["publication_date"] = "A dated public record needs a publication date. Planned briefs must leave it blank."
        if self.record_status == "planned" and self.publication_date is not None:
            errors["publication_date"] = "Do not assign a publication date to an uncompleted commissioning brief."
        if getattr(self, "_defer_reference_validation", False):
            if errors:
                raise ValidationError(errors)
            return
        keys = [source.key for source in self.sources.all()]
        if len(keys) != len(set(keys)):
            errors["body"] = "Every source key must be unique within the article."
        missing = set()
        for block in self.body:
            if block.block_type in {"paragraph", "quote"}:
                missing.update(ref["source_key"] for ref in block.value["references"] if ref["source_key"] not in keys)
        missing.update(c.source_key for c in self.imported_citations.all() if c.source_key not in keys)
        if missing:
            errors["body"] = "Undefined source keys: " + ", ".join(sorted(missing))
        if errors:
            raise ValidationError(errors)
    def get_context(self, request, *args, **kwargs):
        from .services import article_context
        context = super().get_context(request, *args, **kwargs)
        context.update(article_context(self, request))
        return context

class ArticleAuthor(Orderable):
    class Meta:
        abstract = False
        ordering = ["sort_order"]
    page = ParentalKey(ArticlePage, on_delete=models.CASCADE, related_name="authors")
    name = models.CharField(max_length=160)
    affiliation = models.CharField(max_length=250, blank=True)
    orcid = models.CharField(max_length=19, blank=True, validators=[ORCID_VALIDATOR])
    panels = [FieldPanel("name"), FieldPanel("affiliation"), FieldPanel("orcid")]

class ArticleSource(Orderable):
    page = ParentalKey(ArticlePage, on_delete=models.CASCADE, related_name="sources")
    key = models.CharField(max_length=60, validators=[KEY_VALIDATOR], help_text="Stable citation key, e.g. letter-01. Do not rename after publication without updating references.")
    kind = models.CharField(max_length=12, choices=SOURCE_KINDS)
    title = models.CharField(max_length=500)
    authors = models.CharField(max_length=500, blank=True)
    year = models.IntegerField(null=True, blank=True, validators=[validate_year])
    bibliography = models.TextField(help_text="Full human-reviewed bibliographic entry, including edition/publisher when relevant.")
    annotation = models.TextField(blank=True, help_text="Explain relevance and limitations; this is public-facing.")
    display_title = models.CharField(max_length=500, blank=True, help_text="Optional short title for the source ledger.")
    edition_label = models.CharField(max_length=500, blank=True)
    use_description = models.TextField(blank=True)
    verification_status = models.CharField(max_length=500, blank=True)
    url = models.URLField(max_length=1000, blank=True)
    panels = [FieldPanel(n) for n in ["key", "kind", "title", "authors", "year", "bibliography", "annotation", "display_title", "edition_label", "use_description", "verification_status", "url"]]
    class Meta:
        abstract = False
        ordering = ["sort_order"]
        constraints = [models.UniqueConstraint(fields=["page", "key"], name="article_source_key_unique")]

class ResearchArchivePage(Page):
    class Meta:
        abstract = False
    introduction = models.TextField(blank=True)
    reference_layout = StreamField(SourceLayoutStreamBlock(), blank=True)
    content_panels = Page.content_panels + [FieldPanel("introduction"), FieldPanel("reference_layout")]
    parent_page_types = ["journal.HomePage"]
    subpage_types = []
    max_count = 1
    def get_context(self, request, *args, **kwargs):
        from .services import archive_response
        context = super().get_context(request, *args, **kwargs)
        result, form = archive_response(request)
        context.update({"archive_payload": result.model_dump(mode="json"), "archive_form": form})
        return context

class ChronologyPage(Page):
    class Meta:
        abstract = False
    introduction = models.TextField(blank=True)
    is_demonstration = models.BooleanField(default=False)
    content_panels = Page.content_panels + [FieldPanel("introduction"), FieldPanel("is_demonstration"), InlinePanel("events", label="Chronology events")]
    parent_page_types = ["journal.HomePage"]
    subpage_types = []
    def clean(self):
        super().clean()
        keys = [e.key for e in self.events.all()]
        if len(keys) != len(set(keys)):
            raise ValidationError("Chronology event keys must be unique within the page.")
    def get_context(self, request, *args, **kwargs):
        from .services import chronology_payload
        context = super().get_context(request, *args, **kwargs)
        context["chronology_payload"] = chronology_payload(self).model_dump(mode="json")
        return context

class ChronologyEvent(Orderable):
    page = ParentalKey(ChronologyPage, on_delete=models.CASCADE, related_name="events")
    key = models.CharField(max_length=60, validators=[KEY_VALIDATOR])
    year = models.IntegerField(validators=[validate_year])
    date_label = models.CharField(max_length=100, help_text="Human-readable precision, e.g. circa 1790 or 3 March 1850.")
    person = models.CharField(max_length=160)
    theme = models.CharField(max_length=16, choices=THEMES)
    title = models.CharField(max_length=250)
    description = models.TextField()
    source_citation = models.TextField(help_text="Evidence supporting the event and its date.")
    source_url = models.URLField(max_length=1000, blank=True)
    related_article = models.ForeignKey(ArticlePage, blank=True, null=True, on_delete=models.SET_NULL, related_name="chronology_events")
    panels = [FieldPanel(n) for n in ["key", "year", "date_label", "person", "theme", "title", "description", "source_citation", "source_url", "related_article"]]
    class Meta:
        abstract = False
        ordering = ["sort_order"]
        constraints = [models.UniqueConstraint(fields=["page", "key"], name="chronology_event_key_unique")]


class SectionIndexPage(Page):
    """A URL container for /article/ and /issue/, not an invented source document."""
    parent_page_types = ["journal.HomePage"]
    subpage_types = ["journal.ArticlePage", "journal.StandardPage"]
    class Meta:
        abstract = False

class ImportedCitation(Orderable):
    page = ParentalKey(ArticlePage, on_delete=models.CASCADE, related_name="imported_citations")
    source_key = models.CharField(max_length=60, validators=[KEY_VALIDATOR])
    number = models.PositiveIntegerField()
    note_anchor = models.CharField(max_length=60, validators=[KEY_VALIDATOR])
    passage_anchor = models.CharField(max_length=60, validators=[KEY_VALIDATOR])
    locator = models.CharField(max_length=160, blank=True)
    note = models.TextField(blank=True)
    panels = [FieldPanel(n) for n in ["source_key", "number", "note_anchor", "passage_anchor", "locator", "note"]]
    class Meta:
        abstract = False
        ordering = ["sort_order"]
        constraints = [models.UniqueConstraint(fields=["page", "number"], name="imported_citation_number_unique")]

class ContentImportRecord(models.Model):
    """Import provenance; prevents a rerun from replacing edited content."""
    key = models.CharField(max_length=200, unique=True)
    checksum = models.CharField(max_length=64)
    page = models.ForeignKey(Page, on_delete=models.PROTECT)
    revision_id = models.PositiveBigIntegerField(null=True)
    imported_at = models.DateTimeField(auto_now_add=True)
