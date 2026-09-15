import copy
import importlib.util
import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError
from apps.journal.contracts import SourcesPayload, ArchivePayload, ChronologyPayload
ROOT=Path(__file__).resolve().parents[2]
MODELS={'sources':SourcesPayload,'archive':ArchivePayload,'chronology':ChronologyPayload}

@pytest.mark.parametrize('name',MODELS)
def test_fixture_matches_schema_and_model(name):
    schema=json.loads((ROOT/f'contracts/{name}.schema.json').read_text())
    data=json.loads((ROOT/f'contracts/fixtures/{name}.json').read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(data)
    assert MODELS[name].model_validate(data).model_dump(mode='json')==data

@pytest.mark.parametrize('name',MODELS)
def test_unexpected_field_rejected(name):
    data=json.loads((ROOT/f'contracts/fixtures/{name}.json').read_text())
    data['secret_token']='must-not-leak'
    with pytest.raises(ValidationError): MODELS[name].model_validate(data)

@pytest.mark.parametrize('name',MODELS)
def test_version_is_required_on_the_wire(name):
    schema=json.loads((ROOT/f'contracts/{name}.schema.json').read_text())
    data=json.loads((ROOT/f'contracts/fixtures/{name}.json').read_text())
    data.pop('schema_version')
    assert list(Draft202012Validator(schema).iter_errors(data))

def test_source_type_not_arbitrary_string():
    data=json.loads((ROOT/'contracts/fixtures/sources.json').read_text())
    data['sources'][0]['kind']='invented'
    with pytest.raises(ValidationError): SourcesPayload.model_validate(data)

def test_archive_page_size_bounded():
    data=json.loads((ROOT/'contracts/fixtures/archive.json').read_text())
    data['page_size']=100000
    with pytest.raises(ValidationError): ArchivePayload.model_validate(data)

def test_numeric_types_are_not_coerced():
    data=json.loads((ROOT/'contracts/fixtures/chronology.json').read_text())
    data['events'][0]['year']='1815'
    with pytest.raises(ValidationError): ChronologyPayload.model_validate(data)
