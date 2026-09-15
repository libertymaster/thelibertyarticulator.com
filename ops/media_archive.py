"""Stream media backups without requiring tar or a shell in the application image."""
import argparse
import shutil
import sys
import tarfile
from pathlib import Path, PurePosixPath

ROOT = Path('/app/media')

def unpack(stream, root, limit=100 * 1024 ** 3):
    root = root.resolve()
    if any(root.iterdir()):
        raise ValueError('Refusing to restore into nonempty media storage.')
    total = 0
    count = 0
    with tarfile.open(fileobj=stream, mode='r|gz') as archive:
        for member in archive:
            count += 1
            name = PurePosixPath(member.name)
            if name.is_absolute() or '..' in name.parts or '\\' in member.name:
                raise ValueError('Unsafe media path in backup.')
            if not (member.isdir() or member.isfile()):
                raise ValueError('Links, devices, and special files are not accepted in media backups.')
            target = root.joinpath(*name.parts).resolve()
            if not target.is_relative_to(root):
                raise ValueError('Media path escapes the restore directory.')
            total += member.size
            if total > limit or count > 1000000:
                raise ValueError('Restore exceeds the configured byte or file limit.')
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True, mode=0o750)
            else:
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o750)
                with archive.extractfile(member) as src, target.open('xb') as dst:
                    shutil.copyfileobj(src, dst)
                target.chmod(0o640)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['export', 'import'])
    parser.add_argument('--empty-only', action='store_true')
    args = parser.parse_args()
    if args.action == 'import':
        if not args.empty_only:
            parser.error('Import requires --empty-only and fresh restore storage.')
        unpack(sys.stdin.buffer, ROOT)
    else:
        with tarfile.open(fileobj=sys.stdout.buffer, mode='w|gz', dereference=False) as archive:
            for path in sorted(ROOT.rglob('*')):
                if path.is_symlink() or not (path.is_dir() or path.is_file()):
                    raise ValueError('Media contains a link or special file; inspect it before backup.')
                archive.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)

if __name__ == '__main__':
    main()
