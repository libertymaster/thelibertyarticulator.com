#!/usr/bin/env bash
set -Eeuo pipefail

umask 077

readonly BACKUP_OUTPUT_DIR="${BACKUP_OUTPUT_DIR:-/backups}"
readonly BACKUP_METRICS_FILE="${BACKUP_METRICS_FILE:-}"
readonly LOCAL_RETENTION_DAYS="${LOCAL_RETENTION_DAYS:-14}"
readonly R2_PREFIX="${R2_PREFIX:-postgres}"
readonly UPLOAD_TO_R2="${UPLOAD_TO_R2:-true}"

temporary_directory=""
backup_succeeded=0

log() {
  printf '%s %s\n' "$(date --utc +'%Y-%m-%dT%H:%M:%SZ')" "$*" >&2
}

die() {
  log "ERROR: $*"
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

require_variable() {
  [[ -n "${!1:-}" ]] || die "Required environment variable is empty: $1"
}

write_metrics() {
  [[ -n "$BACKUP_METRICS_FILE" ]] || return 0

  local metrics_directory previous_success metrics_tmp
  metrics_directory="$(dirname "$BACKUP_METRICS_FILE")"
  mkdir -p "$metrics_directory"
  previous_success="0"

  if [[ -f "$BACKUP_METRICS_FILE" ]]; then
    previous_success="$(awk '$1 == "liberty_postgres_backup_last_success_timestamp_seconds" { print $2 }' "$BACKUP_METRICS_FILE" | tail -n 1)"
    previous_success="${previous_success:-0}"
  fi

  if [[ "$backup_succeeded" -eq 1 ]]; then
    previous_success="$(date +%s)"
  fi

  metrics_tmp="$(mktemp "${BACKUP_METRICS_FILE}.tmp.XXXXXX")"
  {
    printf '# HELP liberty_postgres_backup_last_success_timestamp_seconds Unix timestamp of the latest successful encrypted PostgreSQL backup.\n'
    printf '# TYPE liberty_postgres_backup_last_success_timestamp_seconds gauge\n'
    printf 'liberty_postgres_backup_last_success_timestamp_seconds %s\n' "$previous_success"
    printf '# HELP liberty_postgres_backup_last_status Whether the latest attempted PostgreSQL backup succeeded.\n'
    printf '# TYPE liberty_postgres_backup_last_status gauge\n'
    printf 'liberty_postgres_backup_last_status %s\n' "$backup_succeeded"
  } >"$metrics_tmp"
  mv -f "$metrics_tmp" "$BACKUP_METRICS_FILE"
}

cleanup() {
  local exit_code=$?
  if [[ -n "$temporary_directory" && -d "$temporary_directory" ]]; then
    rm -rf -- "$temporary_directory"
  fi
  write_metrics || log "WARNING: could not update backup metrics"
  exit "$exit_code"
}
trap cleanup EXIT

for command_name in age aws flock jq pg_dump sha256sum tar; do
  require_command "$command_name"
done

for variable in \
  AGE_RECIPIENT \
  POSTGRES_ADMIN_PASSWORD \
  POSTGRES_ADMIN_USER \
  POSTGRES_APP_DATABASE \
  FUSIONAUTH_DATABASE; do
  require_variable "$variable"
done

if [[ "$UPLOAD_TO_R2" == "true" ]]; then
  for variable in AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY R2_BUCKET R2_ENDPOINT_URL; do
    require_variable "$variable"
  done
elif [[ "$UPLOAD_TO_R2" != "false" ]]; then
  die "UPLOAD_TO_R2 must be true or false"
fi

[[ "$LOCAL_RETENTION_DAYS" =~ ^[0-9]+$ ]] || die "LOCAL_RETENTION_DAYS must be an integer"
mkdir -p "$BACKUP_OUTPUT_DIR"

exec 9>"$BACKUP_OUTPUT_DIR/.postgres-backup.lock"
flock -n 9 || die "Another PostgreSQL backup is already running"

temporary_directory="$(mktemp -d "${TMPDIR:-/tmp}/liberty-backup.XXXXXX")"
readonly timestamp="$(date --utc +'%Y%m%dT%H%M%SZ')"
readonly archive_basename="liberty-postgres-${timestamp}"
readonly encrypted_archive="$BACKUP_OUTPUT_DIR/${archive_basename}.tar.gz.age"
readonly encrypted_checksum="${encrypted_archive}.sha256"

export PGHOST="${PGHOST:-postgres}"
export PGPORT="${PGPORT:-5432}"
export PGUSER="$POSTGRES_ADMIN_USER"
export PGPASSWORD="$POSTGRES_ADMIN_PASSWORD"
export PGSSLMODE="${PGSSLMODE:-require}"

log "Creating consistent custom-format database dumps"
pg_dump \
  --format=custom \
  --compress=zstd:6 \
  --no-owner \
  --no-acl \
  --dbname="$POSTGRES_APP_DATABASE" \
  --file="$temporary_directory/application.dump"

pg_dump \
  --format=custom \
  --compress=zstd:6 \
  --no-owner \
  --no-acl \
  --dbname="$FUSIONAUTH_DATABASE" \
  --file="$temporary_directory/fusionauth.dump"

(
  cd "$temporary_directory"
  sha256sum application.dump fusionauth.dump >manifest.sha256
)

jq --null-input \
  --arg created_at "$(date --utc +'%Y-%m-%dT%H:%M:%SZ')" \
  --arg application_database "$POSTGRES_APP_DATABASE" \
  --arg fusionauth_database "$FUSIONAUTH_DATABASE" \
  --arg postgres_host "$PGHOST" \
  --arg pg_dump_version "$(pg_dump --version)" \
  '{
    format_version: 1,
    created_at: $created_at,
    databases: {
      application: $application_database,
      fusionauth: $fusionauth_database
    },
    source_host: $postgres_host,
    pg_dump_version: $pg_dump_version
  }' >"$temporary_directory/manifest.json"

log "Encrypting backup before it leaves temporary storage"
tar -C "$temporary_directory" -czf - \
  application.dump fusionauth.dump manifest.json manifest.sha256 \
  | age --encrypt --recipient "$AGE_RECIPIENT" --output "$encrypted_archive"

(
  cd "$BACKUP_OUTPUT_DIR"
  sha256sum "$(basename "$encrypted_archive")" >"$(basename "$encrypted_checksum")"
)

if [[ "$UPLOAD_TO_R2" == "true" ]]; then
  readonly remote_directory="s3://${R2_BUCKET}/${R2_PREFIX}/$(date --utc +'%Y/%m')"
  log "Uploading encrypted archive and checksum to R2"
  aws --endpoint-url "$R2_ENDPOINT_URL" s3 cp \
    --only-show-errors \
    "$encrypted_archive" "$remote_directory/$(basename "$encrypted_archive")"
  aws --endpoint-url "$R2_ENDPOINT_URL" s3 cp \
    --only-show-errors \
    "$encrypted_checksum" "$remote_directory/$(basename "$encrypted_checksum")"
fi

backup_succeeded=1
log "Backup complete: $(basename "$encrypted_archive")"

if (( LOCAL_RETENTION_DAYS > 0 )); then
  find "$BACKUP_OUTPUT_DIR" -maxdepth 1 -type f \
    \( -name 'liberty-postgres-*.tar.gz.age' -o -name 'liberty-postgres-*.tar.gz.age.sha256' \) \
    -mtime "+$LOCAL_RETENTION_DAYS" -delete
fi

