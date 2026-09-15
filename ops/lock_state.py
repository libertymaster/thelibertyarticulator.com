"""Verify release input AND output hashes; stage before replacing reviewed locks."""
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from common import ROOT, env_file

OUTPUTS = {
    'images': ['images.lock.env'],
    'dependencies': ['requirements/production.lock', 'requirements/development.lock',
                     'frontend/package-lock.json', 'requirements/resolver-tools.json'],
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(names):
    h = hashlib.sha256()
    for name in names:
        h.update(name.encode() + b'\0' + (ROOT / name).read_bytes() + b'\0')
    return h.hexdigest()


def inputs(kind):
    if kind == 'images':
        return ['images.sources.env']
    if kind != 'dependencies':
        raise ValueError('Unknown lock kind: ' + kind)
    return ['requirements/core.in', 'requirements/production.in', 'requirements/development.in',
            'requirements/lock-tools.in', 'frontend/package.json', 'config/build-baseline.json',
            'ops/lock_dependencies.py']


def input_fingerprint(kind):
    base = fingerprint(inputs(kind))
    if kind == 'images':
        return base
    images = env_file(ROOT / 'images.lock.env')
    selected = {name: images[name] for name in ('PYTHON_BUILD_IMAGE', 'PYTHON_IMAGE', 'NODE_IMAGE')}
    return digest((base + json.dumps(selected, sort_keys=True)).encode())


def verify(kind):
    try:
        meta = json.loads((ROOT / f'{kind}.lock.meta.json').read_text())
        if meta.get('format') != 2 or meta.get('kind') != kind:
            raise ValueError('older or incomplete lock metadata')
        if meta.get('input_sha256') != input_fingerprint(kind):
            raise ValueError('source inputs or build-image digests changed')
        if set(meta.get('outputs', {})) != set(OUTPUTS[kind]):
            raise ValueError('missing output hashes')
        for name in OUTPUTS[kind]:
            path = ROOT / name
            if path.is_symlink() or not path.is_file() or not path.stat().st_size:
                raise ValueError('missing/empty/symlink lock: ' + name)
            if digest(path.read_bytes()) != meta['outputs'][name]:
                raise ValueError('lock output changed: ' + name)
    except (OSError, KeyError, ValueError) as exc:
        tool = 'lock_images.py' if kind == 'images' else 'lock_dependencies.py'
        raise SystemExit(f'{kind} locks are not approved for these inputs ({exc}). '
                         f'Review and run python3 ops/{tool} explicitly. No lock was overwritten.') from exc
    return meta


@contextmanager
def resolution_lock():
    """Serialize image/dependency publication on the documented Linux build host."""
    import fcntl
    runtime = ROOT / 'runtime'
    runtime.mkdir(exist_ok=True)
    path = runtime / 'resolution.lock'
    if path.is_symlink():
        raise SystemExit('Refusing a symlink resolution lock.')
    with path.open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise SystemExit('Another lock resolver is running in this project.') from exc
        yield


def commit(kind, payloads, details=None, expected_input=None):
    """Commit validated candidates; metadata is published last and fails closed.

    Previous files are saved under runtime/lock-backups. A normal write failure
    restores them. A process/power failure cannot leave a falsely verified set,
    because verify() also checks every output hash. This is not an OS transaction.
    """
    if set(payloads) != set(OUTPUTS[kind]):
        raise ValueError('Incomplete lock payload')
    if not all(isinstance(v, bytes) and v.strip() for v in payloads.values()):
        raise ValueError('Empty lock candidate')
    current = input_fingerprint(kind)
    if expected_input is not None and current != expected_input:
        raise SystemExit('Inputs changed during resolution. Candidates were not published.')
    meta_name = f'{kind}.lock.meta.json'
    meta = {'format': 2, 'kind': kind, 'input_sha256': current,
            'outputs': {name: digest(value) for name, value in payloads.items()},
            'details': details or {}}
    all_data = dict(payloads)
    all_data[meta_name] = (json.dumps(meta, indent=2, sort_keys=True) + '\n').encode()
    prior = {}
    for name in all_data:
        path = ROOT / name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != ROOT.parent):
            raise ValueError('Refusing symlink lock destination: ' + name)
        prior[name] = path.read_bytes() if path.is_file() else None
    backup_parent = ROOT / 'runtime/lock-backups'
    backup_parent.mkdir(parents=True, exist_ok=True)
    backup = Path(tempfile.mkdtemp(prefix=kind + '-', dir=backup_parent))
    for name, data in prior.items():
        if data is not None:
            path = backup / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    staged = []
    try:
        for name, data in all_data.items():
            path = ROOT / name
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
            with os.fdopen(fd, 'wb') as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, 0o644)
            staged.append((Path(temporary), path))
        for temporary, path in staged:
            temporary.replace(path)
        verify(kind)
    except BaseException:
        for name, data in prior.items():
            path = ROOT / name
            if data is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(data)
        raise
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)
    print('Previous lock files backed up to ' + str(backup))
    return meta
