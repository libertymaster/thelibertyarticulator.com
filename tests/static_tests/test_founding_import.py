import ast
import hashlib
import io
import json
import sys
import tarfile
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'ops'))
from media_archive import unpack


def test_source_files_match_recorded_checksums():
    manifest = json.loads((ROOT / 'source-import/manifest.json').read_text())
    assert len(manifest['files']) == 13
    for entry in manifest['files']:
        data = (ROOT / 'source-import/original' / entry['path']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry['sha256']


def test_all_sections_have_exactly_one_allowed_template_and_keys():
    registry = json.loads((ROOT / 'content/founding/layout_registry.json').read_text())
    pages = json.loads((ROOT / 'content/founding/pages.json').read_text())
    seen = set()
    for page in pages.values():
        for section in page['sections']:
            value = section['value']
            key = value['layout']
            assert key not in seen
            seen.add(key)
            template = ROOT / 'templates' / registry[key]['template']
            assert template.is_file()
            for field in ['texts', 'links']:
                keys = [item['key'] for item in value[field]]
                assert len(keys) == len(set(keys))
                assert set(keys) == set(registry[key][field])
    assert len(seen) == 50
    assert seen == set(registry)


def test_commissioning_portfolio_preserves_original_counts_and_labels():
    data = json.loads((ROOT / 'content/founding/journal_data.json').read_text())
    records = data['publications']
    assert len(records) == 10
    assert sum(p['status'] == 'Planned' for p in records) == 9
    assert sum(p['status'] == 'Public draft' for p in records) == 1
    assert [sum(p['discipline'] == d for p in records) for d in ['History', 'Philosophy', 'Politics']] == [5, 3, 2]
    assert len(data['workflow']) == 10
    assert len(data['blochLens']) == 7
    assert len(data['standardsSources']) == 8


def test_imported_evidence_is_structured_without_invented_classifications():
    data = json.loads((ROOT / 'content/founding/article_evidence.json').read_text())
    assert len(data['sources']) == len(data['citations']) == 4
    assert all(s['kind'] == 'unclassified' and s['year'] is None for s in data['sources'])
    keys = {s['key'] for s in data['sources']}
    assert all(c['source_key'] in keys and not c['locator'] for c in data['citations'])
    assert all(s['edition_label'] and s['use_description'] and s['verification_status'] for s in data['sources'])


def test_prior_pins_preserved_except_the_two_approved_framework_changes():
    import re
    profile = (ROOT / 'source-import/requested-profile.txt').read_text()
    expected = {line.strip() for line in profile.splitlines() if re.fullmatch(r'[\w-]+(?:\[[\w,]+\])?==[\w.]+', line.strip())}
    actual = set((ROOT / 'requirements/core.in').read_text().splitlines())
    for path in (ROOT / 'requirements/optional').glob('*.in'):
        actual.update(path.read_text().splitlines())
    expected -= {'Django==6.1.1', 'Wagtail==8.0'}
    expected |= {'Django==6.0.8', 'Wagtail==7.4.3'}
    assert len(expected) == 28
    assert expected <= actual


def test_shell_free_application_runtime_and_abi_matching_builder():
    text = (ROOT / 'Dockerfile').read_text()
    final = text.split('FROM ${PYTHON_IMAGE} AS runtime', 1)[1]
    assert 'RUN groupadd' not in final and 'entrypoint.sh' not in final
    assert 'COPY --from=application-build' in final
    assert 'PYTHON_BUILD_IMAGE' in text and 'PYTHON_AUDIT_IMAGE' not in text
    assert 'PYTHON_BUILD_IMAGE=dhi.io/python:3.14.7-debian13-dev' in (ROOT / 'images.sources.env').read_text()
    stack = yaml.safe_load((ROOT / 'compose.yaml').read_text())
    for name in ['web', 'worker', 'beat', 'redis', 'postgres']:
        assert stack['services'][name]['healthcheck']['test'][0] == 'CMD'


def test_optional_identity_has_separate_data_no_ports_and_no_django_auth_override():
    stack = yaml.safe_load((ROOT / 'compose.keycloak.yaml').read_text())
    assert not any('ports' in x for x in stack['services'].values())
    assert stack['networks']['keycloak_db']['internal'] is True
    assert stack['services']['keycloak']['profiles'] == ['identity']
    assert 'web' not in stack['services']
    assert stack['services']['keycloak-postgres']['secrets'] == ['keycloak_postgres_admin_password', 'keycloak_database_password']


def test_source_citations_and_ledger_use_one_structured_source():
    assert 'source.bibliography' in (ROOT / 'templates/journal/includes/imported_notes.html').read_text()
    assert 'source.use_description' in (ROOT / 'templates/journal/includes/imported_ledger.html').read_text()
    content = (ROOT / 'templates/imported/layouts/article-04.html').read_text()
    assert 'includes/imported_notes.html' in content
    assert 'includes/imported_ledger.html' in content


def archive_bytes(name, data=b'content', kind=tarfile.REGTYPE):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w:gz') as archive:
        item = tarfile.TarInfo(name)
        item.type = kind
        item.size = len(data) if kind == tarfile.REGTYPE else 0
        item.linkname = '../outside'
        archive.addfile(item, io.BytesIO(data) if item.size else None)
    output.seek(0)
    return output


@pytest.mark.parametrize('path', ['../outside', '/absolute', 'nested/../../outside', 'bad\\path'])
def test_media_restore_rejects_unsafe_paths(tmp_path, path):
    with pytest.raises(ValueError):
        unpack(archive_bytes(path), tmp_path)


@pytest.mark.parametrize('kind', [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.CHRTYPE, tarfile.FIFOTYPE])
def test_media_restore_rejects_links_and_devices(tmp_path, kind):
    with pytest.raises(ValueError):
        unpack(archive_bytes('file', kind=kind), tmp_path)


def test_media_restore_writes_regular_files_and_refuses_nonempty(tmp_path):
    unpack(archive_bytes('photos/photo.txt'), tmp_path)
    assert (tmp_path / 'photos/photo.txt').read_bytes() == b'content'
    with pytest.raises(ValueError):
        unpack(archive_bytes('second.txt'), tmp_path)


def test_importer_defaults_to_no_mutation():
    module = ast.parse((ROOT / 'apps/journal/management/commands/import_founding_content.py').read_text())
    handle = next(n for n in ast.walk(module) if isinstance(n, ast.FunctionDef) and n.name == 'handle')
    branches = [n for n in handle.body if isinstance(n, ast.If)]
    assert any('apply' in ast.unparse(n.test) and any(isinstance(x, ast.Return) for x in n.body) for n in branches)
