#!/usr/bin/env python3
"""Stage a core-first lock set in the pinned Debian builder, then publish it.

Old Python locks are never resolver constraints for a framework downgrade. An
unchanged npm lock is retained unless --refresh-frontend is explicitly requested.
"""
import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from common import ROOT, env_file
from lock_state import OUTPUTS, commit, input_fingerprint, resolution_lock, verify


def npm_lock_matches(manifest, lock):
    root = lock.get('packages', {}).get('')
    if lock.get('lockfileVersion', 0) < 2 or not isinstance(root, dict):
        return False
    for key in ('name', 'version', 'dependencies', 'devDependencies', 'optionalDependencies'):
        default = {} if key.endswith('Dependencies') or key == 'dependencies' else None
        if root.get(key, default) != manifest.get(key, default):
            return False
    return True


def stage_inputs(stage, refresh_frontend):
    for name in ('requirements/core.in', 'requirements/production.in', 'requirements/development.in',
                 'requirements/lock-tools.in', 'frontend/package.json', 'config/build-baseline.json',
                 'ops/python_contract.py', 'ops/check_runtime.py'):
        target = stage / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    existing = ROOT / 'frontend/package-lock.json'
    if existing.is_file() and not refresh_frontend:
        if existing.is_symlink():
            raise ValueError('Refusing a symlink npm lock.')
        manifest = json.loads((ROOT / 'frontend/package.json').read_text())
        if not npm_lock_matches(manifest, json.loads(existing.read_text())):
            raise ValueError('Existing npm lock differs from package.json. Review before using --refresh-frontend.')
        shutil.copy2(existing, stage / 'frontend/package-lock.json')
        return True
    return False


def python_script():
    return '''set -eu
python -m venv /tmp/lock-tools
/tmp/lock-tools/bin/python -m pip install --disable-pip-version-check -r requirements/lock-tools.in
/tmp/lock-tools/bin/python -m piptools compile --resolver=backtracking --generate-hashes --strip-extras --no-emit-index-url --no-emit-trusted-host --output-file=requirements/production.lock requirements/production.in
/tmp/lock-tools/bin/python -m piptools compile --resolver=backtracking --generate-hashes --strip-extras --no-emit-index-url --no-emit-trusted-host --output-file=requirements/development.lock requirements/development.in
python -m venv /tmp/core-check
/tmp/core-check/bin/python -m pip install --disable-pip-version-check --only-binary=:all: --require-hashes -r requirements/production.lock
/tmp/core-check/bin/python -m pip check
/tmp/core-check/bin/python ops/check_runtime.py
/tmp/lock-tools/bin/python -c 'import importlib.metadata as m, json, platform; from pathlib import Path; Path("requirements/resolver-tools.json").write_text(json.dumps({"python":platform.python_version(), "packages":{d.metadata["Name"]:d.version for d in m.distributions()}}, indent=2)+"\\n")'
'''


def resolve_candidates(stage, images, keep_frontend):
    mount = f'{stage}:/work:z'
    user = f'{os.getuid()}:{os.getgid()}'
    # Only the temporary input directory is writable in the resolver containers.
    # The project .env, secrets, media, and old reviewed locks are not mounted.
    subprocess.run([
        'docker', 'run', '--rm', '--user', user, '-e', 'HOME=/tmp',
        '--entrypoint', '/bin/sh', '-v', mount, '-w', '/work',
        images['PYTHON_BUILD_IMAGE'], '-ec', python_script(),
    ], check=True)
    if not keep_frontend:
        subprocess.run([
            'docker', 'run', '--rm', '--user', user, '-e', 'HOME=/tmp',
            '-e', 'npm_config_cache=/tmp/npm-cache', '-v', mount, '-w', '/work/frontend',
            images['NODE_IMAGE'], 'npm', 'install', '--package-lock-only', '--ignore-scripts', '--no-fund',
        ], check=True)
    manifest = json.loads((stage / 'frontend/package.json').read_text())
    if not npm_lock_matches(manifest, json.loads((stage / 'frontend/package-lock.json').read_text())):
        raise ValueError('Generated npm lock does not match the frontend manifest.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--missing-only', action='store_true', help='Verify an existing complete lock set, without replacing it.')
    parser.add_argument('--refresh-frontend', action='store_true', help='Explicitly re-resolve frontend dependencies too.')
    args = parser.parse_args()
    if args.missing_only and args.refresh_frontend:
        parser.error('--missing-only and --refresh-frontend cannot be combined')
    with resolution_lock():
        verify('images')
        images = env_file(ROOT / 'images.lock.env')
        expected = input_fingerprint('dependencies')
        if args.missing_only and any((ROOT / name).exists() for name in OUTPUTS['dependencies']):
            verify('dependencies')
            print('Existing reviewed dependency locks preserved.')
            return
        # Parent of the project is a bind-mountable host path, not a container-only /tmp.
        with tempfile.TemporaryDirectory(prefix='.liberty-lock-stage-', dir=ROOT.parent) as tmp:
            stage = Path(tmp)
            keep_frontend = stage_inputs(stage, args.refresh_frontend)
            resolve_candidates(stage, images, keep_frontend)
            payloads = {name: (stage / name).read_bytes() for name in OUTPUTS['dependencies']}
            commit('dependencies', payloads, details={
                'profile': 'core', 'frontend_lock_preserved': keep_frontend,
                'builder_image': images['PYTHON_BUILD_IMAGE'], 'runtime_image': images['PYTHON_IMAGE'],
                'production_binary_install_and_pip_check': 'passed in resolver builder',
                'final_runtime_not_yet_tested': True,
            }, expected_input=expected)
    print('Core locks published. Review the diff, audit, and build the actual final image before deployment.')


if __name__ == '__main__':
    main()
