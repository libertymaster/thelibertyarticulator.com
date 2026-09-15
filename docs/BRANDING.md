> **0.3.2 update:** Use [STABILIZATION.md](STABILIZATION.md) for the active Debian/core baseline and framework rollback safety. Earlier version-specific commands below are historical context where they differ.

# Branding assets: 0.3.1

## Included files and behavior

The owner supplied `og.png` and `favicon.svg` after the 0.3.0 content transfer. Their original bytes are retained under `static/branding/`. No cropping, recoloring, recompression, new artwork, or text substitution has been applied.

| File | Verified properties | Use |
|---|---|---|
| `static/branding/og.png` | PNG, RGB, 1200 x 630 pixels | Default Open Graph/Twitter card and founding editorial figure |
| `static/branding/favicon.svg` | SVG, 64 x 64 viewBox; shapes only | Browser favicon |

`content/branding/assets.json` records the upload provenance, byte sizes, SHA-256 checksums, and dimensions. The existing header wordmark and page layout are not replaced with the large social-card image. There is no added Node/Next.js service, React change, API contract change, schema migration, or new dependency.

## URL and template integration

Both files go through the existing staticfiles/WhiteNoise build. Django's `static()` function resolves the configured storage URL. This bundle deliberately retains `CompressedStaticFilesStorage`, which does not add filename hashes; Vite already hashes its own module assets. The helper also accepts hashed URLs if a manifest backend is configured later, without changing storage globally in this update. Social metadata uses an absolute public URL constructed with `PUBLIC_ORIGIN`. A configured absolute static CDN URL is retained.

The public `/og.png` and `/favicon.svg` paths are GET/HEAD-only compatibility redirects to the appropriate static assets. HTML references the direct static asset, not the redirect. The aliases are no-store so the alias itself is not retained across an update. The existing static-file cache lifetime is unchanged; replacing asset contents later may require cache refreshes. No new tunnel route is required.

Open Graph includes the page title, type, URL, site name, description, image, and alt text. The included image is advertised as image/png at 1200 x 630. Twitter-card metadata uses the same image. Planned commissioning briefs remain website records rather than being labeled published articles by this metadata. Article scholarly-status logic is otherwise unchanged.

The editorial figure retains the original caption and now displays the provided image. Width/height attributes describe the supplied image, and CSS preserves its aspect ratio on narrow screens. Its alt text describes the title and telescope/microscope motifs.

## Wagtail overrides and existing content

Leave HomePage's `artwork_url` and `artwork_alt` blank to use the shipped defaults automatically. No import or publication command is required just to activate these fallback assets. Existing valid HTTP(S) or root-relative artwork URLs still override the default, and their alt text is retained. An explicit `/og.png` override resolves to the bundled default.

For a custom image, fill `artwork_alt` with an accurate description. Custom images do not inherit the supplied PNG's dimensions or MIME type because those properties have not been measured. URL validation rejects scripts, data URLs, embedded credentials, protocol-relative URLs, and malformed locations; it does not check whether a remote image is accessible. The server does not fetch remote artwork.

The helper reads the existing template `branding` context, including the draft HomePage context during its own preview. This update does not broaden public access to drafts or change Cloudflare Access. Verify real preview behavior on the locked target build.

## New checkout

Use the normal README setup with the 0.3.1 archive. Its example project name is `liberty_research_031`, to avoid reusing the previous example's volumes accidentally. Its application image tag is `the_liberty_articulator:0.3.1-react`.

All upstream image inputs, Python requirements, npm manifest, contracts, database migrations, content-import data, and React code are unchanged from 0.3.0. In particular, the frontend package version is not bumped for this asset-only release, so dependency-lock input fingerprints are not invalidated by an unrelated version edit.

## Existing 0.3.0 checkout: guarded update

The separate `liberty-articulator-branding-0.3.1-update.zip` contains a source-only updater. It checks old/new hashes before writing anything, refuses conflicting edits and symlinks, and backs up affected files outside the project. It does not replace `.env`, secrets, runtime configuration, lockfiles, content, or databases. It does not run Docker or publish pages.

From the existing 0.3.0 project directory, adjust the Downloads path as needed:

```sh
unzip "$HOME/Downloads/liberty-articulator-branding-0.3.1-update.zip" -d /tmp
UPDATE=/tmp/liberty-articulator-branding-0.3.1-update/apply_update.py
python3 "$UPDATE" --project "$PWD"
# Review the dry-run result, then apply:
python3 "$UPDATE" --project "$PWD" --apply
```

A conflict stops the update before any source write. Compare the corresponding file in the update's `payload/` directory and merge deliberately. Do not disable the hash check to overwrite customized templates or Compose files.

After application, edit only `APP_IMAGE` in the existing `.env` to use a new release tag:

```text
APP_IMAGE=the_liberty_articulator:0.3.1-react
```

**Keep the existing COMPOSE_PROJECT_NAME unchanged for this update.** Do not replace `.env` with the new example, delete volumes, recreate databases, rotate credentials, rerun the content importer, or rerun dependency resolution solely for this patch. The earlier requirement for fresh volumes applies when creating this stack alongside a different production project, not to this source-only 0.3.0-to-0.3.1 change.

For an already prepared, running development project with valid locks and credentials:

```sh
MODE=dev ./ops/dc config --quiet
MODE=dev ./ops/dc build web
MODE=dev ./ops/dc up -d --no-deps web worker beat
MODE=dev ./ops/dc ps web worker beat
```

The existing Dockerfile runs `collectstatic` during image build. Rebuilding is required; copying files only to the host checkout does not replace the files in an already running application image. This change does not require new migrations. The ordinary build still runs the existing frontend build and existing dependency checks; this update does not fix pre-existing dependency/image qualification failures.

For an established staging/production deployment, use the same sequence with `MODE=prod`, your reviewed release procedure, and the correct PUBLIC_ORIGIN. Restarting web has the existing single-host interruption risk. Existing services outside web/worker/beat need no asset-related recreation.

## Verification on the deployment host

```sh
# After rebuilding, expect 302 -> 200 and correct final content types:
curl -IL http://localhost:8080/og.png
curl -IL http://localhost:8080/favicon.svg

# With the pinned development test dependencies installed:
DJANGO_SETTINGS_MODULE=config.settings.testing \
  python manage.py test tests.django_tests.test_branding
```

The production image need not include test dependencies; run the Django test command in the locked CI/development test environment. Open the founding editorial and inspect its figure, inspect page source for one og:image and matching Twitter image, check browser-tab appearance, and verify the image request in developer tools. Test local and public origins separately. Social platforms must be able to fetch the public image without login or a browser challenge; this package does not alter Cloudflare bot rules or claim that a platform's cached preview has refreshed.

## Rollback

The updater prints its backup directory. To inspect and perform a source rollback:

```sh
python3 "$UPDATE" --project "$PWD" --rollback /path/printed/by/updater
python3 "$UPDATE" --project "$PWD" --rollback /path/printed/by/updater --apply
```

Rollback refuses to overwrite files edited after the patch. It restores only files affected by that application. Your manual `.env` change is not rolled back automatically: select the previously retained application image tag and recreate web/worker/beat with the same Compose project. No database rollback is needed for this patch. Never remove volumes as part of branding rollback.

The full archive's SHA256SUMS describes the pristine release. Local edits outside the patch may already differ; the updater's manifest checks only its affected files and makes no claim that the rest of a customized checkout matches the pristine archive.

## Implementation references

- Django static-file integration: https://docs.djangoproject.com/en/6.1/howto/static-files/
- Django manifest storage: https://docs.djangoproject.com/en/6.1/ref/contrib/staticfiles/
- Open Graph metadata and image properties: https://ogp.me/

These references describe implementation behavior. The artwork and its provenance come from the uploaded files, not outside image sources.
