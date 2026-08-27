# Changelog

All notable changes are recorded here. This project follows Keep a Changelog conventions and intends to use semantic versioning once the public API is declared stable.

## Unreleased

### Added

- Initial Django 6 and Wagtail 7 publication platform.
- Publications, contributors, bibliographic sources, taxonomy, series, search, and FusionAuth OIDC integration.
- Source-forward citation rendering and CSL-JSON source representation.
- Three-tier production Compose architecture for edge/application, data/identity, and observability hosts.
- Cloudflare Tunnel and Traefik routing with security headers, rate limiting, replica health checks, and a private metrics route.
- TLS-only PostgreSQL and Redis data services, FusionAuth, Celery worker, and singleton scheduler.
- Central metrics, logs, alerts, and a provisioned Grafana operations dashboard.
- Encrypted R2 PostgreSQL backup and staged restore tooling with recovery runbooks.
- Six-phase CI/CD workflow and HMAC-authenticated deployment webhook.

### Security

- Production secrets are required at runtime and have no checked-in values.
- Application containers use read-only filesystems, dropped capabilities, resource limits, and `no-new-privileges` where compatible.
- No data or observability service is intended to be Internet reachable.

## 0.1.0 - 2026-08-26

### Added

- Initial project scaffold.

