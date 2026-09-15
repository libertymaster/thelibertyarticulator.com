> **0.3.2 update:** Use [STABILIZATION.md](STABILIZATION.md) for the active Debian/core baseline and framework rollback safety. Earlier version-specific commands below are historical context where they differ.

# Operations runbook

## Compose invocation and management

Use `ops/dc`, not an unqualified `docker compose up`. The wrapper supplies `.env`, `images.lock.env`, `compose.yaml`, and the chosen override. `MODE=prod` is the default; set `MODE=dev` for local-only testing. Supported extra files are a comma-separated `COMPOSE_EXTRA_FILES=compose.selinux.yaml,compose.ops.yaml`.

For Arcane or another external manager, first resolve dependency locks and build the application image on a capable build host. Configure the same project directory, environment interpolation, secrets, image lock values, and Compose file order. Keep the manager outside this application stack. Do not embed a second Docker manager or assume a GUI automatically executes the initialization/migration protocol.

## Startup and updates

Preparation changes local files only. Deployment requires explicit `ops/deploy.sh`. Use an unused project name and new volumes on first staging deployment. Preserve a previous application image tag and database backup before every upgrade. Change APP_IMAGE to a new immutable release tag before building an update; do not overwrite the only known-good tag.

For a running publication, first enforce an editorial maintenance window and back up. Stop Beat/worker during incompatible schema transitions; avoid requests using an incompatible old application while migrations run. The included deploy command is a simple single-host startup sequence, not a zero-downtime orchestrator. Use a reviewed staged rollout for subsequent database changes.

To resolve intentional version updates, edit the version inputs and run:

```sh
python3 ops/lock_images.py
python3 ops/lock_dependencies.py
# Review lock diffs, audit dependencies, run tests, and commit before deployment.
```

This re-resolves upstream references; never run it implicitly on every production start. Application image rollback is safe only while the database remains backward-compatible. Otherwise use a tested forward fix or an isolated restore/recovery plan. Never run `down -v` as routine troubleshooting.

## Private observability access

```sh
MODE=prod COMPOSE_EXTRA_FILES=compose.ops.yaml ./ops/dc up -d grafana prometheus
# From an administrative workstation:
ssh -L 3000:127.0.0.1:3000 -L 9090:127.0.0.1:9090 USER@SERVER
```

Use `http://localhost:3000` and `http://localhost:9090` through SSH. Grafana has an admin password file; transfer it through a local secure channel/password manager, not logs or chat. Grafana password initialization applies only to a fresh Grafana database; later file changes do not automatically rotate its existing account. No public Grafana subdomain is provisioned. Remove/recreate these services with the base/prod files alone when localhost maintenance access is no longer needed, then inspect actual bindings.

Prometheus includes jobs for Django, PostgreSQL, Redis, host/container metrics, proxies, and the observability stack. Blackbox probes the internal origin, public HTTPS health, and tunnel readiness. Public/tunnel probes will be down in local-only mode, and the default public probe may hit the existing public site until you configure staging domains. Treat that status correctly; it is not evidence that the new local site is live externally.

Grafana has a provisioned overview and Prometheus/Loki data sources. Alloy discovers only containers from the selected Compose project and persists log positions. Its labels use service/container/stack, not reader queries or other high-cardinality metadata.

## Retention and alerts

Prometheus retention: seven days or 2 GB, whichever limit is reached first. Loki retention: seven days with filesystem TSDB storage and compaction. Docker json-file logs rotate at 10 MB times three per container. These are initial local limits, not guarantees on total disk growth; database, media, image layers, backups, compaction headroom, and all persistent volumes also consume space.

Rules evaluate service/exporter availability, Blackbox failures, publishing heartbeat, HTTP error ratio, disk pressure, and Redis memory. **Alertmanager is configured internally, but its local-only receiver has no notification destination.** Add a reviewed receiver using mounted secrets, then test end-to-end delivery. Prometheus firing rules alone are not evidence of email or paging. Grafana does not automatically turn every Prometheus rule into a configured notification route.

## Common failures

- Image pull/tag unavailable: inspect the exact version input and upstream registry for your architecture. Do not fall back silently to latest. Locks are platform-sensitive; resolve on the intended build/target platform.
- Missing lock files: run preparation on a connected host, review/audit results, commit them. No guessed digests or fake lockfiles are supplied.
- PostgreSQL init failed: read PostgreSQL logs and inspect the fresh volume's initialization status. Do not delete existing data. TCP pg_isready verifies server availability, not successful application-role initialization. The subsequent migration/application check must succeed as well.
- Redis unhealthy: verify the PING-only health ACL and app/exporter credential coherence and file ownership/SELinux labels. Changing one of the generated Redis files requires coordinated rotation of the ACL and credential files.
- React tool absent: inspect the manifest/assets response and browser console. HTML content should still render. Build/type/schema errors must fail the image build rather than become a silent production omission.
- Source validation rejects a reference: compare exact stable keys in the article's Sources and reference blocks. Bibliography titles are not keys.
- Editor 403: verify the Access policy, JWT forwarding, audience and issuer. Do not disable JWT validation as a production workaround. Network access to the JWKS endpoint is required.
- Editor preview images missing: check media ownership, registered rendition path, file extension, and access boundary. A missing asset should not be fixed by exposing the entire media filesystem.
- Scheduler heartbeat stale: check Beat, worker ping, Redis connection/memory, task exceptions, and the publishing command. Do not start duplicate Beat schedulers.
- Monitoring permission failures on Fedora/rootless/Desktop: review the host-sensor exceptions. Do not give every service privileged mode.

## Completion criteria

Keep an operator log of exact image/dependency locks, content migration IDs, test/audit results, external smoke results, backup paths and off-host transfer, restore duration, observed load, and any accepted exceptions. A green container icon alone does not establish editorial correctness or recoverability.

## Founding content and optional identity

Use the explicit importer in CONTENT_MIGRATION.md; deployment does not automatically publish source content. Preserve import records and editor revisions. Review DHI_UPGRADE.md before changing images or adopting volumes. The optional Keycloak overlay has a separate database and recovery plan and does not change existing authentication.
