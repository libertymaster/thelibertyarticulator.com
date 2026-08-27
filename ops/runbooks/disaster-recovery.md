# Disaster recovery runbook

This baseline targets a 24-hour RPO and an initial four-hour RTO. A real objective exists only if timed restore drills meet it. Record every quarterly drill and update these estimates.

## Declare and stabilize

1. Open an incident record, name an incident commander, operations lead, communications lead, and scribe.
2. Record the first observed failure, affected host/services, last known-good time, latest successful backup metric, and recent deployments.
3. Prevent further damage. If database integrity is uncertain, stop application writers (`web_a`, `web_b`, Celery worker, Celery beat, and FusionAuth) while keeping evidence and observability available.
4. Preserve host and container logs, relevant Grafana panels, image digests, Compose configuration, and storage/cloud audit events. Do not rotate credentials until evidence needed for containment is captured, unless active compromise makes rotation urgent.
5. Choose the narrowest recovery path below. Do not restore a database to fix an application-only outage.

## Application host loss (`liberty01server`)

1. Confirm PostgreSQL, Redis, FusionAuth, R2, and the observability host are healthy.
2. Provision a replacement host with the same private DNS name/address and firewall policy.
3. Install Docker, restore reviewed `/opt/liberty` artifacts, runtime environment files from the secret manager, and a newly issued Cloudflare Tunnel credential.
4. Validate Compose, start the stack, run migrations only if the database migration table shows they are pending, and verify both web replicas.
5. Revoke the lost host's tunnel credential and any host-scoped registry token.

Application containers are stateless; do not restore a Docker volume from `liberty01server` except Alloy's queue, which can be discarded.

## Data host loss or database corruption

1. Stop all writers and enable a maintenance response at the edge.
2. Build an isolated recovery data host with the same major PostgreSQL version. Create fresh TLS credentials and provision the application/FusionAuth roles from the secret manager.
3. List candidate encrypted R2 objects and select the newest object from before the corruption or incident. Record its URI and checksum.
4. Restore on the isolated host first using `ops/backup/postgres-restore.sh`. The script requires `CONFIRM_RESTORE=RESTORE`, verifies outer and inner checksums, restores both dumps into staging databases, and preserves the former database names during the swap.
5. Run integrity and functional checks: migration state, critical row counts, Wagtail site/root pages, sample publication/source relationships, FusionAuth tenant/application/user counts, and a test OIDC login with a recovery account.
6. Route the application host to the recovered data host, start one web replica, and repeat readiness/read-only smoke tests. Start the second replica, FusionAuth, worker, then beat.
7. Retain the damaged disks and timestamped prior databases until incident and legal requirements allow disposal.

Example invocation is documented in `ops/backup/README.md`. The age identity must come from recovery escrow and should be removed from the recovery host immediately after use.

## Redis recovery

Cache loss needs no restore; start an empty cache and expect a temporary latency increase. Broker loss can lose pending tasks and results even with AOF. Start Redis from the last valid AOF when storage is intact; otherwise start empty and reconcile domain state before re-enqueueing idempotent tasks. Never blindly replay notification or publication workflows.

## Observability host loss (`liberty03server`)

Rebuild from reviewed configuration, then restore Grafana/Loki/Prometheus volumes only if a separate volume backup exists and its integrity is known. Metrics and logs are operational evidence but not application source of truth. While central telemetry is absent, use local `docker logs`, host journal, and Cloudflare telemetry; establish a temporary alert path before resuming risky changes.

## R2 media incident

Disable application writes with the affected R2 credential, preserve bucket audit logs, and rotate the token. For deletion or corruption, recover through R2 versioning/replication or the separate media backup policy. Database restore alone does not restore media objects; reconcile database object keys against the bucket inventory.

## Secret compromise

Rotate in dependency order and maintain overlap only where the protocol supports it:

1. Cloudflare API/tunnel and R2 tokens.
2. Registry and deployment webhook credentials.
3. PostgreSQL and Redis credentials, updating clients before revoking old values.
4. FusionAuth client secret, recovery/admin sessions, and SMTP credentials.
5. Django secret key only with an explicit plan for invalidating sessions and signed values.

Assume Docker socket access grants host control. If a container with the socket mounted is compromised, rebuild the host rather than trusting in-place cleanup.

## Return to service

The incident commander approves recovery only after readiness succeeds, public probes are stable, authentication and editorial smoke tests pass, queues are reconciled, a new encrypted backup succeeds, alert delivery works, and monitoring shows no unexplained error or saturation. Communicate restored scope and any known data-loss window.

Within five business days, document cause, timeline, impact, detection gaps, recovery measurements, and owners/dates for corrective work. Convert measured backup age and restore duration into revised RPO/RTO evidence.

