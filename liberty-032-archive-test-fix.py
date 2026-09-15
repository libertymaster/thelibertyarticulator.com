#!/usr/bin/env python3
"""Correct the archive empty-state assertion in the 0.3.2 frontend test.

Dry-run by default. Only one test assertion is changed. No Docker commands,
package installation, lock changes, or database operations are performed.
"""
import argparse
import difflib
import os
from pathlib import Path
import stat
import sys
import tempfile

TEST = Path('frontend/tests/islands.test.tsx')
COMPONENT = Path('frontend/src/components/ResearchArchive.tsx')
MESSAGE = b'No public records match these filters. Try a broader search.'
OLD = (b"expect(screen.getByText('No articles match these filters. Try a broader "
       b"search.')).toBeInTheDocument();")
NEW = (b"expect(await screen.findByText('No public records match these filters. "
       b"Try a broader search.')).toBeInTheDocument();")
TEST_NAME = b"it('uses a bounded same-origin endpoint and updates the URL', async () => {"


def checked_path(root: Path, relative: Path) -> Path:
    path = root
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('Refusing a symlink: ' + str(path))
    return path


def repair(root: Path, apply: bool) -> None:
    root = root.expanduser().resolve(strict=True)
    target = checked_path(root, TEST)
    component = checked_path(root, COMPONENT)
    if not target.is_file() or not component.is_file():
        raise ValueError('Expected archive component and test were not found in this project.')
    source = target.read_bytes()
    component_source = component.read_bytes()
    if MESSAGE not in component_source:
        raise ValueError('The component no longer contains the expected message. Review manually.')
    if NEW in source and OLD not in source:
        print('Already corrected. No files changed.')
        return
    if source.count(OLD) != 1 or NEW in source or source.count(TEST_NAME) != 1:
        raise ValueError('Expected original async test assertion is missing or ambiguous. No files changed.')
    updated = source.replace(OLD, NEW, 1)
    print(''.join(difflib.unified_diff(
        source.decode('utf-8').splitlines(keepends=True),
        updated.decode('utf-8').splitlines(keepends=True),
        fromfile=str(TEST), tofile=str(TEST) + ' (corrected)',
    )), end='')
    if not apply:
        print('Dry run only. Run again with --apply to save the correction.')
        return
    mode = stat.S_IMODE(target.stat().st_mode)
    parent = checked_path(root, Path('runtime/patch-backups'))
    parent.mkdir(parents=True, exist_ok=True)
    if target.read_bytes() != source or component.read_bytes() != component_source:
        raise ValueError('Source changed during inspection. No source files changed.')
    backup_dir = Path(tempfile.mkdtemp(prefix='archive-test-', dir=parent))
    backup = backup_dir / 'islands.test.tsx'
    with backup.open('xb') as handle:
        handle.write(source)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(backup, mode)
    fd, temporary_name = tempfile.mkstemp(prefix='.archive-test-', dir=target.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(updated)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        checked_path(root, TEST)
        if target.read_bytes() != source:
            raise ValueError('Test changed before replacement. Source was not overwritten.')
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    print('Changed only: ' + str(TEST))
    print('Original backup: ' + str(backup))
    print('Locks, secrets, application code, and the Docker test gate are unchanged.')
    print('Next: MODE=dev python3 ops/validate_app.py --build')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--apply', action='store_true', help='Apply after creating an original-file backup.')
    args = parser.parse_args()
    try:
        repair(args.project, args.apply)
    except (OSError, ValueError, UnicodeError) as exc:
        print('Repair stopped: ' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
