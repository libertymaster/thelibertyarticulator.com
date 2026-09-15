# Founding-site content transfer

## Authority and provenance

Source: `Pasted text(20260913-193902).txt`, supplied by the publication owner. Source SHA-256: `7c53125e6fbc3637fa8e4b189fe55f17f379ad2abb9172458c77016b3e45d27b`.

Thirteen extracted original files are retained under `source-import/original/`; `source-import/manifest.json` records source ranges and per-file hashes. The original is a source reference, not a runnable Next.js dependency inside this stack. Editorial claims, cited-source descriptions, review labels, policy dates, and article wording are transferred from that source, not externally reverified or replaced by new scholarship.

## Page map

| Supplied source | New implementation |
|---|---|
| `app/page.tsx` | HomePage reference_layout; masthead, 50/30/20 allocation, commitments, featured editorial, portfolio, Bloch Lens, source desk, workflow, founding question |
| `app/about/page.tsx` | StandardPage at `/about/`; mission, pillars, governance, analytical-method explanation, reader-forum prospectus |
| `app/archive/page.tsx` | ResearchArchivePage at `/archive/`; original heading/status caveats plus the existing live research archive and React tool |
| `app/article/the-archive-is-not-the-village/page.tsx` | ArticlePage beneath `/article/`; complete prose, abstract, sections, callout, source ledger, notes, citation, review/version notices |
| `app/issue/founding/page.tsx` | StandardPage beneath `/issue/`; all ten source portfolio records, five/three/two discipline allocation |
| `app/sources/page.tsx` | StandardPage at `/sources/`; four principles, six ledger dimensions, dossier and source distinctions |
| `app/standards/page.tsx` | StandardPage at `/standards/`; draft policy status, percentage table, review model, ten gates, seven-question rubric, verification, corrections, ethics, references |
| `app/submit/page.tsx` | StandardPage at `/submit/`; six article types, seven submission-packet requirements, explicit closed-submissions notices |
| `components/site-header.tsx`, `site-footer.tsx` | HomePage-owned header/footer layout fields, with a navigation entry for the chronology |
| `lib/journal-data.ts` | Exact ten publication records, ten workflow gates, seven rubric questions, eight standards sources in `content/founding/journal_data.json` |
| `app/globals.css` | `static/css/publication.css`; build-tool-only imports/theme directives removed, editorial styles retained |
| `app/layout.tsx` | Django base template, canonical metadata, Wagtail-derived article metadata; original branding assets supplied and connected in 0.3.1 |

## Editable structure

The conversion uses 50 allowlisted section layouts and 901 editable text/link fragments. `content/founding/pages.json` supplies initial values; `layout_registry.json` specifies required keys and template paths. A Wagtail StreamField saves values in revisions. Editors can change wording and URLs without inserting arbitrary markup or replacing structural keys.

These are intentionally curated editorial layouts, not a freeform page builder. Moving or redesigning sections requires reviewing templates/CSS and the registry together. Styling for allocation percentages and numbered lists remains structural rather than relying on pasted rich-text spacing.

The HomePage and founding portfolio retain dated source-card copy. They are **not** automatically regenerated when an ArticlePage is edited. The live archive is dynamic and permission-filtered. This prevents a source transfer from silently changing the original commissioning presentation, but it means editors must review those curated cards when revising the portfolio.

## Scholarly status and evidence

The editorial is dated 29 August 2026, version 1.0, and marked public draft / editorially reviewed / not externally reviewed according to the source. Nine other records remain planned commissioning briefs with no publication date and no invented full text. Wagtail `live=True` only means a page is web-visible; it does not change the semantic review/publication status.

Four original references and four source-ledger rows are modeled as ordered, page-owned source records. Four ImportedCitation rows preserve original note/passage anchors. The server ledger, notes and React explorer read the same source records and the current page revision. Bibliographic text, source URL, display title, edition, use, and verification caveat can be edited. The complete citation is linked for accessible interaction; original inline typography within bibliography text is normalized to plain text.

No contextual source classification, page/folio locator, or chronology event was inferred. Sources begin unclassified where the input did not assign a primary/secondary role. The original printed consultation statements are source copy, not evidence of a new consultation during this build.

## Branding assets and component substitutions

The text input referenced `og.png` and `favicon.svg`; the owner supplied both in the subsequent upload. Version 0.3.1 includes the original bytes in `static/branding/`, with file provenance and checksums in `content/branding/assets.json`. The founding editorial figure and social cards use this artwork automatically when HomePage artwork fields are blank. Existing valid `artwork_url` and `artwork_alt` overrides remain effective. The SVG is used as the favicon. No Wagtail revisions or imported content hashes are changed. See BRANDING.md for asset URLs, overrides, and validation.

Original PublicationCard, ArchiveBrowser and CitationCopy component implementations were not supplied. Portfolio cards were reconstructed from the supplied data/styles. The archive uses the existing React research tool. Citation copying uses small ordinary JavaScript. Decorative Lucide icons were replaced with lightweight text symbols; the original icon package and exact icon artwork are not claimed transferred. No Tailwind, shadcn or Next runtime is needed.

## Safe import and repeat runs

1. Bootstrap only the fresh new project.
2. Run `import_founding_content` without flags to see the plan.
3. Use `--apply` to create draft revisions.
4. Preview, then deliberately publish pages and their ancestors. For a local acceptance test, `--apply --publish` explicitly publishes the imported records.

Nineteen import records bind source checksums to pages and revisions. Existing content with matching import records is preserved. A checksum change, unknown existing page, changed bootstrap text, or a moved/replaced imported container stops the import. The importer does not overwrite later editor changes. When publishing a prior imported draft, it publishes only if that imported revision is still the latest.

The script is not a general migration from a running database. Do not use raw-volume reuse, `--fake`, or content deletion to get around its guards. Build a separate, reviewed migration for your actual production content, media, permissions, and URLs.

## Not implied by publication of this copy

The forum remains prospective; submissions remain closed. Ten editorial gates, review promises, preserved-version policy, rights review, governance, and funding disclosures remain source policy text, not evidence that those operational systems are implemented or ratified. Wagtail revisions exist, but this release does not add a public immutable historical-version comparison service. Review actual workflow/group permissions before assigning users.
