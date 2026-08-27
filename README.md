# The Liberty Articulator

**Investigating under the microscope of liberty. Analyzing through the
telescope of history.**

The Liberty Articulator is a source-forward digital journal built for long-form historical inquiry. It combines a carefully designed public reading experience with Wagtail's editorial workflow, structured citations, contributor profiles, taxonomy, series, search, and production operations for a segmented three-server deployment.

## What is included

- Django 6 / Wagtail 7.4 editorial application

- Publication pages with versions, contributors, sources, categories, keywords, citation metadata, JSON-LD, and featured content

- Contributor and ORCID profiles, bibliographic source records, and series

- Full-text site search and filterable publication archive

- Health, readiness, and Prometheus metric endpoints

- FusionAuth-compatible OIDC boundary with secure local fallback

- Celery worker and beat configuration

- Responsive, accessible, dependency-free public frontend

- Cloudflare Tunnel + Traefik edge configuration

- PostgreSQL, Redis, FusionAuth, backup, and R2 integration

- Prometheus, Alertmanager, Grafana, Loki, Alloy, and exporters

- CI, security checks, tests, deployment scripts, and incident runbooks

## Local quick start

Python 3.14 and Docker are expected.

```bash
cp .env.example .env
make install
make migrate
make seed
make run
```

Open <http://localhost:8000> for the journal and
<http://localhost:8000/admin/> for Wagtail. Create an editor account with:

```bash
.venv/bin/python manage.py createsuperuser
```

SQLite and an in-memory cache are used by default. To exercise the production
data services locally:

```bash
docker compose -f compose.dev.yaml up -d
```

Then set `DATABASE_URL=postgresql://liberty:local-development-only@localhost:5432/liberty`
and the Redis URLs shown in `.env.example`.

## Verification

```bash
make lint
make test
make coverage
.venv/bin/python manage.py check
```

`make check` also runs Django's production deployment checks with safe ephemeral
values. The app provides:

- `/health/` — process liveness; does not depend on downstream services
- `/ready/` — database and cache readiness
- `/metrics/` — Prometheus-format application metrics

## Architecture

Production is intentionally split by trust boundary:

1. **liberty01server — edge/application:** Cloudflare Tunnel, Traefik, two web
   replicas, Celery worker, and exactly one beat scheduler.
2. **liberty02server — data/identity:** PostgreSQL, isolated Redis instances,
   FusionAuth, encrypted backups, and data exporters.
3. **liberty03server — control/observability:** Prometheus, Alertmanager,
   Grafana, Loki, Blackbox Exporter, and central monitoring.

Only the edge tier accepts public web traffic. Data and control services are
reachable over a private routed network with firewall ACLs. Media is stored in
Cloudflare R2 behind `assets.thelibertyarticulator.com`.

See [docs/architecture.md](docs/architecture.md) and the runbooks under
`ops/runbooks/` before deploying.

## Deployment

The deployment manifests are templates that require site-specific secrets,
Cloudflare tunnel credentials, host addresses, TLS policy, and backup keys.
Start with `.env.example` and `.github/example-secrets.env`; never commit filled
secret files. Validate each Compose model before first use:

```bash
docker compose --env-file /secure/path/liberty.env \
  -f deploy/liberty01server/compose.yaml config
```

Trusted main and tag builds use the hardened `dhi.io` Python bases and require
the read-only `DHI_USERNAME` and `DHI_TOKEN` repository secrets. Pull-request
builds use the public Python 3.14 image through explicit build arguments, so
credentials are never exposed to untrusted forks.

Follow [ops/runbooks/deployment.md](ops/runbooks/deployment.md) for the staged
rollout and rollback sequence.

## Editorial principles

The implementation keeps claims, contributors, citations, and revision history
first-class. A successful publishing workflow should make it easy for readers
to distinguish evidence, interpretation, and editorial change over time.

## License

Proprietary. See `LICENSE`.
