import importlib.util
import json
import sys
from pathlib import Path
import pytest
import yaml
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ops'))
import common
import init_secrets
import render_config

@pytest.fixture
def stack(): return yaml.safe_load((ROOT/'compose.yaml').read_text())

def test_production_has_no_published_ports(stack):
    assert not any('ports' in service for service in stack['services'].values())
    override=yaml.safe_load((ROOT/'compose.prod.yaml').read_text())
    assert not any('ports' in service for service in override['services'].values())

def test_every_image_is_a_required_lock_input(stack):
    for name,service in stack['services'].items():
        if name in {'web','worker','beat','migrate'}: continue
        assert ':?Run ops/prepare.sh first}' in service['image']

def test_internal_network_boundaries(stack):
    for name in ['edge','app','data','monitoring','docker_api']:
        assert stack['networks'][name]['internal'] is True
    assert stack['services']['cloudflared']['networks']==['edge','egress']
    assert stack['services']['postgres']['networks']==['data']
    assert 'edge' not in stack['services']['grafana']['networks']

def test_no_accidentally_split_flow_mounts(stack):
    for service in stack['services'].values():
        for mount in service.get('volumes',[]):
            assert ':' in mount and mount not in ('z','ro','rslave')
        for mount in service.get('tmpfs',[]):
            assert mount.startswith('/')

def test_cadvisor_comma_arguments_preserved(stack):
    command=stack['services']['cadvisor']['command']
    assert '--whitelisted_container_labels=com.docker.compose.service,com.docker.compose.project' in command
    assert not any(x in command for x in ['percpu','process','sched','udp'])

def test_socket_mount_only_in_proxy(stack):
    owners=[name for name,service in stack['services'].items() if any('/var/run/docker.sock:' in v for v in service.get('volumes',[]))]
    assert owners==['docker-socket-proxy']

def test_secrets_never_overwritten_and_acl_hashes(tmp_path,monkeypatch):
    monkeypatch.setattr(init_secrets,'ROOT',tmp_path)
    init_secrets.main()
    before={f.name:f.read_bytes() for f in (tmp_path/'secrets').iterdir()}
    init_secrets.main()
    after={f.name:f.read_bytes() for f in (tmp_path/'secrets').iterdir()}
    assert before==after
    assert (tmp_path/'secrets').stat().st_mode & 0o777 == 0o700
    acl=(tmp_path/'secrets/redis.acl').read_text()
    assert before['redis_app_password'].decode().strip() not in acl
    assert 'user default off' in acl
    passwords=json.loads(before['redis_exporter.json'])
    assert passwords['redis://exporter@redis:6379']==before['redis_exporter_password'].decode().strip()

def test_rendered_configs_consistent(tmp_path,monkeypatch):
    monkeypatch.setattr(render_config,'ROOT',tmp_path)
    monkeypatch.setattr(render_config,'configuration',lambda:{'PUBLIC_HOST':'example.org','EDITOR_HOST':'editor.example.org','COMPOSE_PROJECT_NAME':'test_stack'})
    render_config.main()
    proxy=json.loads((tmp_path/'runtime/traefik-dynamic.yml').read_text())
    assert proxy['http']['routers']['editor']['rule']=='Host(`editor.example.org`)'
    assert proxy['http']['services']['django']['loadBalancer']['servers']==[{'url':'http://web:8000'}]
    prometheus=json.loads((tmp_path/'runtime/prometheus.yml').read_text())
    jobs={j['job_name']:j for j in prometheus['scrape_configs']}
    assert jobs['django']['metrics_path']=='/metrics/'
    assert jobs['probe-public']['static_configs'][0]['targets']==['https://example.org/health/']

def test_env_parser_rejects_interpolation(tmp_path):
    path=tmp_path/'env';path.write_text('A=$(echo unsafe)\n')
    with pytest.raises(ValueError): common.env_file(path)

def test_known_celery_transport_pair_is_explicit():
    requirements=(ROOT/'requirements/core.in').read_text()
    assert 'celery[redis]==5.6.3' in requirements
    assert 'kombu==5.6.2' in requirements
    assert 'redis==6.4.0' in requirements
