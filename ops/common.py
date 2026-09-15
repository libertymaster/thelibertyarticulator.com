import os
import re
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def env_file(path):
    result = {}
    if not Path(path).exists():
        return result
    for number, raw in enumerate(Path(path).read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            raise ValueError(f'{path}:{number}: expected KEY=value')
        key, value = line.split('=', 1)
        if not re.fullmatch(r'[A-Z][A-Z0-9_]*', key):
            raise ValueError(f'{path}:{number}: invalid environment key')
        if value[:1] in ('"', "'") and value[-1:] == value[:1]:
            value = value[1:-1]
        if '$' in value or '\n' in value:
            raise ValueError(f'{path}:{number}: use literal values without variable interpolation')
        result[key] = value
    return result

def configuration():
    values = env_file(ROOT / '.env')
    if not values:
        raise SystemExit('Create .env from .env.example, then run ops/prepare.sh.')
    return values

def compose(*args, check=True):
    mode = os.environ.get('MODE', 'prod')
    if mode not in {'prod', 'dev'}:
        raise SystemExit('MODE must be prod or dev.')
    values = configuration()
    command = ['docker', 'compose', '--env-file', str(ROOT / '.env'), '--env-file', str(ROOT / 'images.lock.env'),
               '-f', str(ROOT / 'compose.yaml'), '-f', str(ROOT / f'compose.{mode}.yaml')]
    for filename in filter(None, os.environ.get('COMPOSE_EXTRA_FILES', '').split(',')):
        if filename not in {'compose.ops.yaml', 'compose.selinux.yaml', 'compose.keycloak.yaml'}:
            raise SystemExit('Unsupported extra Compose file.')
        command += ['-f', str(ROOT / filename)]
    process_env = dict(os.environ)
    process_env.update(values)
    process_env.update(env_file(ROOT / 'images.lock.env'))
    return subprocess.run(command + list(args), cwd=ROOT, check=check, env=process_env)
