"""Standard-library-only Python/OS contract shared by image and runtime checks."""
import json
import os
import platform
import sys
import sysconfig
from pathlib import Path

CONTRACT_KEYS = (
    'version', 'implementation', 'SOABI', 'MULTIARCH', 'machine', 'byteorder',
    'base_prefix', 'base_executable', 'os_id', 'os_version', 'libc',
)


def probe():
    release = {}
    path = Path('/etc/os-release')
    if path.is_file():
        for line in path.read_text().splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                release[key] = value.strip('"')
    try:
        libc = os.confstr('CS_GNU_LIBC_VERSION') or ''
    except (ValueError, OSError):
        libc = ''
    if not libc:
        libc = ' '.join(platform.libc_ver()).strip() or 'unknown'
    return {
        'version': list(sys.version_info[:3]),
        'implementation': sys.implementation.name,
        'SOABI': sysconfig.get_config_var('SOABI'),
        'MULTIARCH': sysconfig.get_config_var('MULTIARCH'),
        'machine': platform.machine(), 'byteorder': sys.byteorder,
        'base_prefix': os.path.realpath(sys.base_prefix),
        'base_executable': os.path.realpath(getattr(sys, '_base_executable', sys.executable)),
        'os_id': release.get('ID', ''), 'os_version': release.get('VERSION_ID', ''),
        'libc': libc,
    }


def validate_contract(value, expected):
    required = {
        'version': expected['python'], 'implementation': expected['implementation'],
        'os_id': expected['os_id'], 'os_version': expected['os_version'],
    }
    wrong = [key for key, target in required.items() if value.get(key) != target]
    if not value.get('libc', '').startswith(expected['libc_family'] + ' '):
        wrong.append('libc')
    if not value.get('SOABI') or not value.get('machine') or not value.get('base_executable'):
        wrong.append('interpreter ABI/path')
    if wrong:
        raise ValueError('Python image does not meet config/build-baseline.json: ' + ', '.join(wrong))


def compare_contracts(builder, runtime):
    wrong = [key for key in CONTRACT_KEYS if builder.get(key) != runtime.get(key)]
    if wrong:
        raise ValueError('Python builder/runtime mismatch: ' + ', '.join(wrong))


if __name__ == '__main__':
    print(json.dumps(probe(), sort_keys=True))
