#!/usr/bin/env bash
set -Eeuo pipefail

umask 077

temporary_directory=""

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

cleanup() {
  local exit_code=$?
  if [[ -n "$temporary_directory" && -d "$temporary_directory" ]]; then
    rm -rf -- "$temporary_directory"
  fi
  exit "$exit_code"
}
trap cleanup EXIT

if [[ "${CONFIRM_RESTORE:-}" != "RESTORE" ]]; then
  die "Refusing destructive operation; set CONFIRM_RESTORE=RESTORE after stopping all application writers"
fi

for command_name in age aws createdb jq pg_restore psql sha256sum tar; do
  require_command "$command_name"
done

for variable in \
  AGE_IDENTITY_FILE \
  POSTGRES_ADMIN_PASSWORD \
  POSTGRES_ADMIN_USER \
  POSTGRES_APP_DATABASE \
  POSTGRES_APP_USER \
  FUSIONAUTH_DATABASE \
  FUSIONAUTH_DATABASE_USER; do
  require_variable "$variable"
done

[[ -r "$AGE_IDENTITY_FILE" ]] || die "AGE_IDENTITY_FILE is not readable"

readonly source_archive="${1:-${RESTORE_SOURCE:-}}"
[[ -n "$source_archive" ]] || die "Usage: postgres-restore.sh <local .age file or s3:// URI>"

identifier_pattern='^[a-z_][a-z0-9_]{0,39}$'
for variable in POSTGRES_APP_DATABASE POSTGRES_APP_USER FUSIONAUTH_DATABASE FUSIONAUTH_DATABASE_USER; do
  [[ "${!variable}" =~ $identifier_pattern ]] || die "$variable is not a safe PostgreSQL identifier"
done

temporary_directory="$(mktemp -d "${TMPDIR:-/tmp}/liberty-restore.XXXXXX")"
readonly local_archive="$temporary_directory/backup.tar.gz.age"
readonly local_checksum="$temporary_directory/backup.tar.gz.age.sha256"

if [[ "$source_archive" == s3://* ]]; then
  require_variable R2_ENDPOINT_URL
  log "Downloading encrypted archive from R2"
  aws --endpoint-url "$R2_ENDPOINT_URL" s3 cp --only-show-errors "$source_archive" "$local_archive"
  aws --endpoint-url "$R2_ENDPOINT_URL" s3 cp --only-show-errors "${source_archive}.sha256" "$local_checksum"
else
  [[ -r "$source_archive" ]] || die "Backup archive is not readable: $source_archive"
  [[ -r "${source_archive}.sha256" ]] || die "Checksum file is missing: ${source_archive}.sha256"
  cp -- "$source_archive" "$local_archive"
  cp -- "${source_archive}.sha256" "$local_checksum"
fi

# Normalize the checksum filename without trusting its source path.
readonly expected_checksum="$(awk 'NR == 1 { print $1 }' "$local_checksum")"
[[ "$expected_checksum" =~ ^[0-9a-fA-F]{64}$ ]] || die "Encrypted archive checksum is malformed"
readonly actual_checksum="$(sha256sum "$local_archive" | awk '{ print $1 }')"
[[ "$actual_checksum" == "$expected_checksum" ]] || die "Encrypted archive checksum does not match"

log "Decrypting and inspecting archive"
age --decrypt --identity "$AGE_IDENTITY_FILE" \
  --output "$temporary_directory/backup.tar.gz" "$local_archive"

while IFS= read -r archive_entry; do
  case "$archive_entry" in
    /*|../*|*/../*|*/..)
      die "Archive contains an unsafe path: $archive_entry"
      ;;
  esac
done < <(tar -tzf "$temporary_directory/backup.tar.gz")

tar -xzf "$temporary_directory/backup.tar.gz" -C "$temporary_directory"
for expected_file in application.dump fusionauth.dump manifest.json manifest.sha256; do
  [[ -f "$temporary_directory/$expected_file" ]] || die "Archive is missing $expected_file"
done

(
  cd "$temporary_directory"
  sha256sum --check manifest.sha256
)

[[ "$(jq -r '.format_version' "$temporary_directory/manifest.json")" == "1" ]] \
  || die "Unsupported backup manifest version"

export PGHOST="${PGHOST:-postgres}"
export PGPORT="${PGPORT:-5432}"
export PGUSER="$POSTGRES_ADMIN_USER"
export PGPASSWORD="$POSTGRES_ADMIN_PASSWORD"
export PGSSLMODE="${PGSSLMODE:-require}"

psql --dbname=postgres --set=ON_ERROR_STOP=1 --tuples-only --no-align \
  --command="SELECT 1 FROM pg_roles WHERE rolname = '$POSTGRES_APP_USER'" | grep -qx 1 \
  || die "Application owner role does not exist"
psql --dbname=postgres --set=ON_ERROR_STOP=1 --tuples-only --no-align \
  --command="SELECT 1 FROM pg_roles WHERE rolname = '$FUSIONAUTH_DATABASE_USER'" | grep -qx 1 \
  || die "FusionAuth owner role does not exist"

readonly restore_suffix="$(date --utc +'%Y%m%d%H%M%S')"
readonly application_stage="${POSTGRES_APP_DATABASE}_restore_${restore_suffix}"
readonly fusionauth_stage="${FUSIONAUTH_DATABASE}_restore_${restore_suffix}"
readonly application_previous="${POSTGRES_APP_DATABASE}_before_${restore_suffix}"
readonly fusionauth_previous="${FUSIONAUTH_DATABASE}_before_${restore_suffix}"

database_exists() {
  psql --dbname=postgres --set=ON_ERROR_STOP=1 --tuples-only --no-align \
    --set=database_name="$1" \
    --command="SELECT 1 FROM pg_database WHERE datname = :'database_name'" | grep -qx 1
}

database_exists "$POSTGRES_APP_DATABASE" || die "Target application database does not exist"
database_exists "$FUSIONAUTH_DATABASE" || die "Target FusionAuth database does not exist"

log "Restoring into isolated staging databases"
createdb --owner="$POSTGRES_APP_USER" "$application_stage"
createdb --owner="$FUSIONAUTH_DATABASE_USER" "$fusionauth_stage"

pg_restore \
  --exit-on-error \
  --no-owner \
  --no-acl \
  --role="$POSTGRES_APP_USER" \
  --dbname="$application_stage" \
  "$temporary_directory/application.dump"

pg_restore \
  --exit-on-error \
  --no-owner \
  --no-acl \
  --role="$FUSIONAUTH_DATABASE_USER" \
  --dbname="$fusionauth_stage" \
  "$temporary_directory/fusionauth.dump"

psql --dbname="$application_stage" --set=ON_ERROR_STOP=1 --command="SELECT 1" >/dev/null
psql --dbname="$fusionauth_stage" --set=ON_ERROR_STOP=1 --command="SELECT 1" >/dev/null

log "Disconnecting clients and atomically swapping restored databases"
psql --dbname=postgres \
  --set=ON_ERROR_STOP=1 \
  --set=app_database="$POSTGRES_APP_DATABASE" \
  --set=fusionauth_database="$FUSIONAUTH_DATABASE" \
  --set=app_stage="$application_stage" \
  --set=fusionauth_stage="$fusionauth_stage" \
  --set=app_previous="$application_previous" \
  --set=fusionauth_previous="$fusionauth_previous" <<'SQL'
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname IN (:'app_database', :'fusionauth_database')
  AND pid <> pg_backend_pid();

BEGIN;
SELECT format('ALTER DATABASE %I RENAME TO %I', :'app_database', :'app_previous') \gexec
SELECT format('ALTER DATABASE %I RENAME TO %I', :'app_stage', :'app_database') \gexec
SELECT format('ALTER DATABASE %I RENAME TO %I', :'fusionauth_database', :'fusionauth_previous') \gexec
SELECT format('ALTER DATABASE %I RENAME TO %I', :'fusionauth_stage', :'fusionauth_database') \gexec
COMMIT;
SQL

log "Restore complete. Previous databases were preserved as:"
log "  $application_previous"
log "  $fusionauth_previous"
log "Restart application writers, validate, then remove the previous databases during a separate approved change."

