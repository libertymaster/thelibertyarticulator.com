# PostgreSQL backup and restore

The backup job creates PostgreSQL custom-format dumps for the application and FusionAuth databases, records checksums and a manifest, encrypts the complete archive with `age`, and only then uploads it to Cloudflare R2. No unencrypted dump is written to persistent storage.

## Required secret material

Store these values in `/etc/liberty/backup.env` with mode `0600`; do not commit that file:

- `POSTGRES_ADMIN_USER` and `POSTGRES_ADMIN_PASSWORD`
- `POSTGRES_APP_DATABASE` and `FUSIONAUTH_DATABASE`
- `AGE_RECIPIENT` (the public age recipient used for encryption)
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` for an R2 token restricted to the backup prefix
- `R2_BUCKET` and `R2_ENDPOINT_URL`

The private age identity must be kept outside the three production servers and in an offline recovery escrow. A copy may be mounted temporarily for an approved restore. Test that escrowed identities can decrypt a sample backup at least quarterly.

## Schedule a backup

Prepare host directories owned by UID/GID `10001`, then mount them through the data-tier Compose file:

```text
/var/lib/liberty/backups
/var/lib/liberty/node-exporter
```

Run the one-shot service from a systemd timer or another host scheduler:

```bash
docker compose --env-file /etc/liberty/compose.env \
  -f /opt/liberty/deploy/liberty02server/compose.yaml \
  --profile backup run --rm backup
```

A daily backup with a 26-hour stale alert supports a nominal 24-hour recovery point objective. R2 lifecycle policy should retain daily objects for 35 days, monthly objects for 13 months, and protected annual recovery points according to policy. R2 object lock or a second-account copy is strongly recommended.

## Restore drill

Restores are intentionally gated and must occur during a maintenance window. Stop both application replicas, Celery worker, Celery beat, and FusionAuth before starting. Copy the age identity to a temporary root-readable path, then run the backup tool image with the restore script as its entrypoint.

```bash
CONFIRM_RESTORE=RESTORE \
AGE_IDENTITY_FILE=/run/age/identity.txt \
docker compose --env-file /etc/liberty/compose.env \
  -f /opt/liberty/deploy/liberty02server/compose.yaml \
  --profile backup run --rm --entrypoint /usr/local/bin/postgres-restore.sh backup \
  s3://liberty-backups/postgres/2026/08/liberty-postgres-YYYYMMDDTHHMMSSZ.tar.gz.age
```

The restore script verifies the outer checksum, decrypts into ephemeral storage, verifies the inner dump checksums, restores into staging databases, and swaps names only after both restores succeed. The pre-restore databases remain under timestamped names for rollback. Drop them only in a later, separately approved change after functional validation.

Never perform the first restore of a backup on production. Exercise it first on an isolated recovery host and record dump size, restore duration, integrity checks, and application smoke-test results.
