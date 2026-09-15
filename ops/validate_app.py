#!/usr/bin/env python3
"""Build optionally, then test the final app image without deployment secrets or networks."""
import argparse
from datetime import datetime, timezone
import json
import subprocess
from common import ROOT, compose, configuration
from lock_state import verify


def container_command(image, args):
    return ['docker', 'run', '--rm', '--network', 'none', '--read-only',
            '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true',
            '--user', '10001:10001', '--memory', '1536m', '--cpus', '2',
            '--tmpfs', '/tmp:size=128m,mode=1777',
            '--tmpfs', '/app/.test-media:size=64m,uid=10001,gid=10001,mode=0700',
            '-e', 'DJANGO_SETTINGS_MODULE=config.settings.testing',
            '--entrypoint', '/venv/bin/python', image, *args]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true')
    args = parser.parse_args()
    verify('images'); verify('dependencies')
    image = configuration().get('APP_IMAGE', 'the_liberty_articulator:0.3.2-debian')
    if args.build:
        compose('build', 'web')
    image_id = subprocess.check_output(['docker', 'image', 'inspect', image, '--format', '{{.Id}}'], text=True).strip()
    if not image_id.startswith('sha256:'):
        raise SystemExit('No local immutable image ID found after the build.')
    checks = [
        ['ops/check_runtime.py', '--compare', '/app/build-runtime-contract.json', '--require-runtime-user'],
        ['manage.py', 'check'],
        ['manage.py', 'makemigrations', '--check', '--dry-run'],
        ['manage.py', 'test', 'tests.django_tests', '--verbosity=2'],
    ]
    for check in checks:
        print('Final-image check: ' + ' '.join(check), flush=True)
        subprocess.run(container_command(image_id, check), check=True)
    runtime = ROOT / 'runtime'; runtime.mkdir(exist_ok=True)
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'app_image': image,
              'image_id': image_id, 'checks': checks, 'database': 'ephemeral SQLite only',
              'network': 'none', 'deployment_secrets_mounted': False,
              'postgres_redis_cloudflare_not_tested': True}
    (runtime / 'app-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Final-image checks passed without production data. PostgreSQL/Redis/editor-browser '
          'and ingress acceptance checks remain separate.')


if __name__ == '__main__':
    main()
