#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

SQL_FILE="docker/postgres/bootstrap.sql"

if [ ! -f "$SQL_FILE" ]; then
    echo "ERROR: missing PostgreSQL bootstrap file: $SQL_FILE" >&2
    exit 1
fi

if [ ! -x "./ops/dc" ]; then
    echo "ERROR: ./ops/dc is missing or not executable" >&2
    exit 1
fi

echo "Checking PostgreSQL readiness..."

./ops/dc exec -T --user 70:70 postgres \
    pg_isready \
    -h /var/run/postgresql \
    -U postgres \
    -d postgres >/dev/null

echo "Applying PostgreSQL bootstrap..."

./ops/dc exec -T --user 70:70 postgres \
    psql \
    -X \
    -v ON_ERROR_STOP=1 \
    -h /var/run/postgresql \
    -U postgres \
    -d postgres \
    -f - < "$SQL_FILE"

echo "PostgreSQL bootstrap completed successfully."
