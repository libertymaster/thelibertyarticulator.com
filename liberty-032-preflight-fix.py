#!/usr/bin/env python3
"""Repair two preflight defects in Liberty Articulator 0.3.2; dry run by default.

Changes only ops/check_image_contracts.py. Does not invoke Docker, change locks,
read secrets, edit Compose, or start/migrate services. Backups are made beside
that file and can be restored with cp -p after reviewing subsequent changes.
"""
import argparse
import ast
import difflib
import os
from pathlib import Path
import shutil
import stat
import tempfile

REPLACEMENTS = (
    (
        "def run(image, binary, args):\n"
        "    return subprocess.check_output(['docker', 'run', '--rm', '--network', 'none', '--entrypoint', binary, image, *args], text=True, timeout=120).strip()",
        "def run(image, binary, args):\n"
        "    command = ['docker', 'run', '--rm', '--network', 'none']\n"
        "    # None preserves the image's entrypoint, as the Compose service does.\n"
        "    if binary is not None:\n"
        "        command += ['--entrypoint', binary]\n"
        "    command += [image, *args]\n"
        "    return subprocess.check_output(command, text=True, timeout=120).strip()",
    ),
    (
        "        'REDIS_EXPORTER_IMAGE': [('redis_exporter', ['--version'])],",
        "        'REDIS_EXPORTER_IMAGE': [(None, ['--version'])],",
    ),
    (
        "        for binary, args in commands:\n"
        "            print(f'Checking {key}: {binary}', flush=True)\n"
        "            results[key][binary] = run(images[key], binary, args)",
        "        for binary, command_args in commands:\n"
        "            label = binary or 'image-entrypoint'\n"
        "            print(f'Checking {key}: {label}', flush=True)\n"
        "            results[key][label] = run(images[key], binary, command_args)",
    ),
)


def corrected(source):
    result = source
    for number, (old, new) in enumerate(REPLACEMENTS, 1):
        if result.count(old) == 1 and new not in result:
            result = result.replace(old, new, 1)
        elif old not in result and result.count(new) == 1:
            continue
        else:
            raise ValueError(
                f'Patch section {number} does not match the original or repaired file. '
                'Nothing written; review local edits instead of forcing the patch.'
            )
    ast.parse(result, filename='ops/check_image_contracts.py')
    return result


def apply_patch(project, apply=False):
    project = Path(project).expanduser().resolve(strict=True)
    ops = project / 'ops'
    target = ops / 'check_image_contracts.py'
    if ops.is_symlink() or target.is_symlink() or not target.is_file():
        raise ValueError('Expected a regular ops/check_image_contracts.py; refusing missing files or symlinks.')
    original = target.read_bytes()
    updated = corrected(original.decode('utf-8')).encode('utf-8')
    if original == updated:
        print('Already repaired. No files changed.')
        return None
    print(''.join(difflib.unified_diff(
        original.decode().splitlines(keepends=True),
        updated.decode().splitlines(keepends=True),
        fromfile='a/ops/check_image_contracts.py',
        tofile='b/ops/check_image_contracts.py',
    )), end='')
    if not apply:
        print('Dry run only. Add --apply to make this change and create a backup.')
        return None
    mode = stat.S_IMODE(target.stat().st_mode)
    fd, backup_name = tempfile.mkstemp(prefix='check_image_contracts.py.before-redis-fix-', suffix='.bak', dir=ops)
    os.close(fd)
    backup = Path(backup_name)
    # copy2 retains mode/timestamps. Recheck bytes before replacing the target.
    shutil.copy2(target, backup)
    temporary = None
    try:
        fd, temporary_name = tempfile.mkstemp(prefix='.check_image_contracts-', dir=ops)
        temporary = Path(temporary_name)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(mode)
        if target.is_symlink() or target.read_bytes() != original or backup.read_bytes() != original:
            raise ValueError('Source changed while preparing the patch. Target was not replaced.')
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f'Repaired: {target}')
    print(f'Backup:   {backup}')
    print('No Docker commands were run. Image/dependency locks, .env, secrets, and Compose were not changed.')
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', default='.', help='Existing 0.3.2 project directory (default: current directory).')
    parser.add_argument('--apply', action='store_true', help='Apply the reviewed change; otherwise only display the diff.')
    args = parser.parse_args()
    try:
        apply_patch(args.project, args.apply)
    except (OSError, UnicodeError, ValueError, SyntaxError) as exc:
        parser.exit(1, f'Repair stopped: {exc}\n')


if __name__ == '__main__':
    main()
