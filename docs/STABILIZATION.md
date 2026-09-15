# 0.3.2: Debian build and framework stabilization

## Fixed baseline

| Layer | Input |
|---|---|
| Python builder | `dhi.io/python:3.14.7-debian13-dev` |
| Python runtime | `dhi.io/python:3.14.7-debian13` |
| Django | `6.0.8` |
| Wagtail | `7.4.3` |
| Application tag | `the_liberty_articulator:0.3.2-debian` |

The separate Debian audit / Alpine build arrangement is removed. There are three
Docker stages: Node assets, Debian application build, and Debian runtime. The
source audit runs inside the Debian build stage. Node compiles assets and runs
frontend unit tests; it is not a production server. The existing React code,
content, styles, images, page models, and migration files are preserved.

Other container image source references and the network topology are unchanged.
The PostgreSQL Alpine image does not transfer native Python artifacts to the
application; it remains a separate service. No existing PostgreSQL volume is
converted or reused automatically.

## Why the installation profile changed

The former production requirements installed 28 requested packages plus supporting
libraries, including editor extensions that were not activated. An inactive
extension can still prevent pip from resolving the installation.

`requirements/production.in` now includes `core.in`. The core has the active
Django/Wagtail/Gunicorn/PostgreSQL driver/Celery/Redis client/Pillow/WhiteNoise/
Pydantic/JWT/metrics dependencies. The two framework versions change as requested;
other active direct version constraints are retained.

The old extension and inactive-integration pins are preserved in:

- `requirements/optional/editor-extensions.in`
- `requirements/optional/integrations.in`

These files are **not included** by the default install. Some candidate libraries,
such as Django REST Framework and django-filter, may still be required transitively
by Wagtail, at versions allowed by Wagtail. Their old independent direct pins no
longer override that core resolution. Nothing is automatically added to
`INSTALLED_APPS`. See DEPENDENCIES.md for the activation boundary.

## What a successful target-host build must do

1. Pull intentional image tags and record immutable digests.
2. Check both Python image versions, Debian release, glibc identity, CPU architecture,
   SOABI, interpreter paths, and base prefix.
3. Compile the production lock from the new core inputs, without using old Python
   locks as constraints. Compile the development lock **constrained by production**.
4. Install the hashed production lock in a clean builder environment using wheels
   only, run `pip check`, and exercise active native modules. No compiler is silently
   added to work around a missing wheel. An absent compatible wheel is a blocking
   package qualification issue to review explicitly.
5. Stage all new lock outputs outside the project. Preserve a matching existing npm
   lock unless `--refresh-frontend` is explicitly requested. Record resolver tooling.
6. Back up previous locks and publish the new files only after all resolution gates
   succeed. Hash both inputs and outputs. A partial set or edited lock fails verification.
7. Build static assets, collectstatic, and run the native checks in the final non-root,
   shell-free image. PNG/JPEG/WebP encode/decode tests are included.
8. Run `ops/validate_app.py` against the actual final image ID. This uses no network,
   host volumes, or deployment secrets. Django checks, migration drift detection,
   and the Django tests run against ephemeral SQLite and temporary test media.

The image QA step does not test PostgreSQL, Redis, Celery execution, browser
interactions, Cloudflare, or the running monitoring services. Those remain release
gates in VALIDATION.md. A matching ABI alone is not a complete runtime test.

## Fresh isolated checkout (recommended)

Do not unzip over an existing project. The new example uses project name
`liberty_research_032`, so named database/media volumes are distinct.

```sh
unzip Liberty-Articulator-v0.3.2-Debian.zip
cd liberty-articulator-react-0.3.2
cp .env.example .env
# Review project name, Docker data root, hostnames and local port availability.
docker login dhi.io
./ops/prepare.sh
```

Preparation does not start the site. Registry and dependency resolution must
actually succeed. Stop at the first error; do not force-install conflicts or
replace versions with `latest`.

Test the application image without touching a persistent database:

```sh
MODE=dev python3 ops/validate_app.py --build
```

Then start the separate local project:

```sh
./ops/dev.sh
MODE=dev ./ops/dc exec web python manage.py createsuperuser
```

`dev.sh` deliberately repeats cached build/image checks before starting its
PostgreSQL/Redis services and running `safe_migrate`. The website/editor use
`http://localhost:8080/` and `/admin/`. Port 8080 must be free. Do not stop an
unrelated production service to free that port; choose a reviewed dev port/origin
override or a separate test host instead.

Founding content remains an explicit operation:

```sh
MODE=dev ./ops/dc exec web python manage.py import_founding_content
MODE=dev ./ops/dc exec web python manage.py import_founding_content --apply
# LOCAL TEST ONLY, after reviewing the draft import:
MODE=dev ./ops/dc exec web python manage.py import_founding_content --apply --publish
```

Do not run the fictional `--demo` seed for the real founding-content import.

## Existing 0.3.1 source checkout: guarded patch

Back up your code, database, media and reviewed locks first. The patch installer
only changes listed source files. It does not alter `.env`, secrets, existing
lockfiles, volumes, running containers, or published content. It rejects conflicts
with local edits rather than force-overwriting them.

```sh
unzip "$HOME/Downloads/Liberty-Articulator-v0.3.2-update.zip" -d /tmp
UPDATE=/tmp/liberty-articulator-stabilization-0.3.2-update/apply_update.py
python3 "$UPDATE" --project "$PWD"
# Review the dry run before writing:
python3 "$UPDATE" --project "$PWD" --apply
```

The source patch alone does not make the old database compatible. Prefer a new
checkout and fresh volumes for this version change. Do not reuse a database that
has been migrated under Wagtail 8 or Django 6.1 without a reviewed restore/data
migration plan. On an isolated test checkout, set a new Compose project name and
`APP_IMAGE=the_liberty_articulator:0.3.2-debian`. Do not rotate old credentials or
delete old volumes as part of this change.

For the patch path, refresh locks deliberately:

```sh
# Preserves all non-Python locked image digests and removes the obsolete audit key.
python3 ops/lock_images.py --refresh-python
python3 ops/check_image_contracts.py --python-only
# Re-resolve Python; preserve a matching existing npm lock by default.
python3 ops/lock_dependencies.py
python3 ops/render_config.py
MODE=dev ./ops/dc config --quiet
MODE=dev python3 ops/validate_app.py --build
```

The selective image refresh recognizes format-2 locks or the recorded original
0.3.1 source fingerprint. Customized legacy image inputs require manual review;
the helper refuses to guess their old tag-to-digest mappings. The default
`python3 ops/lock_images.py` intentionally resolves all image sources and is not a
substitute for selective refresh when you intend to preserve unrelated digests.

The `ops/dc` wrapper uses `.env` and `images.lock.env` as authoritative values,
including when the shell contains different image variables. Use the wrapper
consistently so a shell override does not bypass the reviewed image inputs.

## Database downgrade boundary

`safe_migrate` is the migration service entry point. It checks exact framework
versions, reads existing migration history, rejects unknown records (including
newer Wagtail migrations), handles known squashed-migration records, checks history
consistency and model/migration drift, then runs normal **forward** migrations.
It does not reverse migrations or offer a fake mode.

A known migration history is not proof that a database previously used by a newer
framework is safe: schemas, data semantics and application customizations can
still differ. Use a fresh database for initial qualification, then a compatible
pre-upgrade backup or a reviewed export/import into another fresh database.
Never delete `django_migrations` rows, use `--fake`, or run `down -v` to evade a guard.

Read-only inspection, once the new image has passed its isolated tests:

```sh
MODE=dev ./ops/dc run --rm --no-deps web python manage.py check_database_compatibility
```

The command requires a reachable project database, but does not start dependencies
with `--no-deps` and does not modify schema or content.

## Source rollback

The patch prints its backup directory. Its `--rollback PATH` mode is a dry run
unless `--apply` is also supplied. It refuses to overwrite later edits. This
restores code only. It does not revert manual `.env` edits, lock re-resolution,
new migrations, or changed database contents. Previous locks are separately backed
up under `runtime/lock-backups/`. Never switch a used database between framework
versions merely by restoring an old application image.

## Remaining qualification

The authoring environment did not have Docker or package-registry connectivity.
No registry pulls, dependency locks, complete application builds, actual Django
runs, image security audits or database restoration were performed there. The
verification report distinguishes source/helper tests from those pending gates.
The build intentionally fails rather than silently modifying an unavailable or
incompatible package version. Keep staging domains until all release checks pass.
