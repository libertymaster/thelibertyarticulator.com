#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
command -v docker >/dev/null || { echo 'Docker Engine and Compose v2 are required.' >&2; exit 1; }
docker compose version >/dev/null
command -v python3 >/dev/null
[ -f .env ] || cp .env.example .env
chmod 600 .env
python3 ops/init_secrets.py
python3 ops/render_config.py
if [ -f images.lock.env ]; then
  python3 -c 'import sys; sys.path.insert(0,"ops"); from lock_state import verify; verify("images")'
else
  python3 ops/lock_images.py
fi
python3 ops/check_image_contracts.py
python3 ops/lock_dependencies.py --missing-only
./ops/dc config --quiet
echo 'Preparation complete. Existing locks and secrets were preserved. No site was deployed.'
