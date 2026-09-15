#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v age >/dev/null || { echo 'Install age before taking encrypted backups.' >&2; exit 1; }
recipient=$(python3 -c 'import sys;sys.path.insert(0,"ops");from common import configuration;print(configuration().get("BACKUP_RECIPIENT",""))')
[[ "$recipient" == age1* ]] || { echo 'Set an age public recipient in .env. Keep its private identity off-host.' >&2; exit 1; }
umask 077
stamp=$(date -u +%Y%m%dT%H%M%SZ)
folder="backups/$stamp"
mkdir -p "$folder"
# This is a logical database backup. Stop publication/uploads during the DB+media window
# for a cross-resource-consistent snapshot. Do not stop PostgreSQL itself.
database=$(python3 -c 'import sys;sys.path.insert(0,"ops");from common import configuration;print(configuration()["POSTGRES_DB"])')
./ops/dc exec -T --user 70:70 postgres pg_dump -U postgres -d "$database" -Fc --no-owner --no-acl | age -r "$recipient" -o "$folder/database.dump.age"
./ops/dc exec -T web python ops/media_archive.py export | age -r "$recipient" -o "$folder/media.tar.gz.age"
# Recovery configuration and secret files are encrypted as well. Never commit the output.
tar -czf - .env images.lock.env images.lock.meta.json dependencies.lock.meta.json requirements/production.lock secrets runtime | age -r "$recipient" -o "$folder/config.tar.gz.age"
(cd "$folder"; sha256sum *.age > SHA256SUMS)
echo "Encrypted backup written to $folder. Copy it off-host and run a restore drill."
