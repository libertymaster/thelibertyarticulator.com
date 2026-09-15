# Backup and restore

## Policy to decide before launch

Specify an owner, retention period, off-host encrypted destination, recovery point objective (RPO), recovery time objective (RTO), and an age key custodian. No recovery objective has been measured in this bundle. Backups on the same Docker host are not disaster recovery.

The included backup command creates encrypted logical PostgreSQL, media, and recovery-configuration archives. The age public recipient is safe to store in .env. Keep the private identity off the production host and retain a tested recovery copy. Install age on the administrative/backup host before using these scripts. Automatic unattended scheduling and remote transport are deliberately not configured without a destination and key policy.

## Consistent backup window

Database and media are two resources. A pg_dump snapshot alone does not make a separately streamed media archive transactionally consistent. Prevent editor writes/uploads and scheduled/background publishing during the window, wait for active tasks to finish, then take the archives. Public read-only serving can remain available. One approach is a temporary editor Access maintenance policy and stopping Beat/worker after drain; application-specific writers must also be paused. Record the start/end times.

```sh
# In the reviewed maintenance window:
MODE=prod ./ops/dc stop beat worker
MODE=prod ./ops/backup.sh
MODE=prod ./ops/dc up -d worker beat
```

Reopen editing after success. If the backup fails, inspect the exit code and partial directory rather than labeling it complete. Scripts use pipefail and restrictive output permissions. Copy the timestamped backup directory off-host and verify its SHA256SUMS there. Store checksum/signature records in an independently controlled location when authenticity against host compromise matters.

The config archive contains secrets and must stay encrypted. Metrics/log histories and Redis transient cache/broker state are not archived by this command. The database and media are the content recovery sources; scheduler/application tasks need idempotent behavior after recovery.

## Isolated restore drill

Use another checkout and **a new Compose project containing `_restore_` in its name**. The restore script refuses any existing labeled volumes for that project. It does not stop or erase production volumes. Avoid the same local development port when the original test project is still running.

Copy the reviewed source/dependency/image locks for the backed-up release, set a new .env project name, generate new local secrets/runtime config, and make the matching application image available. Do not run migrations/bootstrap before restoring the database: pg_restore supplies the archived schema. Do not restore over an initialized live project.

```sh
# In the separate recovery checkout with fresh .env and reviewed lockfiles:
python3 ops/init_secrets.py
python3 ops/render_config.py
MODE=dev ./ops/dc build web
./ops/restore.sh /absolute/path/to/backup /absolute/path/to/age-private-identity
```

The configuration archive is for controlled recovery inspection, not automatic replacement of the drill's fresh .env/secrets. Database content restores using the freshly initialized application role; no-owner/no-acl avoids restoring ownership from the production environment. The restore connection uses the fresh local PostgreSQL administrator and SET ROLE to the new application owner. Use a matching application/schema release. A fresh Django secret invalidates old sessions; retain the original key through a secure recovery process only when required.

After the script's content and HTTP checks, compare article/source/author/event counts with the original backup record; inspect uploaded images/documents; authenticate; preview a new draft; publish, correct, and unpublish a test page; inspect citations/chronology and scheduler behavior. Record wall-clock restore time and any missing assets. Start Beat/worker only when the restored copy is safely isolated and its outbound email/tunnel behavior is controlled.

## PostgreSQL major versions

This project intentionally uses PostgreSQL 18 and the `/var/lib/postgresql` parent mount with image-declared `/var/lib/postgresql/18/data` PGDATA. It is not safe to mount an existing PostgreSQL 17 raw data directory into it. Use a separately planned logical dump/restore or supported major-upgrade procedure. This fresh project's initialization/role design also does not automatically adopt an arbitrary existing PostgreSQL 18 volume.

## 0.3.0 additions

The source-import records, page revisions and structured evidence live in PostgreSQL and are part of the logical database backup. Source templates/data and image/dependency locks must be retained with the corresponding release. The media helper rejects traversal, symlinks, hardlinks and special files on restore and requires an empty target; no shell is required in the application runtime. Test the local PostgreSQL admin socket before relying on unattended backup.

The optional Keycloak database is NOT included by the base backup script. See KEYCLOAK.md for separate identity recovery. No backup, restore, R2 transfer or off-host copy has been executed in the authoring environment.
