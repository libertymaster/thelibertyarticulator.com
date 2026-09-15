"""Public widget contracts. Generated JSON Schema and TypeScript come from this file."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, json_schema_serialization_defaults_required=True)

class CitationLink(Contract):
    number: int
    anchor: str
    passage_anchor: str
    locator: str
    note: str

class SourceItem(Contract):
    key: str
    kind: Literal["primary", "secondary", "unclassified"]
    title: str
    authors: str
    year: int | None
    bibliography: str
    annotation: str
    url: str
    citations: list[CitationLink]

class SourcesPayload(Contract):
    schema_version: Literal["1"] = "1"
    article_title: str
    sources: list[SourceItem]

class Choice(Contract):
    value: str
    label: str

class ArchiveFilters(Contract):
    q: str = ""
    subject: str = ""
    author: str = ""
    series: str = ""
    source_kind: str = ""
    published_from: str = ""
    published_to: str = ""
    historical_from: str = ""
    historical_to: str = ""
    status: str = ""
    sort: Literal["newest", "oldest", "title"] = "newest"

class ArticleCard(Contract):
    id: int
    title: str
    url: str
    abstract: str
    publication_date: str
    authors: list[str]
    subjects: list[str]
    series: str
    historical_period: str
    is_demonstration: bool
    discipline: str = ""
    article_type: str = "Article"
    record_status: str = "public_draft"
    status_label: str = "Public draft"
    review_status: str = "Review status not declared"
    sources_summary: str = ""
    method: str = ""
    display_date: str = ""
    read_time: str = ""

class Facets(Contract):
    subjects: list[Choice]
    authors: list[Choice]
    series: list[Choice]

class ArchivePayload(Contract):
    schema_version: Literal["1"] = "1"
    endpoint: str = "/api/v1/archive/"
    filters: ArchiveFilters
    facets: Facets
    results: list[ArticleCard]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    pages: int = Field(ge=1)
    page_size: int = Field(ge=1, le=24)
    errors: list[str]

class TimelineEvent(Contract):
    key: str
    year: int
    date_label: str
    person: str
    theme: Literal["life", "writing", "politics", "context"]
    title: str
    description: str
    source_citation: str
    source_url: str
    article_url: str
    article_title: str

class ChronologyPayload(Contract):
    schema_version: Literal["1"] = "1"
    title: str
    events: list[TimelineEvent]
