> **0.3.2 update:** Use [STABILIZATION.md](STABILIZATION.md) for the active Debian/core baseline and framework rollback safety. Earlier version-specific commands below are historical context where they differ.

# Acceptance and release gates

Run these against the actual resolved lockfiles and intended deployment. Keep the logs with the release record. A source-only pass does not satisfy runtime gates.

## 1. Source and contract checks

In a Python 3.14.7 environment matching the Debian 13 build image containing the reviewed development lock:

```sh
python ops/check_style.py
ruff check .
python ops/export_contracts.py --check
python -m pytest tests/static_tests -q
DJANGO_SETTINGS_MODULE=config.settings.testing python manage.py check
DJANGO_SETTINGS_MODULE=config.settings.testing python manage.py makemigrations --check --dry-run
DJANGO_SETTINGS_MODULE=config.settings.testing python manage.py test tests.django_tests
```

The style gate checks deterministic line endings/trailing whitespace; Ruff checks correctness errors. Generated types are not maintained by hand. The supplied initial and additive import migrations have not been executed in the authoring environment; migration-state equality and clean-database application are required on the connected test host. Do not paper over a migration mismatch with --fake.

Before any persistent database change, run the final-image tests with no network,
mounts or deployment secrets:

```sh
MODE=dev python3 ops/validate_app.py --build
```

This runs native checks, Django checks, migration-drift detection, and the Django
suite against ephemeral SQLite inside the non-root final application image.
Inspect `runtime/app-validation.json` and retain the console output. It does not
replace PostgreSQL/Redis/browser tests.

## 2. Frontend and browser checks

```sh
cd frontend
npm ci
npm run build
npm test
npm audit --audit-level=high
# With the development publication and explicit demo content running:
npx playwright install --with-deps chromium
npm run test:e2e
```

Build includes schema-validator generation and full TypeScript checking. Browser tests cover source filtering, archive URL persistence, chronology evidence, and JavaScript-disabled fallbacks. Add manual keyboard, focus, zoom, screen-reader, narrow-screen, printing, and editorial-preview checks. The package does not claim an accessibility audit.

The Python tests cover anonymous/live/restricted/draft filtering, unpublishing, citation validation, current-page preview data, date validation, public methods, and submitted source/reference form logic. These are supplied test cases, not claimed executed runtime evidence.

## 3. Exact Compose and owning-program configuration checks

```sh
MODE=dev ./ops/dc config --quiet
MODE=dev ./ops/check_configs.sh
# Also inspect the production merge without printing secret file contents:
MODE=prod ./ops/dc config --quiet
```

The wrapper uses the actual file order and both environment files. Inspect no production published ports, required network membership, secret mounts, and the intentionally privileged host sensors. Config-check commands use Prometheus's promtool, Loki's verifier, Alloy validation, and HAProxy's configuration test. Validate Traefik by starting it and checking its logs/health because this bundle does not invent a non-existent static-validator command for it.

## 4. Application, security, and operations checks

```sh
MODE=dev ./ops/dc up -d --wait web worker beat traefik
MODE=dev ./ops/dc exec -T web python ops/smoke.py
MODE=prod ./ops/dc run --rm web python manage.py check --deploy --fail-level WARNING
python3 ops/security_check.py
pip-audit -r requirements/production.lock
```

Security scans require a reviewed Git checkout and the build-time scanner image locks. Never add real secret files to Git to make a scanner see them. The scanner checks committed history and tracked working files, then scans a saved image archive without mounting Docker's control socket into the scanner. Audits may fail if a pinned version has a known vulnerability; investigate and update rather than suppress the entire gate.

Externally verify public HTTPS, expected Host routing, editor Access denial before authentication, correct JWT acceptance after Access login, subsequent Wagtail login/permissions, CSRF rejection, password-reset email, editor preview, uploads, and document access restrictions. Test an article publication, correction, scheduled publication, unpublication, and draft-only source change. The public site must never serve draft-only metadata; a cached browser tab naturally retains content already downloaded and is not a revocation boundary.

## 5. Monitoring, load, and recovery

Start monitoring, then verify all relevant Prometheus targets, pg_up, Redis exporter metrics, host/container metrics, Loki log arrival, Grafana data sources/dashboard, internal/external probes, and publishing heartbeat. A local-only tunnel probe is expected to be down. Simulate a safe test failure and verify both rule firing and separately configured notification delivery.

Perform a controlled load check only against a deployment you administer:

```sh
python3 ops/load_check.py http://127.0.0.1:8080/archive/ --requests 120 --concurrency 4
```

This small test is not a complete capacity benchmark. Define representative article/source/event counts, simultaneous users, query mixes, p95 latency/error objectives, saturation limits, and a soak period. Include PostgreSQL plans and restore-media behavior; do not infer capacity from a single homepage request.

Run an off-host encrypted backup and clean isolated restore, verify records/media/editor behavior, and record achieved RPO/RTO evidence. The included scripts alone do not establish recoverability.

## Release decision

Do not call the stack production-ready until the above gates pass or narrowly scoped exceptions are recorded with rationale, owner, expiry, and mitigation. There is no automatic production deployment from CI and no automatic modification of Cloudflare DNS, Access, router, or existing containers.

## Content-transfer and stabilization acceptance additions

Run ops/check_image_contracts.py against real resolved image digests. Verify the PostgreSQL UID/PGDATA, Python ABI, Redis PING-only health role, Grafana password file provider and native-module runtime import gate. Run pip check for the locked core profile. Optional candidates are not installed by default; qualify each explicitly before adding its installation requirements and editor hooks. Reject unknown database migration records and test safe_migrate before touching a restored database.

In an isolated local project, run import_founding_content dry-run, --apply, and an explicit --apply --publish after review. Confirm 19 tracked import objects, ten public records, nine with planned status and no publication date, the full editorial with four linked references, all imported informational pages, and a chronology without invented events. Rerun the import and confirm no duplicate pages and no overwrite of an edited revision. Test draft/private/unpublished exclusion from the archive and the page-preview source payload.

Check all three React tools with JavaScript enabled and disabled against the real Django application. Check mobile navigation, percentage tables, ordered sections, original anchor links, evidence filters, archive URL/history, chronology filters, print output, accessible names, keyboard focus and editor preview. Static preview screenshots in docs/previews are not substitutes for these checks.

Alertmanager receiver delivery must be configured and proved before alerting is operational. For optional Keycloak, test readiness, forwarded HTTPS issuer, administrator access/MFA, realm/client settings and a separate identity restore. Base tests do not assert SSO integration.
