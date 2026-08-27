# Production deployment configuration

Each server owns one Compose project. Copy only the repository and configuration needed by that tier, keep secret files below `/etc/liberty`, and use private DNS for `liberty01.internal`, `liberty02.internal`, and `liberty03.internal`.

## Common preparation

1. Install a supported Docker Engine and Compose v2 release. Configure daemon log rotation and security updates.
2. Create a dedicated operator group. Access to Docker is root-equivalent; do not grant it to the application runtime account.
3. Create `/opt/liberty` from a reviewed release artifact and make it read-only to service accounts.
4. Copy the relevant `compose.env.example` to `/etc/liberty/compose.env`, populate it from the secret manager, and set mode `0600`.
5. Resolve every image tag to a reviewed digest in the environment file. The checked-in tags are versioned starting points, not a substitute for immutable production references.
6. Permit only the flows in `docs/architecture.md`; reject all other inbound private and public traffic.

Validate a tier without starting it:

```bash
docker compose --env-file /etc/liberty/compose.env \
  -f /opt/liberty/deploy/liberty03server/compose.yaml config --quiet
```

Compose interpolation reads `compose.env`; container `env_file` files are separate and must not be committed. A blank required value is an intentional validation failure.

## TLS material

PostgreSQL expects `server.crt`, `server.key`, and `ca.crt` in `POSTGRES_TLS_DIR`. Redis expects the same names in `REDIS_TLS_DIR`. Issue them from a private CA, include `liberty02.internal` and its private address in the certificate SANs, and rotate before expiry. The server key must be readable by its container account and no broader than mode `0600`. Application URLs must use `sslmode=verify-full` for PostgreSQL and `rediss://` with CA verification for Redis once trust paths are mounted in the application image.

Do not reuse the Cloudflare origin/tunnel credential as an internal CA or database credential.

## Start order

Bring up `liberty03server`, then `liberty02server`, and finally `liberty01server`. This gives Alloy valid remote-write destinations before application/data telemetry starts. Create databases only through the PostgreSQL initialization hook on an empty data volume; it is not a general migration mechanism.

The PostgreSQL backup service has the `backup` profile and does not run during a normal `up -d`. Schedule it explicitly after verifying an age recipient and R2 least-privilege token.

## Production readiness gates

- All containers expected to be healthy/running for 15 minutes.
- Both public blackbox probes succeed and the TLS-expiry metric is present.
- A synthetic critical alert reaches the on-call receiver.
- Database, cache, broker, and OIDC readiness pass from an application container.
- An encrypted backup uploads, downloads, decrypts, and restores on an isolated recovery host.
- Cloudflare shows no public origin DNS record and the hosts have no public service listeners.
- Grafana, Prometheus, Alertmanager, and the deployment webhook are reachable only through the operator network or an explicitly protected proxy.

