#!/usr/bin/env python3
"""Resolve pinned image inputs; --refresh-python preserves unrelated image locks."""
import argparse
import json
import re
import subprocess

from common import ROOT, env_file
from lock_state import commit, digest, input_fingerprint, resolution_lock

PYTHON_KEYS = {'PYTHON_BUILD_IMAGE', 'PYTHON_IMAGE'}


def repository(reference):
    ref = reference.split('@', 1)[0]
    ref = ref.rsplit(':', 1)[0] if ':' in ref.rsplit('/', 1)[-1] else ref
    parts = ref.split('/')
    if len(parts) == 1:
        return 'docker.io/library/' + ref
    if '.' not in parts[0] and ':' not in parts[0] and parts[0] != 'localhost':
        return 'docker.io/' + ref
    return ref


def validate_digest(reference):
    if not re.fullmatch(r'[^\s]+@sha256:[a-f0-9]{64}', reference):
        raise ValueError('Expected an immutable registry digest reference.')


def prior_sources():
    meta = json.loads((ROOT / 'images.lock.meta.json').read_text())
    if meta.get('format') == 2:
        if digest((ROOT / 'images.lock.env').read_bytes()) != meta.get('outputs', {}).get('images.lock.env'):
            raise ValueError('Existing image lock output was edited.')
        sources = meta.get('details', {}).get('sources')
        if not isinstance(sources, dict):
            raise ValueError('Existing image lock has no source mapping.')
        return sources
    # Explicit legacy migration path for the shipped 0.3.1 inputs. Legacy
    # metadata did not hash outputs; those still require operator review.
    original = ROOT / 'source-import/baselines/0.3.1/images.sources.env'
    old_hash = digest(b'images.sources.env\0' + original.read_bytes() + b'\0')
    if meta.get('input_sha256') != old_hash:
        raise ValueError('Legacy lock inputs are not the supplied 0.3.1 baseline.')
    return env_file(original)


def retained_pins(sources):
    old_sources = prior_sources()
    old = env_file(ROOT / 'images.lock.env')
    kept = {}
    for key, source in sources.items():
        if key in PYTHON_KEYS:
            continue
        if old_sources.get(key) != source or key not in old:
            raise ValueError('Non-Python image input changed or is missing: ' + key)
        validate_digest(old[key])
        if repository(old[key]) != repository(source):
            raise ValueError('Existing image digest repository differs: ' + key)
        kept[key] = old[key]
    return kept


def resolve(source):
    if '@sha256:' in source:
        validate_digest(source)
    subprocess.run(['docker', 'pull', source], check=True)
    text = subprocess.check_output(
        ['docker', 'image', 'inspect', source, '--format', '{{range .RepoDigests}}{{println .}}{{end}}'],
        text=True,
    )
    for candidate in text.splitlines():
        candidate = candidate.strip()
        if '@sha256:' in candidate and repository(candidate) == repository(source):
            validate_digest(candidate)
            return candidate
    raise SystemExit('Registry returned no matching digest for ' + source)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh-python', action='store_true',
                        help='Use existing non-Python locks; resolve only the Debian Python pair.')
    args = parser.parse_args()
    with resolution_lock():
        sources = env_file(ROOT / 'images.sources.env')
        expected = input_fingerprint('images')
        if not PYTHON_KEYS <= set(sources):
            raise SystemExit('Both Python image inputs are required.')
        kept = retained_pins(sources) if args.refresh_python else {}
        pins = {}
        for key, source in sources.items():
            if key in kept:
                pins[key] = kept[key]
                print('Preserving ' + key, flush=True)
            else:
                print(f'Resolving {key}: {source}', flush=True)
                pins[key] = resolve(source)
        data = '# Resolved by ops/lock_images.py; review before release.\n'
        data += '\n'.join(f'{key}={value}' for key, value in pins.items()) + '\n'
        commit('images', {'images.lock.env': data.encode()},
               details={'sources': sources}, expected_input=expected)
    print('Image locks published. No application was built, started, or migrated.')


if __name__ == '__main__':
    main()
