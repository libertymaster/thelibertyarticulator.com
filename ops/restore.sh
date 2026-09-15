#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ $# == 2 ]] || { echo 'Usage: ops/restore.sh /absolute/path/to/backup /absolute/path/to/age-identity' >&2; exit 1; }
backup=$(realpath "$1")
identity=$(realpath "$2")
project=$(python3 -c 'import sys;sys.path.insert(0,"ops");from common import configuration;print(configuration()["COMPOSE_PROJECT_NAME"])')
[[ "$project" == *_restore_* ]] || { echo 'Refusing restore: use a separate checkout and a project name containing _restore_.' >&2; exit 1; }
if docker volume ls --filter "label=com.docker.compose.project=$project" --format '{{.Name}}' | grep -q .; then
  echo 'Refusing restore into existing project volumes. Choose a fresh restore project.' >&2; exit 1
fi
(cd "$backup"; sha256sum -c SHA256SUMS)
export MODE=dev
./ops/dc run --rm --no-deps volume-init
./ops/dc up -d --wait postgres redis
# The fresh database exists but migrations have NOT run. pg_restore supplies the schema.
database=$(python3 -c 'import sys;sys.path.insert(0,"ops");from common import configuration;print(configuration()["POSTGRES_DB"])')
age -d -i "$identity" "$backup/database.dump.age" | ./ops/dc exec -T --user 70:70 postgres pg_restore -U postgres -d "$database" --role=liberty_app --no-owner --no-acl --exit-on-error
age -d -i "$identity" "$backup/media.tar.gz.age" | ./ops/dc run --rm -T --no-deps web python ops/media_archive.py import --empty-only
./ops/dc run --rm web python manage.py check
./ops/dc run --rm web python manage.py verify_content
./ops/dc up -d web
./ops/dc exec -T web python ops/smoke.py
echo 'Isolated restore checks completed. Compare record counts, log in, inspect media, preview, and record recovery duration.'
