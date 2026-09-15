#!/usr/bin/env python3
"""Enable Django's bundled PostgreSQL app in Liberty Articulator 0.3.2.

Dry run by default. Changes only config/settings/base.py. Does not invoke Docker,
install packages, regenerate locks, read secret files, or modify database data.
"""
import argparse
import ast
import difflib
import hashlib
import os
from pathlib import Path
import stat
import tempfile

RELATIVE = Path('config/settings/base.py')
APP = 'django.contrib.postgres'
APP_CONFIG = 'django.contrib.postgres.apps.PostgresConfig'
ANCHOR = '    "django.contrib.staticfiles", "django.contrib.sitemaps",'


def corrected(source):
    """Inspect literal settings without importing or executing the project."""
    tree = ast.parse(source, filename=str(RELATIVE))
    writes = [n for n in ast.walk(tree) if isinstance(n, ast.Name)
              and n.id == 'INSTALLED_APPS' and isinstance(n.ctx, ast.Store)]
    assignments = [n for n in tree.body if isinstance(n, ast.Assign)
                   and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                   and n.targets[0].id == 'INSTALLED_APPS']
    if len(writes) != 1 or len(assignments) != 1:
        raise ValueError('Expected one direct INSTALLED_APPS assignment. Review customized settings; nothing written.')
    value = assignments[0].value
    if not isinstance(value, ast.List):
        raise ValueError('Expected a literal INSTALLED_APPS list; nothing written.')
    apps = ast.literal_eval(value)
    if not all(isinstance(item, str) for item in apps) or 'wagtail.search' not in apps:
        raise ValueError('Expected Wagtail search in a literal string app list; nothing written.')
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == 'INSTALLED_APPS'):
            raise ValueError('INSTALLED_APPS is modified by a method call. Review manually; nothing written.')
    matches = sum(name in (APP, APP_CONFIG) for name in apps)
    if matches > 1:
        raise ValueError('Duplicate PostgreSQL app registrations. Review manually; nothing written.')
    if matches == 1:
        return source
    lines = source.splitlines(keepends=True)
    indexes = [i for i in range(value.lineno - 1, value.end_lineno)
               if lines[i].rstrip('\r\n') == ANCHOR]
    if len(indexes) != 1:
        raise ValueError('The insertion point differs from the supplied bundle. Review manually; nothing written.')
    index = indexes[0]
    newline = '\r\n' if lines[index].endswith('\r\n') else '\n'
    lines.insert(index + 1, f'    "{APP}",{newline}')
    result = ''.join(lines)
    # Confirm the transformation is syntactically valid and is idempotent.
    if corrected(result) != result:
        raise ValueError('Post-patch verification failed; nothing written.')
    return result


def project_target(project):
    root = Path(project).expanduser().resolve(strict=True)
    for path in (root / 'config', root / 'config/settings', root / RELATIVE):
        if path.is_symlink():
            raise ValueError('Refusing a symlink under config/settings.')
    target = root / RELATIVE
    if not target.is_file():
        raise ValueError('Missing config/settings/base.py. Run from the project or set --project.')
    return root, target


def replace_checked(target, expected, replacement):
    mode = stat.S_IMODE(target.stat().st_mode)
    fd, name = tempfile.mkstemp(prefix='.base.py-postgres-', dir=target.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(replacement)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(mode)
        if target.is_symlink() or target.read_bytes() != expected:
            raise ValueError('Settings changed during patch preparation. Target was not replaced.')
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def apply_patch(project, apply=False):
    root, target = project_target(project)
    original = target.read_bytes()
    updated = corrected(original.decode('utf-8')).encode('utf-8')
    if original == updated:
        print('PostgreSQL app is already registered. No files changed.')
        return None
    print(''.join(difflib.unified_diff(
        original.decode().splitlines(keepends=True), updated.decode().splitlines(keepends=True),
        fromfile='a/' + str(RELATIVE), tofile='b/' + str(RELATIVE),
    )), end='')
    if not apply:
        print('Dry run only. Use --apply to save the correction with a backup.')
        return None
    backup_parent = root / 'runtime/patch-backups'
    for path in (root / 'runtime', backup_parent):
        if path.is_symlink():
            raise ValueError('Refusing a symlink backup directory.')
    backup_parent.mkdir(parents=True, exist_ok=True)
    backup_dir = Path(tempfile.mkdtemp(prefix='postgres-settings-', dir=backup_parent))
    backup = backup_dir / 'base.py'
    backup.write_bytes(original)
    backup.chmod(0o600)
    (backup_dir / 'after.sha256').write_text(hashlib.sha256(updated).hexdigest() + '\n')
    replace_checked(target, original, updated)
    print(f'Repaired: {target}')
    print(f'Backup directory: {backup_dir}')
    print('No Docker commands were run. Keep the current .env, secrets, locks, and volumes.')
    return backup_dir


def rollback(project, directory, apply=False):
    root, target = project_target(project)
    path = Path(directory).expanduser().absolute()
    allowed = root / 'runtime/patch-backups'
    if '..' in path.parts:
        raise ValueError('Use the exact backup directory without parent traversal.')
    try:
        path.relative_to(allowed)
    except ValueError as exc:
        raise ValueError('Use the backup directory printed for this project.') from exc
    for part in [path, *path.parents]:
        if part == root:
            break
        if part.is_symlink():
            raise ValueError('Refusing a symlink backup path.')
    backup = path / 'base.py'
    after_hash = path / 'after.sha256'
    if backup.is_symlink() or after_hash.is_symlink():
        raise ValueError('Refusing symlink backup files.')
    original = backup.read_bytes()
    repaired = corrected(original.decode('utf-8')).encode('utf-8')
    if hashlib.sha256(repaired).hexdigest() != after_hash.read_text().strip():
        raise ValueError('Backup verification failed; nothing written.')
    current = target.read_bytes()
    if current == original:
        print('Source already matches the backup. No files changed.')
        return
    if current != repaired:
        raise ValueError('Settings have changed since this patch. Refusing to overwrite later edits.')
    if not apply:
        print('Rollback dry run: restore only config/settings/base.py. Add --apply to proceed.')
        return
    replace_checked(target, current, original)
    print('Source restored. No containers, images, or databases were changed.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', default='.', help='Existing project directory.')
    parser.add_argument('--apply', action='store_true', help='Apply after reviewing the dry run.')
    parser.add_argument('--rollback', metavar='BACKUP_DIRECTORY', help='Restore this patch only; refuses later edits.')
    args = parser.parse_args()
    try:
        if args.rollback:
            rollback(args.project, args.rollback, args.apply)
        else:
            apply_patch(args.project, args.apply)
    except (OSError, UnicodeError, ValueError, SyntaxError) as exc:
        parser.exit(1, f'Repair stopped: {exc}\n')


if __name__ == '__main__':
    main()
