## Summary

Describe the user or operator outcome and why this change is needed.

## Validation

- [ ] Tests cover the changed behavior and pass locally.
- [ ] Ruff formatting/lint, mypy, and Django checks pass.
- [ ] I tested relevant keyboard, narrow viewport, error, and empty states.
- [ ] New or changed behavior is documented and the changelog is updated.

## Data and operations

- [ ] No database change, or migrations are backward compatible and reviewed.
- [ ] Celery tasks are idempotent and safe under duplicate delivery.
- [ ] Deployment, observability, capacity, and rollback effects are described below.
- [ ] Infrastructure changes include native configuration validation and a rollback plan.

Deployment/rollback notes:

<!-- State migration duration/locking, feature flags, expected metrics, and exact rollback constraints. -->

## Security and privacy

- [ ] No secret, private key, production export, personal data, or unpublished source material is included.
- [ ] Inputs, authorization, object visibility, redirects, uploads, and error disclosure were considered.
- [ ] Dependency/image changes are pinned, audited, and justified.
- [ ] Logs and metrics avoid credentials, tokens, content bodies, and unnecessary identifiers.
- [ ] I followed the private reporting process for any vulnerability discovered.

