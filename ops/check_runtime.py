#!/usr/bin/env python3
"""Validate the exact Python/framework baseline and active native dependencies.

No database connection, settings import, shell, package installer, or secret access.
"""
import argparse
import importlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
from python_contract import compare_contracts, probe, validate_contract

ROOT = Path(__file__).resolve().parents[1]


def inspect_runtime():
    expected = json.loads((ROOT / 'config/build-baseline.json').read_text())
    contract = probe()
    validate_contract(contract, expected)
    versions = {name: importlib.metadata.version(name) for name in expected['packages']}
    if versions != expected['packages']:
        raise ValueError('Framework versions differ from the approved build baseline: ' + str(versions))
    for name in ('django', 'wagtail', 'psycopg', 'PIL._imaging', 'pydantic_core',
                 'cryptography.hazmat.bindings._rust', 'brotli', 'ssl', 'sqlite3'):
        importlib.import_module(name)
    from PIL import Image
    import psycopg.pq
    if psycopg.pq.__impl__ != 'binary':
        raise ValueError('Expected the locked psycopg[binary] implementation.')
    image_formats = {}
    for kind in ('PNG', 'JPEG', 'WEBP'):
        stream = io.BytesIO()
        Image.new('RGB', (2, 2)).save(stream, format=kind)
        stream.seek(0)
        with Image.open(stream) as image:
            image.load()
            if image.size != (2, 2):
                raise ValueError('Image codec round-trip failed: ' + kind)
        image_formats[kind] = True
    return {'python': contract, 'packages': versions, 'image_codecs': image_formats,
            'psycopg_implementation': psycopg.pq.__impl__, 'uid': os.getuid()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', type=Path)
    parser.add_argument('--compare', type=Path)
    parser.add_argument('--require-runtime-user', action='store_true')
    args = parser.parse_args()
    report = inspect_runtime()
    if args.compare:
        prior = json.loads(args.compare.read_text())
        compare_contracts(prior['python'], report['python'])
        if prior['packages'] != report['packages']:
            raise ValueError('Builder and runtime framework packages differ.')
    if args.require_runtime_user:
        expected = json.loads((ROOT / 'config/build-baseline.json').read_text())
        if report['uid'] != expected['runtime_uid']:
            raise ValueError('Final image is not running under the approved non-root UID.')
    if args.write:
        args.write.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    print('Python/framework/native runtime checks passed; no service or database was contacted.')


if __name__ == '__main__':
    main()
