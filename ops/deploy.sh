#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

export MODE=prod

echo '==> Checking configuration renderer'
python3 -m py_compile ops/render_config.py

echo '==> Rendering production runtime configuration'
python3 ops/render_config.py

echo '==> Validating generated Traefik configuration'
python3 -m json.tool runtime/traefik-dynamic.yml >/dev/null

echo '==> Running production preflight'
python3 ops/preflight.py

echo '==> Validating production Compose configuration'
./ops/dc config --quiet

echo '==> Validating and building application image'
python3 ops/validate_app.py --build

echo '==> Initializing persistent volumes'
./ops/dc run --rm --no-deps volume-init

echo '==> Starting PostgreSQL and Redis'
./ops/dc up -d --wait postgres redis

echo '==> Bootstrapping PostgreSQL roles and permissions'
./ops/bootstrap_postgres.sh

echo '==> Running Django migrations'
./ops/dc run --rm migrate

echo '==> Bootstrapping site configuration'
./ops/dc run --rm web python manage.py bootstrap_site

echo '==> Running Django production deployment checks'
./ops/dc run --rm web \
  python manage.py check --deploy --fail-level WARNING

echo '==> Starting application and reverse proxy'
./ops/dc up -d --wait web worker beat traefik

echo '==> Verifying application content'
./ops/dc exec -T web python manage.py verify_content

echo '==> Running internal smoke tests'
./ops/dc exec -T web python ops/smoke.py

echo '==> Starting Cloudflare Tunnel'
./ops/dc --profile tunnel up -d cloudflared

echo '==> Final service state'
./ops/dc ps

echo
echo 'Production startup and internal checks completed.'
echo 'Finish external, editor, backup/restore, monitoring, alerting, and load gates in docs/VALIDATION.md.'
