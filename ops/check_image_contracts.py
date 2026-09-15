#!/usr/bin/env python3
"""Run explicit, credential-free image capability checks on the target Docker host."""
import io
import json
import subprocess
import tarfile
from common import ROOT, env_file
from lock_state import verify
from python_contract import compare_contracts, validate_contract

def run(image, binary, args):
    command = ['docker', 'run', '--rm', '--network', 'none']
    # None preserves the image's entrypoint, as the Compose service does.
    if binary is not None:
        command += ['--entrypoint', binary]
    command += [image, *args]
    return subprocess.check_output(command, text=True, timeout=120).strip()

def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python-only", action="store_true", help="Check the app build pair without probing monitoring/identity images.")
    args = parser.parse_args()
    verify('images')
    images = env_file(ROOT / 'images.lock.env')
    results = {}
    checks = {
        'POSTGRES_IMAGE': [('postgres', ['--version']), ('psql', ['--version']), ('pg_dump', ['--version']), ('pg_restore', ['--version']), ('pg_isready', ['--version'])],
        'REDIS_IMAGE': [('redis-server', ['--version']), ('redis-cli', ['--version'])],
        'TRAEFIK_IMAGE': [('traefik', ['version'])],
        'PROMETHEUS_IMAGE': [('prometheus', ['--version']), ('promtool', ['--version'])],
        'ALERTMANAGER_IMAGE': [('alertmanager', ['--version']), ('amtool', ['--version'])],
        'ALLOY_IMAGE': [('alloy', ['--version'])],
        'LOKI_IMAGE': [('loki', ['-version'])],
        'NODE_EXPORTER_IMAGE': [('node_exporter', ['--version'])],
        'POSTGRES_EXPORTER_IMAGE': [('postgres_exporter', ['--version'])],
        'REDIS_EXPORTER_IMAGE': [(None, ['--version'])],
        'BLACKBOX_IMAGE': [('blackbox_exporter', ['--version'])],
        'KEYCLOAK_IMAGE': [('/bin/bash', ['--version']), ('/opt/keycloak/bin/kc.sh', ['--version'])],
    }
    for key, commands in ({} if args.python_only else checks).items():
        results[key] = {}
        for binary, command_args in commands:
            label = binary or 'image-entrypoint'
            print(f'Checking {key}: {label}', flush=True)
            results[key][label] = run(images[key], binary, command_args)
    probe = (ROOT / 'ops/python_contract.py').read_text()
    build = json.loads(run(images['PYTHON_BUILD_IMAGE'], 'python', ['-c', probe]))
    runtime = json.loads(run(images['PYTHON_IMAGE'], 'python', ['-c', probe]))
    baseline = json.loads((ROOT / 'config/build-baseline.json').read_text())
    validate_contract(build, baseline)
    validate_contract(runtime, baseline)
    compare_contracts(build, runtime)
    results['python_builder'] = build
    results['python_runtime'] = runtime
    (ROOT / 'runtime').mkdir(exist_ok=True)
    if args.python_only:
        (ROOT / 'runtime/python-image-contracts.json').write_text(json.dumps(results, indent=2) + '\n')
        print('Matching Debian/Python interpreter contracts passed. Final native imports run during docker build.')
        return
    # Read passwd from a stopped container rather than assuming it has id/cat/a shell.
    cid = subprocess.check_output(['docker', 'create', images['POSTGRES_IMAGE']], text=True).strip()
    try:
        raw = subprocess.check_output(['docker', 'cp', cid + ':/etc/passwd', '-'])
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            member = next(m for m in archive.getmembers() if m.isfile())
            text = archive.extractfile(member).read().decode()
        row = next(line.split(':') for line in text.splitlines() if line.startswith('postgres:'))
        if row[2:4] != ['70', '70']:
            raise SystemExit('PostgreSQL image UID/GID differs from the reviewed 70:70 volume ownership. Update both together before deployment.')
    finally:
        subprocess.run(['docker', 'rm', cid], check=True, stdout=subprocess.DEVNULL)
    info = json.loads(subprocess.check_output(['docker', 'image', 'inspect', images['POSTGRES_IMAGE']], text=True))[0]
    if 'PGDATA=/var/lib/postgresql/18/data' not in info['Config'].get('Env', []):
        raise SystemExit('Unexpected PostgreSQL PGDATA contract. Do not reuse volumes; review image documentation.')
    (ROOT / 'runtime').mkdir(exist_ok=True)
    (ROOT / 'runtime/image-contract-checks.json').write_text(json.dumps(results, indent=2) + '\n')
    print('Image command/ABI/UID checks passed. Service startup and persistence still require integration tests.')

if __name__ == '__main__':
    main()
