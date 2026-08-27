# Contributing

Changes should preserve the journal's source-forward editorial model, accessibility, and operational safety. Keep domain rules in selectors/services, keep views thin, and accompany behavior changes with tests and documentation.

## Local setup

The supported runtime is Python 3.14. Create an isolated environment, install development dependencies, and copy the example environment file:

```bash
python3.14 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
cp .env.example .env
python manage.py migrate
python manage.py loaddata fixtures/initial_categories.json fixtures/initial_keywords.json
python manage.py runserver
```

Alternatively, use `compose.dev.yaml` for PostgreSQL and Redis, then run the Django process from the virtual environment. Development secrets and SQLite files remain local and must never be committed.

## Before opening a pull request

Run the same core checks as CI:

```bash
ruff check apps config tests
ruff format --check apps config tests
mypy apps config
bandit -r apps config -x tests
pytest
python manage.py check
```

New models require committed migrations. New public behavior requires unit or integration tests. Template changes need keyboard and narrow-viewport checks; semantic HTML and visible focus must be preserved. Do not weaken CSRF, cookie, host, proxy, storage, or authentication settings to make a test pass.

## Structure and conventions

- `apps/<domain>/models.py` owns persisted domain concepts.
- `selectors.py` owns reusable read queries and publication visibility rules.
- `services.py` owns orchestration and pure transformations.
- `tasks.py` contains idempotent Celery entry points; tasks can be delivered more than once.
- `config/settings/` separates shared, development, testing, and production policy.
- `deploy/` and `ops/` changes require an explicit rollout and rollback note.
- `fixtures/` contains only non-secret baseline taxonomy. Users are provisioned through FusionAuth or a deliberate `createsuperuser` operation.

Use type annotations for new Python code. Keep lines within 100 characters. Ruff controls import ordering and formatting. Avoid broad exception handling unless the failure is intentionally contained and observable.

## Database changes

Application deployments are rolling, so a migration must work with both the old and new application image during the update window. Prefer expand/migrate/contract:

1. Add nullable fields, new tables, or compatible indexes.
2. Deploy code that writes both shapes and backfill in an idempotent task.
3. Switch readers after backfill verification.
4. Remove old fields only in a later release.

Never combine an irreversible data migration with an unrelated feature. Record expected duration and lock behavior for large tables. Test the migration against a production-shaped database copy with sensitive data removed.

## Security and dependencies

Do not put secrets, access tokens, user data, private source material, or production exports in issues, fixtures, snapshots, logs, or commits. Report vulnerabilities privately according to the repository security policy rather than opening a public issue.

Dependency changes must be pinned, justified, and pass `pip-audit`. Container tag changes require release-note review and an image scan. Prefer official or hardened images and immutable digests in the deployed environment.

## Review and release

Pull requests require the template checklist, passing CI, and code-owner approval. The default branch is protected. Production deployment requires the GitHub environment approval, while infrastructure changes follow `ops/runbooks/deployment.md`. User-visible changes belong in `docs/CHANGELOG.md` under **Unreleased**.

