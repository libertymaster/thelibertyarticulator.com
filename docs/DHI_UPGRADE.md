> **0.3.2 update:** Use [STABILIZATION.md](STABILIZATION.md) for the active Debian/core baseline and framework rollback safety. Earlier version-specific commands below are historical context where they differ.

# Hardened-image qualification and migration notes

## Version inputs versus verified deployments

`images.sources.env` retains the supplied infrastructure references and build/utility inputs, with the approved Python builder/runtime changed together to Debian 13. `ops/lock_images.py` pulls them and records actual repository digests on the target platform. No registry digests, successful pulls, or attestation checks are asserted by this delivery.

Authenticate using `docker login dhi.io`. Keep the credential in Docker's configured credential store, not in project files. CI requires read-only DHI_USERNAME/DHI_TOKEN secrets. Fork pull requests do not receive those secrets and must not be granted trusted workflow access merely to make a build pass.

## Python: preserve the runtime ABI

The 0.3.2 baseline uses Debian 13 for both Python stages. The former Debian
source-audit / Alpine dependency-build arrangement is removed. Node has a separate
asset-build stage, not a production application service.

| Stage | Image input | Outputs allowed to cross |
|---|---|---|
| Dependency/application build | `dhi.io/python:3.14.7-debian13-dev` | glibc-compatible virtual environment, source checks, application and collected assets |
| Final runtime | `dhi.io/python:3.14.7-debian13` | Executes matching Python/native modules as UID 10001 |

`check_image_contracts.py` checks Debian release, glibc identity, exact Python
version, implementation, CPU architecture, ABI, interpreter location and base
prefix in both images. The final Docker stage runs `check_runtime.py` as the
non-root runtime user. That check exercises psycopg's binary implementation,
Pillow image codecs, Pydantic Core, cryptography, Brotli, TLS and SQLite and verifies
the exact Django/Wagtail versions. These are implemented gates, not tests already
passed in this authoring environment.

Production dependencies must have compatible wheels. The resolver and Dockerfile
use `--only-binary=:all:` and hashed locks; a missing wheel stops the build instead
of introducing unreviewed compilers or native libraries. Review any failure at
the package/version/architecture boundary. Do not reuse an Alpine virtual
environment or pretend that matching distribution names alone establish native
library compatibility. Qualify the final runtime and its required libraries.

For an existing reviewed image lock, `python3 ops/lock_images.py --refresh-python`
retains non-Python digests. `python3 ops/check_image_contracts.py --python-only`
can isolate Python qualification. The unqualified commands below check all image
sources and are appropriate for a fresh checkout.

## Shell-free services

The application entrypoint and health probes use Python. Redis health uses redis-cli directly. PostgreSQL init uses psql SQL files, and its readiness command invokes pg_isready against TCP. Backups invoke pg_dump/pg_restore directly; media streaming uses Python, not a shell/tar inside the application image.

Redis has an unauthenticated **PING-only** health ACL user. It cannot read or mutate data. App/exporter roles retain their own password authentication and ACL scope; the default user is disabled. Existing pre-0.3 health ACLs are rejected rather than overwritten. Fresh-project preparation is the expected path; coordinate any existing ACL change with credential rotation and a separate review.

Grafana uses the native configuration file provider (`$__file{...}`) in its INI file for the mounted administrator password. It does not depend on a shell evaluating a secret environment-variable suffix. Changing the initial password file does not rotate an account already stored in Grafana's database.

Keycloak is a separately documented exception: its selected DHI image includes Bash and kc.sh, and capability checks verify them. No blanket claim is made that all hardened images include a shell.

## PostgreSQL storage and permissions

The DHI PostgreSQL 18 image uses `/var/lib/postgresql/18/data`. The parent mount is `/var/lib/postgresql`; Compose does not override PGDATA. This differs from the original bundle's non-DHI `/18/docker` layout.

The application and optional identity databases run as the expected postgres UID/GID 70:70, with writable owned data volumes and a narrowly writable socket directory. The qualifier reads the image passwd file and declared PGDATA and refuses a mismatch. Reconcile an image contract change with volume ownership and the runbook; do not blindly chown an existing production volume.

SQL initialization creates separate application and metrics roles on an empty database. TCP readiness establishes server availability; it does **not** prove migrations or role creation succeeded. The next migration/startup step exercises the application credentials. Investigate initialization logs and partial state without deleting data. The local admin socket used by backup/restore must be tested against the resolved image; no superuser password is printed or exposed in command arguments.

**Do not mount old raw database volumes into this new project.** Use an encrypted logical backup and isolated restore for content migration. PostgreSQL major upgrades and changed data-directory conventions require explicit handling.

## Target-host qualification

```sh
python3 ops/lock_images.py
python3 ops/check_image_contracts.py
python3 ops/lock_dependencies.py
MODE=dev ./ops/dc config --quiet
./ops/dev.sh
MODE=dev ./ops/check_configs.sh
```

The image qualifier tests required native executables, PostgreSQL identity/storage metadata, and the Python ABI, then saves `runtime/image-contract-checks.json`. It does not test application startup, backup consistency, Grafana provisioning, metrics, logs, or secure tunnel delivery. Complete those separately before deployment.

Primary references: [Docker glibc/musl](https://docs.docker.com/dhi/explore/security-concepts/glibc-musl/), [DHI PostgreSQL guide](https://hub.docker.com/hardened-images/catalog/dhi/postgres/guides), [Grafana configuration providers](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/), [Keycloak containers](https://www.keycloak.org/server/containers).
