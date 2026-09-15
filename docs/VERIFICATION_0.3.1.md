# Verification report: 0.3.1 branding update

**Date:** 13 September 2026
**Scope:** Integration of the two uploaded assets into the supplied 0.3.0 source bundle.
**Status:** Source, asset-integrity, and updater checks passed. This is not evidence of a deployed or fully tested Docker/Django/Wagtail application.

## Executed for this update

| Check | Result |
|---|---|
| Existing and new static suite | 68 tests passed, including 28 branding-related cases |
| Guarded updater functional checks on disposable copies | 10 checks passed: dry run, apply, preservation of local state, repeated application, rollback dry run, later-edit rejection, complete rollback, conflict refusal, symlink refusal, corrupt-payload refusal |
| PNG verification | Pillow verified the supplied PNG; actual dimensions 1200 x 630, RGB |
| SVG inspection | XML parses; 64 x 64 viewBox; only svg/rect/circle/path elements; no scripts, event attributes, external references, or DTD/entity declarations |
| Original asset preservation | Packaged PNG and SVG SHA-256 hashes match the uploaded files exactly |
| Python, JSON, YAML, shell syntax | Passed; counts recorded in evidence/branding-source-checks.json |
| Whitespace/line-ending gate | Passed |
| API contract generation | Existing generated schemas and TypeScript definitions matched |
| Scope comparison against pristine 0.3.0 | Dockerfile, upstream image inputs, requirements, entire frontend, contracts, database migrations, founding content data, source-import reference files, and monitoring configurations unchanged |
| Archive and file integrity | ZIP CRC checks passed; per-file SHA256SUMS verified |

Asset hashes:

```text
4261342b1994cec303f64ddfb9f61180b8e1bad8efc46d1e71e301b3d35447ce  static/branding/og.png
48ffbd4dd1d72cc54effbcf4ff97e4d98ab31791ffd08bef1c522e575cb3311f  static/branding/favicon.svg
```

The updater tests used only disposable local project copies with synthetic state canaries. They did not access a deployment host. Evidence files are under `docs/evidence/branding-*`.

## Implemented, not executed here

Eight new Django test methods cover metadata rendering, custom-image dimensions/escaping, the figure URL, GET/HEAD redirects, POST rejection, route precedence, preview-context resolution, and public-origin metadata. Existing founding-import tests also assert that the assets replace the old missing-artwork notice. These are supplied test implementations, not passed application-runtime evidence.

The pure resolver tests use an injected static-URL function. They verify compatibility with ordinary URLs, CDN URLs, and hashed URLs; they do not claim a live manifest-storage or WhiteNoise integration test. The actual bundle continues to use CompressedStaticFilesStorage without global filename hashing.

No Docker executable was available. Django/Wagtail and WhiteNoise were not installed in the authoring environment. A minimal dependency probe for the requested Django==6.1.1 and whitenoise==6.12.0 did not resolve an installable distribution in this environment; that result does not establish upstream availability or incompatibility. No replacement dependency versions were installed or written into the project. A Playwright Chromium executable was also unavailable, so no new live-browser/layout checks are claimed.

Consequently, this update did not execute:

- Docker builds, image qualification or merged Compose semantic checks.
- Actual collectstatic/WhiteNoise serving, Django template rendering, Wagtail preview/publication, or the Django test suite.
- Frontend build/tests, live browser tests, external social crawlers, or Cloudflare access/cache behavior.
- Security audits, load tests, backup/restore, or any production deployment.

The requested dependency profile and all broader 0.3.0 runtime acceptance gates remain outstanding. The previous report is retained verbatim as VERIFICATION_0.3.0.md; its screenshots and evidence describe that earlier static source snapshot, not a running 0.3.1 site.

## Deployment boundary

No production database, container, DNS record, Cloudflare setting, repository, secret, or user-edited file was accessed or changed. The full bundle is for a separate checkout; the guarded patch may update the matching 0.3.0 project without changing its data model. Read BRANDING.md before applying it. Keeping existing COMPOSE_PROJECT_NAME and secrets is essential when updating that project.
