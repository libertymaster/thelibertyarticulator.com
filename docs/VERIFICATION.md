# Verification report: 0.3.2 Debian/core stabilization

Date: 14 September 2026.
Baseline source: the supplied complete 0.3.1 archive. The original remains unchanged.

**Status: revised source and local safety checks completed. This is not a completed
Docker image build or a verified production deployment.** Docker is unavailable
in the authoring container. Direct PyPI/npm probes failed DNS resolution; this is
an environment limitation, not evidence that the requested releases do not exist.
Django and Wagtail are not installed here. No alternative framework versions were
silently installed or substituted.

## Executed locally

| Check | Result |
|---|---|
| Static/helper tests | 109 passed on host Python 3.13.5 |
| Lock integrity/failure tests | Included in the 109: changed inputs/outputs, old/partial metadata, selective image preservation, candidate failure, interrupted publication recovery, resolver mutex, symlink rejection |
| Syntax parsing | 80 Python sources, all JSON/YAML/TOML files, and 8 shell scripts passed; see source-check evidence for counts |
| Frontend syntax | 15 non-generated TypeScript/TSX modules transpiled successfully using locally available TypeScript 5.8.3 and Node 22.16.0; not type checking or bundling |
| Public data contracts | `python ops/export_contracts.py --check` passed with unchanged generated outputs |
| Whitespace/line endings | `python ops/check_style.py` passed |
| Scope comparison | Existing journal code/migrations, content, contracts, frontend, templates, static assets, monitoring configurations and original imported reference files match 0.3.1 byte-for-byte |
| Infrastructure inputs | Every non-Python image source and the five existing Compose overrides are unchanged |
| Guarded source updater | 14 disposable-copy tests passed: apply/rollback, conflict refusal, interrupted-write recovery and preservation; see stabilization-updater-checks.json |
| Packaging | Archive CRC/content equality, per-file SHA256SUMS and script permissions checked during packaging; archive hashes are supplied separately |

The static suite tests the pure migration-history classifier and inspects the
management-command boundary. It does **not** execute Django's MigrationLoader or
prove a database downgrade safe. The contract tests use the locally installed
Pydantic, not a resolved production environment. The compiler used for syntax
inspection is likewise not the unresolved frontend lock's compiler.

Evidence is in `docs/evidence/stabilization-*`. The previous version's reports
and screenshots are retained as historical evidence, not rerun-runtime evidence.

## Implemented target-host gates, not executed here

- Both real DHI images must identify as CPython 3.14.7 / Debian 13 / glibc and agree
  on their interpreter paths, base prefix, ABI, architecture and libc contract.
- Python dependency resolution uses the approved core inputs and pip-tools 7.6.1.
  Production wheels install with hashes and pass pip check in the Debian builder.
  Development is constrained by the production lock. Existing npm locks are retained
  when their root manifest agrees, unless explicit refresh is requested.
- Actual native runtime tests exercise psycopg binary, Pillow PNG/JPEG/WebP,
  Pydantic Core, cryptography, Brotli, TLS and SQLite, plus exact framework versions.
- The actual asset build must generate validators, type-check, bundle and pass
  frontend unit tests. Static syntax inspection is not a substitute.
- `MODE=dev python3 ops/validate_app.py --build` tests the final immutable image ID
  with no network, host bind mounts or deployment secrets. Django checks, migration
  drift detection and the Django suite use ephemeral SQLite. The five newly supplied
  Django stabilization tests are part of that pending suite.
- `safe_migrate` checks database history and drift before forward migration. It
  neither reverses migrations nor certifies that a newer framework's database is
  semantically compatible.
- PostgreSQL/Redis execution, actual Wagtail edit/preview/publish behavior, browser
  interactions, scheduled publishing, monitoring, secure ingress, security scans,
  load tests, notification delivery and backup/restore still require the test host.

No deployable image digest or dependency lock has been invented. A missing image,
missing wheel, dependency conflict or failed native check is a blocking failure.
Do not force installation, ignore test failures or reuse a newer-framework database
merely to get past a gate.

## Scope and safety

The package changes source in a separate working copy. The patch modifies only
listed source files after preflight and backup; it does not write .env, secrets,
existing locks, volumes or publication data, and performs no Docker operations.
Lock re-resolution is a separate explicit step that backs up prior locks. All tests
here used disposable local fixtures, never a deployment host.

Use a fresh project/database for initial qualification. Preserve any existing
Django 6.1 / Wagtail 8 database and evaluate a compatible backup or reviewed content
migration separately. No live site, repository, DNS, Cloudflare configuration or
user server was accessed or changed.
