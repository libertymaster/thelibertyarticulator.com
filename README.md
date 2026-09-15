# The Liberty Articulator 0.3.2

**Debian Python stabilization: Django 6.0.8, Wagtail 7.4.3, Python 3.14.7.**
A Wagtail-rendered scholarly publication with three React research tools and a
private-origin Docker Compose stack. This revision modifies the supplied 0.3.1
source project; it does not deploy or change the existing publication.

Use a **new checkout, unique Compose project name, and fresh volumes** for the
initial framework rollback test. Do not point this image at a database already
migrated with Wagtail 8 / Django 6.1 without a reviewed recovery/migration plan.

Read [stabilization and migration safety](docs/STABILIZATION.md),
[dependency profiles](docs/DEPENDENCIES.md), and the
[actual verification report](docs/VERIFICATION.md) before first startup.

## What changed

- Matching `dhi.io/python:3.14.7-debian13-dev` and `dhi.io/python:3.14.7-debian13`
  replace the separate audit / Alpine build arrangement.
- The active core pins Django 6.0.8 and Wagtail 7.4.3. Optional editor and inactive
  integration pins are preserved separately, not installed by default.
- Lock resolution stages outputs, constrains development by production, preserves
  a matching npm lock, checks output hashes, and backs up previous lockfiles.
- Native imports and image codec checks run in the final non-root image.
- The startup scripts first run isolated final-image Django tests, then use a
  guarded forward-migration command that rejects unknown migration history.
- Non-Python container image sources, React implementation, content, style,
  branding, page models and existing migrations are preserved.

## Architecture

Internet -> Cloudflare Tunnel -> Traefik -> Gunicorn -> Django/Wagtail.

PostgreSQL, Redis, Celery worker and one Beat scheduler support the application.
PostgreSQL/Redis exporters, Prometheus, Grafana, Loki, Alloy, Node Exporter,
Blackbox Exporter and cAdvisor supply observability. Alertmanager is internally
connected but has no configured external notification destination. The optional
Keycloak overlay remains separate. Arcane stays outside this stack.

Production publishes no host ports. Development exposes the web application on
127.0.0.1:8080. Single-host Compose is one failure domain, not high availability.

## First local run

Prerequisites: Linux Docker Engine with Compose v2, Python 3 on the host, registry
and package-network access, DHI credentials, and an available local port 8080.
Review cAdvisor privileges, Docker data root and Fedora SELinux notes in SECURITY.md.

```sh
unzip Liberty-Articulator-v0.3.2-Debian.zip
cd liberty-articulator-react-0.3.2
cp .env.example .env
# Keep COMPOSE_PROJECT_NAME unique; review the rest of .env locally.
docker login dhi.io
./ops/prepare.sh
# Build and test without a persistent database, deployment secrets or a network:
MODE=dev python3 ops/validate_app.py --build
# Start only the new local project after the checks pass:
./ops/dev.sh
MODE=dev ./ops/dc exec web python manage.py createsuperuser
```

The explicit image check above is a useful checkpoint. `dev.sh` repeats the cached
build/image checks before initialization. The core dependency and image locks
must be resolved successfully on this connected host; no fabricated lockfiles or
registry digests are included. Do not bypass a failed check with --fake, forced
package installation, or volume deletion.

## Import the supplied founding site

```sh
# Plan only, no database writes:
MODE=dev ./ops/dc exec web python manage.py import_founding_content
# Create draft revisions:
MODE=dev ./ops/dc exec web python manage.py import_founding_content --apply
# LOCAL TEST ONLY, after editorial review:
MODE=dev ./ops/dc exec web python manage.py import_founding_content --apply --publish
```

The import preserves the supplied one public-draft editorial and nine planned
briefs. It does not overwrite later editorial changes or invent review records,
source classifications or chronology events. Do not use --demo for this import.

The public local site is `http://localhost:8080/`; editor is `/admin/`. Key paths:
`/archive/`, `/historys-heroes/`, `/standards/`, `/sources/`, `/about/`, `/submit/`,
`/issue/founding/`, and `/article/the-archive-is-not-the-village/`.

## React and editorial ownership

Wagtail renders the article, headings, footnotes, bibliography and ordinary pages.
React enhances the article source explorer, advanced research archive and
History's Heroes chronology. The source/chronology widgets use embedded data;
the archive uses the bounded GET endpoint `/api/v1/archive/`. There is no Next.js
service or parallel React article renderer.

The source ledger and explorer share revision-owned source records. Imported
layout fields remain editable text/links inside reviewed templates. Home and
founding-portfolio cards remain dated, curated snapshots; the archive queries live
public records. The uploaded PNG/SVG branding files remain unchanged. See
CONTENT_MIGRATION.md and BRANDING.md for content and asset boundaries.

## Existing checkout and rollback

Use the optional guarded source update only after reading STABILIZATION.md. It
preserves .env, secrets and old locks, but the changed Python inputs require
explicit new locks. `ops/lock_images.py --refresh-python` can preserve unrelated
image digests when the old input provenance is recognized. Source rollback is
not a database rollback. Preserve existing volumes and backups.

## Production and release status

Keep staging hostnames until all gates in VALIDATION.md pass. The tunnel remains
dashboard-managed and routes public/editor hosts to `http://traefik:8080`.
Production requires Cloudflare Access JWT gating plus Wagtail login. No R2
migration, automatic identity federation, manuscript intake, notification delivery,
or ratified editorial workflow is implied by this source update.

Static/helper checks were executed in the authoring environment. Docker builds,
package resolution, actual Django/Wagtail tests, PostgreSQL/Redis integration,
frontend builds/browser tests, security scans and restoration drills were not.
The supplied commands perform those checks on the target host. This is a source
release awaiting runtime qualification, not a production-readiness claim.
