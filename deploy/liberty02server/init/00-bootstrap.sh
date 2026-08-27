#!/usr/bin/env bash
set -Eeuo pipefail

required=(
  POSTGRES_APP_DATABASE
  POSTGRES_APP_USER
  POSTGRES_APP_PASSWORD
  FUSIONAUTH_DATABASE
  FUSIONAUTH_DATABASE_USER
  FUSIONAUTH_DATABASE_PASSWORD
)

for variable in "${required[@]}"; do
  if [[ -z "${!variable:-}" ]]; then
    printf 'Missing required variable: %s\n' "$variable" >&2
    exit 64
  fi
done

identifier_pattern='^[a-z_][a-z0-9_]{0,62}$'
for variable in POSTGRES_APP_DATABASE POSTGRES_APP_USER FUSIONAUTH_DATABASE FUSIONAUTH_DATABASE_USER; do
  if [[ ! "${!variable}" =~ $identifier_pattern ]]; then
    printf '%s must be a safe PostgreSQL identifier\n' "$variable" >&2
    exit 64
  fi
done

psql --set=ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" \
  --dbname postgres \
  --set=app_database="$POSTGRES_APP_DATABASE" \
  --set=app_user="$POSTGRES_APP_USER" \
  --set=app_password="$POSTGRES_APP_PASSWORD" \
  --set=fusionauth_database="$FUSIONAUTH_DATABASE" \
  --set=fusionauth_user="$FUSIONAUTH_DATABASE_USER" \
  --set=fusionauth_password="$FUSIONAUTH_DATABASE_PASSWORD" \
  --file /docker-entrypoint-initdb.d/sql/01-create-databases.sql

