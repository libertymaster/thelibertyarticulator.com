"""Shell-free process entry point for the hardened Python runtime."""
import os
import sys
from pathlib import Path

def main():
    args = sys.argv[1:]
    if not args:
        raise SystemExit('A process command is required.')
    if args[0] == 'gunicorn':
        folder = Path('/tmp/prometheus')
        folder.mkdir(mode=0o700, exist_ok=True)
        os.environ['PROMETHEUS_MULTIPROC_DIR'] = str(folder)
        for path in folder.glob('*.db'):
            if path.is_file() and not path.is_symlink():
                path.unlink()
    if args[0] == 'worker':
        concurrency = int(os.environ.get('CELERY_CONCURRENCY', '2'))
        if not 1 <= concurrency <= 64:
            raise SystemExit('CELERY_CONCURRENCY must be between 1 and 64.')
        args = ['celery', '-A', 'config', 'worker', '--loglevel=INFO', '--hostname=worker@%h', f'--concurrency={concurrency}']
    os.execvp(args[0], args)

if __name__ == '__main__':
    main()
