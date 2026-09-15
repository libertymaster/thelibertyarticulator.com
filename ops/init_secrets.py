#!/usr/bin/env python3
import hashlib
import json
import os
import secrets
from common import ROOT

def main():
    folder = ROOT / 'secrets'
    folder.mkdir(mode=0o700, exist_ok=True)
    folder.chmod(0o700)
    def write(name, value):
        path = folder / name
        if not path.exists():
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, 'w') as handle:
                handle.write(value + '\n')
            # Individual file binds are readable by distinct non-root container UIDs.
            # The enclosing host directory remains private (0700).
            path.chmod(0o444)
        return path.read_text().strip()
    for name in ['django_secret_key', 'postgres_admin_password', 'postgres_app_password',
                 'postgres_metrics_password', 'grafana_admin_password',
                 'keycloak_postgres_admin_password', 'keycloak_database_password', 'keycloak_bootstrap_password']:
        write(name, secrets.token_urlsafe(64))
    app = write('redis_app_password', secrets.token_urlsafe(48))
    exporter = write('redis_exporter_password', secrets.token_urlsafe(48))
    digest = lambda value: hashlib.sha256(value.encode()).hexdigest()
    # Redis databases are not an authorization boundary. Each user has an explicit role.
    acl = '\n'.join([
        'user default off',
        f'user app on #{digest(app)} ~* &* +@all -@admin -flushall -flushdb',
        'user health on nopass -@all +ping',
        f'user exporter on #{digest(exporter)} ~* -@all +ping +hello +echo +info +select +dbsize +lastsave +client|setname +client|list +config|get +slowlog|get +slowlog|len +latency|latest +memory|stats +cluster|info',
    ])
    existing_acl = folder / 'redis.acl'
    if existing_acl.exists() and 'user health on nopass -@all +ping' not in existing_acl.read_text():
        raise SystemExit('Existing Redis ACL uses the previous health protocol. Do not overwrite live secrets. Use a fresh 0.3.0 test directory, or follow docs/DHI_UPGRADE.md.')
    write('redis.acl', acl)
    write('redis_exporter.json', json.dumps({'redis://exporter@redis:6379': exporter}, indent=2))
    write('cloudflared_token', 'REPLACE_WITH_DASHBOARD_TUNNEL_TOKEN')
    write('email_password', '')
    print('Secret files initialized. Existing values were preserved; none were printed.')

if __name__ == '__main__':
    main()
