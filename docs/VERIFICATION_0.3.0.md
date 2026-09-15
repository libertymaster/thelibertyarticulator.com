# Verification report

**Bundle:** The Liberty Articulator 0.3.0-react
**Date:** 13 September 2026
**Status:** source implementation with static/layout checks; not a verified production deployment.

## Checks actually executed in this environment

| Check | Result |
|---|---|
| `python -m pytest tests/static_tests -q` | 40 tests passed |
| `python ops/check_style.py` | Passed whitespace/line-ending gate |
| `python ops/export_contracts.py --check` | Generated JSON Schemas and TypeScript contracts matched |
| Python AST parsing | 66 Python files passed syntax parsing |
| JSON decoding | All project JSON files passed; exact checked file count is in evidence/syntax-checks.json |
| YAML parsing | 13 YAML/YML files passed parsing, not Docker Compose semantic validation |
| Shell syntax | 8 scripts passed the appropriate sh/bash syntax check |
| TypeScript syntax transpilation | 16 frontend TS/TSX modules passed; no dependency resolution or full semantic type check |
| Chromium static layout fixtures | 8 pages at two widths, 16 checks passed; one H1, no horizontal overflow, duplicate IDs or unresolved local anchors |
| Manual static screenshot inspection | Homepage, standards allocation, mobile article inspected; screenshots retained under previews/ |

The static suite includes source-file hash verification; page-layout registry/content consistency; ten portfolio records and their 5/3/2 balance; seven rubric questions, ten gates and eight standards references; exact preservation of 28 requested package pins; builder-family/health/identity-isolation assertions; common source/notes wiring; and safe media-archive rejection cases.

Source checks used the available host Python 3.13.5 rather than target Python 3.14.7. Pydantic was 2.13.4 locally, while the target input is 2.13.5. Node was 22.16.0, and global TypeScript was 5.8.3. These source checks do not substitute for repeating them in the actual locked target images.

## Tests and gates supplied but NOT executed here

- DHI registry authentication, exact image pulls, digest resolution, signature/attestation checks or native-image capability/ABI checks.
- Python/npm dependency resolution, installation, lock generation, `pip check`, or validation of every third-party Wagtail extension.
- Docker image builds, final-image native-module imports, merged Compose validation, container health or persistence tests.
- Django startup, Wagtail editor, clean migrations, `makemigrations --check`, ORM/content import, preview/publication or Django test suites.
- Complete React/Vite build, semantic TypeScript checking, component/unit tests or Playwright application E2E tests.
- Cloudflare routing/Access validation, real HTTPS/external probes, SMTP, real Grafana/Prometheus/Loki/Alloy ingestion or delivered alerts.
- Keycloak startup, administrator login, OIDC federation or identity backup/restore.
- Secret-history scans, vulnerability scans, Python/npm audits, penetration tests or load tests.
- Database/media backup, off-host transfer, restore drills or migration of existing production/R2 content.

The environment did not have Docker or the application dependencies. Direct package-host resolution was unavailable. No successful application build or runtime test has been invented, and no lockfile or digest was fabricated.

Nine new Django import tests are included, covering dry-run, draft-only import, explicit later publication, repeated-import/editor preservation, source anchors, private-article exclusion, planned-date validation, foreign-content protection and shared-reference updates. They are test implementations, not passing runtime evidence.

## Important unresolved risks and decisions

1. The complete requested package graph may have incompatible metadata or runtime APIs. Framework support alone does not qualify every addon. Pins are retained; stop and report conflicts rather than silently downgrading.
2. Added Alpine development image availability, native build dependencies and final runtime libraries must pass qualification. Debian native artifacts are not copied into Alpine.
3. DHI command paths, UID/GID 70:70 and PGDATA are checked by the target-host script but have not been inspected from pulled images here.
4. The additive migration is hand-authored and requires clean-database and state-equality tests. Do not bypass a mismatch with --fake.
5. Imported policy claims are preserved source text, not implemented or ratified operational procedures. Nine briefs remain planned; original artwork and real chronology events were not supplied.
6. The imported home/portfolio copy is curated, not automatically synchronized with later ArticlePage metadata. The archive is dynamic.
7. Alertmanager lacks an external receiver, and Keycloak is opt-in infrastructure without application SSO integration.
8. This is a new database/volume project, not an in-place upgrade. Existing volume ownership/data-layout assumptions must not be reused blindly.

## Acceptance on the actual deployment host

Follow VALIDATION.md, DHI_UPGRADE.md, CONTENT_MIGRATION.md and the README. Keep actual image/dependency locks, input fingerprints, test outputs, content checks, external probes and restoration evidence with the release record. Existing production containers, DNS, secrets, database and repository were not accessed or changed.
