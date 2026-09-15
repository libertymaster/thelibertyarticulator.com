#!/usr/bin/env python3
import os
import re
from common import ROOT, configuration, env_file
from lock_state import verify

def main():
    env=configuration()
    verify("images")
    verify("dependencies")
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{2,63}', env.get('COMPOSE_PROJECT_NAME','')):
        raise SystemExit('Choose an explicit, unique lowercase Compose project name.')
    for name,image in env_file(ROOT/'images.lock.env').items():
        if not re.fullmatch(r'.+@sha256:[a-f0-9]{64}',image):
            raise SystemExit(f'{name} is not an immutable digest reference.')
    for filename in ['images.lock.env','requirements/production.lock','frontend/package-lock.json','runtime/traefik-dynamic.yml']:
        if not (ROOT/filename).is_file():
            raise SystemExit(f'Missing {filename}; run ops/prepare.sh.')
    if os.environ.get('MODE','prod') == 'prod':
        if env.get('REQUIRE_CF_ACCESS') != '1':
            raise SystemExit('Production requires Cloudflare Access on the editor hostname.')
        team=env.get('CF_ACCESS_TEAM_DOMAIN','')
        if not re.fullmatch(r'[a-z0-9-]+\.cloudflareaccess\.com',team) or not env.get('CF_ACCESS_AUD'):
            raise SystemExit('Configure CF_ACCESS_TEAM_DOMAIN and CF_ACCESS_AUD in .env.')
        token=(ROOT/'secrets/cloudflared_token').read_text().strip()
        if len(token)<40 or token.startswith('REPLACE_'):
            raise SystemExit('Place the dashboard tunnel token in secrets/cloudflared_token on the host.')
        if env.get('PUBLIC_ORIGIN') != 'https://'+env.get('PUBLIC_HOST',''):
            raise SystemExit('PUBLIC_ORIGIN must match the HTTPS public hostname.')
    print('Preflight passed. No secret values were printed.')

if __name__=='__main__':
    main()
