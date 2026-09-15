> **0.3.2 update:** Use [STABILIZATION.md](STABILIZATION.md) for the active Debian/core baseline and framework rollback safety. Earlier version-specific commands below are historical context where they differ.

# Architecture and content boundaries

## Decision record

Chosen primary path: a content-led Wagtail website with isolated React tools. Scope: a new single-host Compose project. This is one failure domain, not high availability or cross-host orchestration. Management software such as Arcane remains outside the application stack. The deployment bundle does not contact or reconfigure an existing management instance.

Public rendering, URL hierarchy, page revisions, scheduling, notes, bibliographies, and canonical/citation metadata stay in Django/Wagtail. React owns reader selection/filter state. No Next.js runtime, backend-for-frontend, GraphQL service, or second editorial database is introduced.

The file-provider choice for Traefik is deliberate: two domain routes and an archive subroute do not justify Docker discovery access. Service discovery uses Compose DNS. The Docker API proxy is used only by monitoring components. Its remaining sensitive read surface is documented separately.

## Content model

`HomePage` contains publication pages and SectionIndexPage containers; the imported article and issue paths use /article/ and /issue/. It also owns published header/footer layouts. ResearchArchivePage, ChronologyPage and StandardPage retain their roles. `Subject` and `Series` are reusable taxonomies. `ArticleAuthor` and `ArticleSource` are ordered page-owned children. An article's bibliography is a source snapshot belonging to its revision, not an unrestricted shared source snippet whose edits silently rewrite already published articles.

Article sources contain a stable key, primary/secondary/unclassified classification, title, author text, optional year, bibliographic entry, explanatory annotation, and optional external URL. A reference attaches to a structured paragraph or quotation and points to the key. Its page/folio/section locator and note are displayed as numbered footnotes. References are numbered in rendered body order. Their anchors derive from persisted StreamField block identifiers and reference position. Reordering a reference list can change individual note anchors; bibliographic source keys should remain stable.

Body blocks: paragraph rich text, h2/h3/h4 headings, quotation, and figure. Ordinary prose is rendered by Wagtail, not parsed into a second client-side document tree. Figures support explicit alternative text, caption, and credit. Inline-word footnote editing, automatic citation-style formatting, citation import, DOI registration, full ORCID checksum validation, contributor identity verification, and rights clearance are not implemented.

`ChronologyEvent` is an ordered revision-aware child of a chronology page. Its signed year is for ordering/filtering; the date label carries uncertainty and precision such as "circa". BCE/CE has no year zero. The numeric supported interval is -10000 to -1 and 1 to 10000. The editor remains responsible for evidential accuracy.

## Contracts and runtime behavior

Pydantic models are the single authoring location for public widget shapes. `ops/export_contracts.py` emits schema and TypeScript deterministically. The deliberately small TypeScript emitter supports the schema constructs used by these models and raises on unsupported shapes rather than producing `any`. Serialized defaults are required on the wire. AJV compiles the three schemas during the asset build; browser validation then uses standalone code.

Sources and chronology use `json_script` embedded data with the current page instance. No fetch is needed to browse an article's sources or its chronology. Archive requests use a same-origin, GET-only endpoint with input validation, bounded page size, stable sort tie-breakers, and ORM queries. Responses contain public/live pages beneath the selected Wagtail Site root. Draft-only taxonomy/author facets are not returned. Private content is excluded even for a logged-in reader: this is a public archive, not an editorial search API.

Archive queries search title and abstract, filter by metadata, and match overlapping historical intervals. Page size is fixed at 12. This is an initial relational search implementation, not relevance-ranked body search or an external search engine. Large corpus performance needs realistic PostgreSQL query plans, pagination tests, and indexing decisions. Facet names are all public values in the current site, not dynamically filtered counts for each prospective facet combination.

React mounts into empty dedicated containers. It never calls `createRoot` on the article body. Fallbacks are hidden only after a successful component commit, restored after a render error, and retained when initialization/schema validation fails. Print CSS shows full server content. Links use native anchors; filter controls use native labels/buttons. Reader errors keep previous archive results rather than blanking the entire page.

Archive URLs use history pushState after a successful search and respond to browser back/forward. Chronology URL filters and the selected event are updated in place for sharing. Source selection stays local to the article panel.

## Publication and cache policy

Django is authoritative on every HTML/API request. Non-static responses use private/no-store, including draft previews. This intentionally avoids distributed page-cache invalidation in the first release. Do not override that policy with Cloudflare Cache Everything or an API/editor cache rule. Hashed frontend assets are served separately.

One Celery Beat enqueues scheduled publication/expiry checks every minute. A worker executes Wagtail's scheduled publishing command under a Redis lock and writes a success heartbeat. Beat health depends on this complete scheduling path, not merely a PID file. A failed beat, worker, broker, or publishing command can therefore trigger the same stale-heartbeat symptom; inspect all four when troubleshooting.

Metadata taxonomy names can change independently of an article revision. The revision snapshot guarantee applies to article source and author records, not every external link, third-party resource, shared taxonomy, or referenced image asset. Public image renditions are not a confidential-media vault.

## Deployment compatibility

The active baseline is Python 3.14.7, Django 6.0.8, and Wagtail 7.4.3, using
Debian 13 for the Python dependency builder and runtime. Wagtail 7.4 supports
Django 6.0 and Python 3.14. Core dependencies are installed by default; the former
optional extension/integration pins are retained only as qualification candidates.
Exact dependencies, wheels and runtime library compatibility still require a
successful connected build. See DEPENDENCIES.md, STABILIZATION.md and DHI_UPGRADE.md.
A supported framework pairing is not evidence that every candidate extension works.

Generate and commit dependency/image locks on a connected build host. Resolve new image digests deliberately, review release notes and vulnerabilities, run the gates, and deploy an immutable application image tag/digest. Keep database/schema changes backward-compatible across a rollback window. A frontend-generated type file is not a substitute for a content migration.

## Imported layouts and evidence

SourceSectionBlock renders only registry-owned templates with revision-owned escaped text/link values. ImportedCitation retains original footnote anchors and points to page-owned ArticleSource rows. The source ledger, notes and explorer share those evidence records. Curated home/portfolio cards remain dated source-copy snapshots; only the research archive automatically queries current public/live articles. ContentImportRecord tracks checksum/page/revision provenance and guards repeat imports.

The optional identity overlay and Alertmanager are new in 0.3.0. Identity is not integrated into login automatically; Alertmanager has no external notification destination until configured.
