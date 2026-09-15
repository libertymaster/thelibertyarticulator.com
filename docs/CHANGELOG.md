# 0.3.2 - Debian/core stabilization (2026-09-14)

- Django 6.0.8 and Wagtail 7.4.3, with matching Python 3.14.7 Debian 13 builder/runtime.
- Core-first dependencies; original optional pins retained for separate qualification.
- Staged lock resolution, explicit selective Python image refresh, output integrity checks.
- Native/codec tests in the final image; isolated Django image-validation runner.
- Guarded forward migrations, with unknown migration-history and model-drift refusal.
- No content, React, branding, application model, or existing migration changes.
- See STABILIZATION.md and VERIFICATION.md; no runtime pass is inferred from source checks.

# 0.3.1 branding update

- Preserve the supplied PNG and SVG bytes and record SHA-256 provenance.
- Use storage-aware static URLs (compatible with a manifest backend) for the favicon, Open Graph/Twitter cards, and editorial figure.
- Resolve social image URLs against PUBLIC_ORIGIN, not an editor/internal request host.
- Keep valid Wagtail artwork overrides; use the included defaults for empty fields.
- Add GET/HEAD compatibility redirects for /og.png and /favicon.svg.
- Keep default image dimensions at 1200 x 630 and preserve responsive aspect ratio.
- No content-data edits, database migrations, upstream dependency/image changes, or React changes.
- Application release tag only: 0.3.1-react. Existing environment files are not modified automatically.

# 0.3.0 change summary

- Preserved the requested image references and 28 exact package pins.
- Added source-audit and matching-musl dependency stages for the requested Alpine runtime.
- Added native-image qualification and stale/partial lock protection.
- Switched PostgreSQL initialization/backups and application startup to shell-free execution paths; preserved native PostgreSQL 18 DHI data layout.
- Added PING-only Redis health ACL and native Grafana file-provider secret configuration.
- Added internal Alertmanager and optional isolated Keycloak services.
- Added original-source provenance, 50 safe section layouts, editable Wagtail copy, source importer and nine import integration tests.
- Retained all three React tools; enhanced record-status handling and shared imported citation/source data.
- Added static media-archive safeguards and static/source/browser-layout checks.
- Did not deploy, alter the prior bundle, import a live database, fabricate images or activate unverified editor extensions.
