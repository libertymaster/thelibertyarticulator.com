#!/usr/bin/env python3
import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError

base=os.environ.get('SMOKE_BASE_URL','http://127.0.0.1:8000').rstrip('/')
headers={'Host':os.environ.get('PUBLIC_HOST','thelibertyarticulator.com'),'X-Forwarded-Proto':'https'}
for path in ['/', '/archive/', '/historys-heroes/', '/standards/', '/sitemap.xml', '/health/', '/ready/', '/api/v1/archive/']:
    with urlopen(Request(base+path,headers=headers),timeout=15) as response:
        body=response.read()
        assert response.status==200, path
        if path.startswith('/api/'):
            payload=json.loads(body)
            assert payload['schema_version']=='1' and isinstance(payload['results'],list)
        print('PASS', path)
try:
    urlopen(Request(base+'/api/v1/archive/?historical_from=0',headers=headers),timeout=15)
    raise AssertionError('Invalid historical year was accepted')
except HTTPError as exc:
    assert exc.code == 400
print('PASS archive input validation')
