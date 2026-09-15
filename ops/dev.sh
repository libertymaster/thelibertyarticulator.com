#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
export MODE=dev
python3 ops/preflight.py
./ops/dc config --quiet
python3 ops/validate_app.py --build
./ops/dc run --rm --no-deps volume-init

./ops/dc up -d --wait postgres redis

./ops/bootstrap_postgres.sh

./ops/dc run --rm migrate

./ops/dc run --rm web python manage.py bootstrap_site
if [ "${1:-}" = '--demo' ]; then
  ./ops/dc run --rm web python manage.py seed_demo --publish-demo
fi
./ops/dc up -d web worker beat traefik
echo 'Local publication: http://localhost:8080/ ; editor: http://localhost:8080/admin/'
echo 'Create your editor account with MODE=dev ./ops/dc exec web python manage.py createsuperuser.'
