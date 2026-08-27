# Deployment runbook

Use this runbook for application releases and reviewed Compose/configuration changes. The deployer owns execution; the incident commander role is not needed unless the release causes customer impact.

## Preconditions

- CI lint, security, test, build, and image scan jobs passed for the exact commit.
- The production environment approval identifies an operator and change window.
- The application image is immutable and available to `liberty01server` as `sha-<40-character commit>` or by digest.
- Grafana shows no unresolved critical infrastructure alert; both web replicas are healthy.
- The latest encrypted PostgreSQL backup is less than 26 hours old and its most recent restore drill passed.
- Release notes identify migrations, expected duration, feature flags, and rollback constraints.

If a migration removes or transforms data, stop. Use an expand/migrate/contract release sequence instead of a rolling deployment.

## Automated application release

The GitHub production job signs a small JSON payload with `DEPLOY_WEBHOOK_SECRET` and sends it to the localhost-bound webhook through the approved private/protected path. The handler accepts only the configured repository, `refs/heads/main`, a valid commit SHA, and a unique delivery identifier.

Follow the service log on `liberty01server`:

```bash
sudo journalctl -u liberty-deploy-webhook.service --follow
```

The fixed deploy script performs these steps:

1. Validate Compose interpolation.
2. Pull the four application image consumers.
3. Run Django migrations once in an ephemeral container.
4. Replace `web_a`, wait for health, then replace `web_b`.
5. Replace the Celery worker and singleton beat service.
6. Record the successful image and commit under `/var/lib/liberty-deploy`.

Verify after completion:

```bash
curl --fail --silent https://thelibertyarticulator.com/health/
curl --fail --silent https://thelibertyarticulator.com/ready/
docker compose --env-file /etc/liberty/compose.env \
  -f /opt/liberty/deploy/liberty01server/compose.yaml ps
```

Then verify a publication page, search, editor login, a harmless Celery task, HTTP error rate, replica count, and logs for the deployment's request/delivery identifier. Observe for at least 15 minutes before closing the change.

## Manual application release

Use only when the webhook path is impaired but the release is approved:

```bash
sudo -u liberty-deploy /opt/liberty/ops/deployment/deploy.sh \
  0123456789abcdef0123456789abcdef01234567 manual-CHANGE-ID
```

Replace the sample SHA and change identifier. Do not run two release mechanisms concurrently; both scripts lock the deployment state directory.

## Rollback

For code-only failure, read `/var/lib/liberty-deploy/last-successful.env`, confirm that the prior image still exists in the registry, set `APP_IMAGE` to that immutable value, and update `web_a`, `web_b`, worker, and beat in the same health-checked sequence. Do not reverse a database migration automatically.

If the new migration is backward compatible, the old image can operate on the expanded schema. If it is not, declare an incident and use the migration-specific recovery plan. Restoring the entire database is a last resort because it loses all writes after the backup.

## Infrastructure configuration change

1. Save the exact current `docker compose config` output and relevant image IDs in the change record.
2. Validate YAML and component-native configuration (`promtool`, `amtool`, `alloy fmt`, Traefik validation where available) before upload.
3. Apply one tier at a time. Observability first, data second, application last for initial builds; use the smallest affected tier for later changes.
4. Use `docker compose up -d --wait` only for services with trustworthy image health checks. Otherwise inspect service readiness directly.
5. Never use `down -v` in production. Named volumes contain durable state.

For Prometheus rules, run:

```bash
docker run --rm \
  -v /opt/liberty/deploy/liberty03server/prometheus:/etc/prometheus:ro \
  dhi.io/prometheus:3.14.0-debian13 \
  promtool check config /etc/prometheus/prometheus.yml
```

After any Alertmanager change, send a labeled test alert and confirm delivery. After any tunnel or Traefik change, verify the three public hostnames/paths and confirm the origin still has no public listener.

