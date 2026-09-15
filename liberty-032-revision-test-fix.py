#!/usr/bin/env python3
"""Repair the 0.3.2 founding-import regression test without changing the importer.

Dry-run by default. Checks the original method, backs up the test, then replaces
only that method. No Docker, database, package, configuration, or lock operations.
Use --rollback BACKUP --apply to restore a backup if the test is still unchanged
since this repair. Requires Python 3.10 or newer and only the standard library.
"""
import argparse
import ast
import difflib
import os
from pathlib import Path
import stat
import sys
import tempfile

TARGET = Path('tests/django_tests/test_founding_import.py')
METHOD_NAME = 'test_import_will_not_overwrite_editor_changes'
OLD = "    def test_import_will_not_overwrite_editor_changes(self):\n        self.run_import(apply=True, publish=True)\n        page = ArticlePage.objects.get(slug='the-archive-is-not-the-village')\n        draft = page.get_latest_revision_as_object()\n        draft.title = 'An editor changed this draft'\n        revision = draft.save_revision()\n        self.run_import(apply=True, publish=True)\n        page.refresh_from_db()\n        self.assertEqual(page.latest_revision_id, revision.pk)\n        self.assertNotEqual(page.title, draft.title)\n"
NEW = "    def test_import_will_not_overwrite_editor_changes(self):\n        self.run_import(apply=True, publish=True)\n        page = ArticlePage.objects.get(slug='the-archive-is-not-the-village')\n        published_title = page.title\n        published_revision_id = page.live_revision_id\n        expected_draft_title = 'An editor changed this draft'\n\n        # Wagtail may return the same Page instance when no draft changes exist.\n        # Keep expected values independent of that instance and its later refresh.\n        draft = page.get_latest_revision_as_object()\n        draft.title = expected_draft_title\n        revision = draft.save_revision()\n        revision.refresh_from_db()\n        self.assertEqual(revision.content['title'], expected_draft_title)\n\n        self.run_import(apply=True, publish=True)\n        page.refresh_from_db()\n        revision.refresh_from_db()\n\n        # Verify persisted draft content, not a mutable in-memory alias of page.\n        self.assertEqual(page.latest_revision_id, revision.pk)\n        self.assertEqual(page.live_revision_id, published_revision_id)\n        self.assertEqual(page.title, published_title)\n        self.assertTrue(page.live)\n        self.assertTrue(page.has_unpublished_changes)\n        self.assertEqual(page.draft_title, expected_draft_title)\n        self.assertEqual(revision.content['title'], expected_draft_title)\n        self.assertEqual(\n            page.get_latest_revision_as_object().title, expected_draft_title\n        )\n"


def checked_path(root: Path, relative: Path) -> Path:
    path = root
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('Refusing a symlink: ' + str(path))
    return path


def transformed(source: bytes) -> tuple[bytes, bool]:
    text = source.decode('utf-8')
    tree = ast.parse(text)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == 'FoundingImportTests']
    if len(classes) != 1:
        raise ValueError('Expected one FoundingImportTests class. No source changed.')
    methods = [n for n in classes[0].body if isinstance(n, ast.FunctionDef)
               and n.name == METHOD_NAME]
    if len(methods) != 1:
        raise ValueError('Target test is missing or duplicated. No source changed.')
    newline = '\r\n' if '\r\n' in text else '\n'
    old, new = OLD.replace('\n', newline), NEW.replace('\n', newline)
    method = methods[0]
    lines = text.splitlines(keepends=True)
    block = ''.join(lines[method.lineno - 1:method.end_lineno])
    if block == new:
        return source, True
    if block != old or text.count(old) != 1:
        raise ValueError('The target method differs from the original 0.3.2 test. '
                         'Review local changes manually; nothing was overwritten.')
    updated = text.replace(old, new, 1)
    ast.parse(updated)
    return updated.encode('utf-8'), False


def repair(root: Path, apply: bool, rollback: Path | None = None) -> None:
    root = root.expanduser().resolve(strict=True)
    target = checked_path(root, TARGET)
    if not target.is_file():
        raise ValueError('Expected test not found: ' + str(target))
    source = target.read_bytes()
    if rollback is not None:
        backup_path = rollback.expanduser().absolute()
        for path in [backup_path, *backup_path.parents]:
            if path.is_symlink():
                raise ValueError('Refusing a symlink in rollback path.')
        if not backup_path.is_file():
            raise ValueError('Rollback backup is not a regular file.')
        restored = backup_path.read_bytes()
        expected, already = transformed(restored)
        if already:
            raise ValueError('Rollback input is not an original pre-repair backup.')
        if source == restored:
            print('Already restored. No files changed.')
            return
        if source != expected:
            raise ValueError('Current test differs from the repaired backup. '
                             'Refusing to overwrite later edits.')
        updated = restored
    else:
        updated, already = transformed(source)
        if already:
            print('Already corrected. No files changed.')
            return
    print(''.join(difflib.unified_diff(
        source.decode('utf-8').splitlines(keepends=True),
        updated.decode('utf-8').splitlines(keepends=True),
        fromfile=str(TARGET), tofile=str(TARGET) + ' (proposed)',
    )), end='')
    if not apply:
        print('Dry run only. Run again with --apply to save these changes.')
        return
    mode = stat.S_IMODE(target.stat().st_mode)
    parent = checked_path(root, Path('runtime/patch-backups'))
    parent.mkdir(parents=True, exist_ok=True)
    checked_path(root, TARGET)
    if target.read_bytes() != source:
        raise ValueError('Test changed during inspection. No source was overwritten.')
    backup_dir = Path(tempfile.mkdtemp(prefix='revision-test-', dir=parent))
    backup = backup_dir / TARGET.name
    with backup.open('xb') as handle:
        handle.write(source)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(backup, mode)
    fd, temporary_name = tempfile.mkstemp(prefix='.revision-test-', dir=target.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(updated)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        checked_path(root, TARGET)
        if target.read_bytes() != source:
            raise ValueError('Test changed before replacement. No source was overwritten.')
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    print('Changed only: ' + str(TARGET))
    print('Original backup: ' + str(backup))
    print('Application/importer code, secrets, locks, and existing repairs are unchanged.')
    print('Next: MODE=dev python3 ops/validate_app.py --build')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--rollback', type=Path, metavar='BACKUP',
                        help='Restore a backup only if there have been no later edits.')
    args = parser.parse_args()
    try:
        repair(args.project, args.apply, args.rollback)
    except (OSError, ValueError, UnicodeError, SyntaxError) as exc:
        print('Repair stopped: ' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
