import ast
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'ops'))
import lock_dependencies
import lock_images
import lock_state
import python_contract
from apps.core.migration_history import unknown_migrations


def test_core_baseline_and_separate_optional_profiles():
    baseline = json.loads((ROOT / 'config/build-baseline.json').read_text())
    assert baseline['packages'] == {'Django': '6.0.8', 'Wagtail': '7.4.3'}
    assert baseline['python'] == [3, 14, 7]
    assert baseline['os_id'] == 'debian' and baseline['os_version'] == '13'
    production = (ROOT / 'requirements/production.in').read_text()
    core = (ROOT / 'requirements/core.in').read_text()
    assert '-r core.in' in production and '-r optional/' not in production
    assert 'Django==6.0.8' in core and 'Wagtail==7.4.3' in core
    assert 'wagtail-fedit' not in core and 'django-celery-beat' not in core
    assert '-c production.lock' in (ROOT / 'requirements/development.in').read_text()


def test_docker_build_has_only_three_stages_and_no_cross_libc_copy():
    text = (ROOT / 'Dockerfile').read_text()
    stages = [line for line in text.splitlines() if line.startswith('FROM ')]
    assert len(stages) == 3
    assert '${NODE_IMAGE} AS assets' in stages[0]
    assert '${PYTHON_BUILD_IMAGE} AS application-build' in stages[1]
    assert '${PYTHON_IMAGE} AS runtime' in stages[2]
    assert '--only-binary=:all:' in text and '--require-hashes' in text
    runtime = text.split(stages[2], 1)[1]
    assert 'RUN [' in runtime and 'RUN /bin/sh' not in runtime
    assert 'USER 10001:10001' in runtime and 'check_runtime.py' in runtime
    assert 'lxml.etree' not in (ROOT / 'ops/check_runtime.py').read_text()


def test_migrate_service_uses_checked_forward_entrypoint():
    model = yaml.safe_load((ROOT / 'compose.yaml').read_text())
    assert model['services']['migrate']['command'] == ['python', 'manage.py', 'safe_migrate', '--noinput']
    script = (ROOT / 'apps/core/management/commands/safe_migrate.py').read_text()
    assert script.index("call_command('check_database_compatibility'") < script.index("call_command('migrate'")
    assert 'fake=True' not in script


def sample_contract():
    return {'version': [3, 14, 7], 'implementation': 'cpython', 'os_id': 'debian',
            'os_version': '13', 'libc': 'glibc 2.41', 'SOABI': 'cpython-314-x86_64-linux-gnu',
            'MULTIARCH': 'x86_64-linux-gnu', 'machine': 'x86_64', 'byteorder': 'little',
            'base_prefix': '/opt/python', 'base_executable': '/opt/python/bin/python3.14'}


def test_matching_contract_is_accepted():
    expected = json.loads((ROOT / 'config/build-baseline.json').read_text())
    value = sample_contract()
    python_contract.validate_contract(value, expected)
    python_contract.compare_contracts(value, dict(value))


@pytest.mark.parametrize('field,value', [('version',[3,13,9]),('os_id','alpine'),('os_version','12'),
                                        ('libc','musl 1.2'),('SOABI',None)])
def test_wrong_python_or_os_is_rejected(field, value):
    actual = sample_contract(); actual[field] = value
    with pytest.raises(ValueError):
        python_contract.validate_contract(actual, json.loads((ROOT / 'config/build-baseline.json').read_text()))


@pytest.mark.parametrize('field', python_contract.CONTRACT_KEYS)
def test_each_transfer_contract_field_is_checked(field):
    actual = sample_contract(); actual[field] = 'different'
    with pytest.raises(ValueError):
        python_contract.compare_contracts(sample_contract(), actual)


@pytest.mark.parametrize('source,canonical', [('node:24-bookworm-slim','docker.io/library/node'),
    ('docker.io/library/node@sha256:'+'a'*64,'docker.io/library/node'),
    ('dhi.io/python:3.14.7-debian13','dhi.io/python')])
def test_registry_repository_normalization(source,canonical):
    assert lock_images.repository(source) == canonical


@pytest.fixture
def lock_root(tmp_path, monkeypatch):
    monkeypatch.setattr(lock_state, 'ROOT', tmp_path)
    monkeypatch.setattr(lock_dependencies, 'ROOT', tmp_path)
    monkeypatch.setattr(lock_images, 'ROOT', tmp_path)
    for name in lock_state.inputs('dependencies') + ['ops/python_contract.py','ops/check_runtime.py']:
        p = tmp_path / name; p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes((ROOT / name).read_bytes())
    images = {name: 'example.test/' + name.lower() + '@sha256:' + 'a'*64
              for name in ('PYTHON_BUILD_IMAGE','PYTHON_IMAGE','NODE_IMAGE','REDIS_IMAGE')}
    (tmp_path/'images.sources.env').write_text('\n'.join(k+'='+v.split('@')[0]+':1' for k,v in images.items())+'\n')
    payload = ('\n'.join(k+'='+v for k,v in images.items())+'\n').encode()
    lock_state.commit('images',{'images.lock.env':payload},details={'sources':lock_images.env_file(tmp_path/'images.sources.env')})
    return tmp_path


def dependency_payload():
    package = json.loads((ROOT/'frontend/package.json').read_text())
    npm = {'lockfileVersion':3,'packages':{'':{key:package[key] for key in ('name','version','dependencies','devDependencies')}}}
    return {'requirements/production.lock':b'# synthetic test fixture only\n',
            'requirements/development.lock':b'# synthetic test fixture only\n',
            'frontend/package-lock.json':json.dumps(npm).encode(),
            'requirements/resolver-tools.json':b'{"test_fixture":true}\n'}


def test_lock_outputs_are_checked_not_just_inputs(lock_root):
    lock_state.commit('dependencies',dependency_payload())
    lock_state.verify('dependencies')
    (lock_root/'requirements/production.lock').write_text('corrupt')
    with pytest.raises(SystemExit,match='output changed'):
        lock_state.verify('dependencies')


def test_core_edit_invalidates_dependency_metadata(lock_root):
    lock_state.commit('dependencies',dependency_payload())
    with (lock_root/'requirements/core.in').open('a') as f: f.write('# approved future edit\n')
    with pytest.raises(SystemExit,match='inputs'):
        lock_state.verify('dependencies')


def test_python_digest_change_invalidates_dependency_metadata(lock_root):
    lock_state.commit('dependencies',dependency_payload())
    p=lock_root/'images.lock.env'; p.write_text(p.read_text().replace('python_image@sha256:'+'a'*64,'python_image@sha256:'+'b'*64))
    with pytest.raises(SystemExit): lock_state.verify('dependencies')


def test_monitoring_digest_does_not_invalidate_python_locks(lock_root):
    lock_state.commit('dependencies',dependency_payload())
    p=lock_root/'images.lock.env'; p.write_text(p.read_text().replace('redis_image@sha256:'+'a'*64,'redis_image@sha256:'+'b'*64))
    lock_state.verify('dependencies')
    # The image metadata itself still refuses a manually altered output.
    with pytest.raises(SystemExit): lock_state.verify('images')


def test_partial_or_legacy_dependency_metadata_is_rejected(lock_root):
    (lock_root/'dependencies.lock.meta.json').write_text('{"input_sha256":"legacy"}')
    with pytest.raises(SystemExit): lock_state.verify('dependencies')


def test_source_change_during_resolution_prevents_publication(lock_root):
    expected=lock_state.input_fingerprint('dependencies')
    (lock_root/'requirements/core.in').write_text('changed')
    with pytest.raises(SystemExit,match='during resolution'):
        lock_state.commit('dependencies',dependency_payload(),expected_input=expected)
    assert not (lock_root/'requirements/production.lock').exists()


def test_existing_frontend_lock_retained_but_old_python_locks_not_staged(lock_root,tmp_path):
    payload=dependency_payload()
    for name,data in payload.items(): (lock_root/name).write_bytes(data)
    stage=lock_root/'stage'; stage.mkdir()
    assert lock_dependencies.stage_inputs(stage,False)
    assert (stage/'frontend/package-lock.json').read_bytes()==payload['frontend/package-lock.json']
    assert not (stage/'requirements/production.lock').exists()
    assert not (stage/'requirements/development.lock').exists()


def test_frontend_drift_requires_explicit_refresh(lock_root):
    (lock_root/'frontend/package-lock.json').write_text('{"lockfileVersion":3,"packages":{"":{}}}')
    stage=lock_root/'stage'; stage.mkdir()
    with pytest.raises(ValueError,match='differs'):
        lock_dependencies.stage_inputs(stage,False)
    assert lock_dependencies.stage_inputs(stage,True) is False


def test_candidate_failure_leaves_old_locks_unchanged(lock_root,monkeypatch):
    payload=dependency_payload()
    lock_state.commit('dependencies',payload)
    before={n:(lock_root/n).read_bytes() for n in [*payload,'dependencies.lock.meta.json']}
    def fail(*args): raise RuntimeError('synthetic resolver failure')
    monkeypatch.setattr(lock_dependencies,'resolve_candidates',fail)
    monkeypatch.setattr(sys,'argv',['lock_dependencies.py'])
    with pytest.raises(RuntimeError): lock_dependencies.main()
    assert all((lock_root/n).read_bytes()==v for n,v in before.items())


def test_missing_only_cannot_certify_partial_locks(lock_root,monkeypatch):
    (lock_root/'requirements/production.lock').write_text('partial')
    monkeypatch.setattr(sys,'argv',['lock_dependencies.py','--missing-only'])
    with pytest.raises(SystemExit): lock_dependencies.main()
    assert not (lock_root/'dependencies.lock.meta.json').exists()


def test_legacy_python_refresh_preserves_unrelated_digests(lock_root):
    old_source = ROOT/'source-import/baselines/0.3.1/images.sources.env'
    dest=lock_root/'source-import/baselines/0.3.1/images.sources.env'
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(old_source.read_bytes())
    old=lock_images.env_file(dest)
    resolved={k:lock_images.repository(v)+'@sha256:'+'c'*64 for k,v in old.items()}
    (lock_root/'images.lock.env').write_text('\n'.join(k+'='+v for k,v in resolved.items())+'\n')
    legacy={'input_sha256':lock_state.digest(b'images.sources.env\0'+dest.read_bytes()+b'\0')}
    (lock_root/'images.lock.meta.json').write_text(json.dumps(legacy))
    desired=lock_images.env_file(ROOT/'images.sources.env')
    kept=lock_images.retained_pins(desired)
    assert 'PYTHON_AUDIT_IMAGE' not in kept
    assert 'PYTHON_BUILD_IMAGE' not in kept and 'PYTHON_IMAGE' not in kept
    assert kept['POSTGRES_IMAGE']==resolved['POSTGRES_IMAGE']
    assert kept['NODE_IMAGE']==resolved['NODE_IMAGE']
    desired['REDIS_IMAGE']='dhi.io/redis:changed'
    with pytest.raises(ValueError): lock_images.retained_pins(desired)


def test_migration_history_recognizes_squashed_history():
    available={('app','0003_squashed')}
    replacements={('app','0003_squashed'):[('app','0001'),('app','0002')]}
    assert unknown_migrations({('app','0001'),('app','0002')},available,replacements)==[]
    assert unknown_migrations({('wagtailcore','9999_future')},available,replacements)==[('wagtailcore','9999_future')]


def test_guard_has_no_database_write_calls():
    text=(ROOT/'apps/core/management/commands/check_database_compatibility.py').read_text()
    tree=ast.parse(text)
    called={node.func.attr for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
    assert not ({'save','delete','create','update','ensure_schema','record_applied'} & called)


def test_final_image_qa_is_isolated_and_shell_free():
    import validate_app
    command=validate_app.container_command('sha256:'+'f'*64,['manage.py','test','tests.django_tests'])
    assert command[command.index('--network')+1]=='none'
    assert '--read-only' in command and '-v' not in command and '--mount' not in command
    assert command[command.index('--entrypoint')+1]=='/venv/bin/python'
    assert command[command.index('--user')+1]=='10001:10001'


def test_compose_uses_file_inputs_not_unrelated_shell_overrides(tmp_path,monkeypatch):
    import common
    monkeypatch.setattr(common,'ROOT',tmp_path)
    (tmp_path/'.env').write_text('APP_IMAGE=approved-app:1\nCOMPOSE_PROJECT_NAME=approved_project\n')
    (tmp_path/'images.lock.env').write_text('PYTHON_IMAGE=dhi.io/python@sha256:'+'a'*64+'\n')
    monkeypatch.setenv('PYTHON_IMAGE','unapproved:latest')
    monkeypatch.setenv('APP_IMAGE','wrong-app:1')
    seen={}
    def run(*args,**kwargs): seen.update(kwargs); return SimpleNamespace(returncode=0)
    monkeypatch.setattr(common.subprocess,'run',run)
    common.compose('config','--quiet')
    assert seen['env']['PYTHON_IMAGE']=='dhi.io/python@sha256:'+'a'*64
    assert seen['env']['APP_IMAGE']=='approved-app:1'


def test_lock_publication_failure_restores_previous_outputs(lock_root, monkeypatch):
    payload = dependency_payload()
    lock_state.commit('dependencies', payload)
    names = [*payload, 'dependencies.lock.meta.json']
    before = {name: (lock_root / name).read_bytes() for name in names}
    altered = dict(payload)
    altered['requirements/production.lock'] = b'# another synthetic lock fixture\n'
    real_replace = Path.replace
    calls = []

    def fail_second_replace(path, target):
        calls.append(str(target))
        if len(calls) == 2:
            raise OSError('simulated write interruption')
        return real_replace(path, target)

    monkeypatch.setattr(Path, 'replace', fail_second_replace)
    with pytest.raises(OSError, match='simulated'):
        lock_state.commit('dependencies', altered)
    assert len(calls) == 2
    assert all((lock_root / name).read_bytes() == data for name, data in before.items())
    lock_state.verify('dependencies')


def test_resolution_mutex_rejects_another_active_resolver(lock_root):
    with lock_state.resolution_lock():
        with pytest.raises(SystemExit, match='Another lock resolver'):
            with lock_state.resolution_lock():
                pytest.fail('Concurrent resolver unexpectedly entered')


def test_source_symlink_lock_destination_is_rejected(lock_root):
    target = lock_root / 'requirements/production.lock'
    external = lock_root / 'outside.txt'
    external.write_text('not a lock; do not change')
    target.symlink_to(external)
    with pytest.raises(ValueError, match='symlink'):
        lock_state.commit('dependencies', dependency_payload())
    assert external.read_text() == 'not a lock; do not change'
