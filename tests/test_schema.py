import copy
import pathlib

import pytest
import ruamel.yaml
from jsonschema import Draft7Validator

from schema_parser import convert, load_profiles

SOURCE = pathlib.Path(__file__).parent.parent / "device-management/mdm/profiles"
pytestmark = pytest.mark.skipif(not SOURCE.is_dir(), reason="submodule not checked out")

MUNKI = """
PayloadDisplayName: UiB Apps - Munkireport - Servicemanagement
PayloadIdentifier: no.uib.profiles.apps.munkireport.servicemanagement
PayloadUUID: 2d5fa223-1183-5425-a3a7-ef763668d5dd
PayloadOrganization: Universitetet i Bergen
PayloadType: Configuration
PayloadVersion: 1
PayloadContent:
  - PayloadType: 'com.apple.servicemanagement'
    PayloadIdentifier: no.uib.profiles.apps.munkireport.servicemanagement.main
    PayloadUUID: 9aaf33be-eba1-5392-9827-fe91a10278c5
    PayloadVersion: 1
    Rules:
      - RuleType: Label
        RuleValue: com.github.munkireport.runner
"""


@pytest.fixture(scope="module")
def schema():
    return convert(*load_profiles(SOURCE.glob("*.yaml")))


@pytest.fixture
def profile():
    return ruamel.yaml.YAML(typ="safe").load(MUNKI)


def errors(schema, doc):
    return [e.message for e in Draft7Validator(schema).iter_errors(doc)]


def test_schema_is_valid_draft7(schema):
    Draft7Validator.check_schema(schema)


def test_example_is_valid(schema, profile):
    assert errors(schema, profile) == []


def test_custom_payload_type_is_allowed(schema, profile):
    profile["PayloadContent"].append(
        {
            "PayloadType": "no.uib.custom",
            "PayloadIdentifier": "x",
            "PayloadUUID": "y",
            "PayloadVersion": 1,
            "Anything": {"goes": [1, 2]},
        }
    )
    assert errors(schema, profile) == []


def test_custom_payload_still_needs_common_keys(schema, profile):
    profile["PayloadContent"].append({"PayloadType": "no.uib.custom"})
    assert errors(schema, profile)


def test_apple_payload_is_checked_by_its_own_type(schema, profile):
    bad = copy.deepcopy(profile)
    bad["PayloadContent"][0]["Rules"][0]["RuleType"] = "Bogus"
    assert errors(schema, bad)  # enum, two levels down

    bad = copy.deepcopy(profile)
    del bad["PayloadContent"][0]["Rules"][0]["RuleValue"]
    assert errors(schema, bad)  # required, nested

    bad = copy.deepcopy(profile)
    bad["PayloadContent"][0]["Rulez"] = []
    assert errors(schema, bad)  # typo'd key


def test_keys_of_other_payload_types_dont_leak(schema, profile):
    profile["PayloadContent"][0]["PayloadType"] = "com.apple.dock"
    assert errors(schema, profile)  # Rules isn't a dock key


def test_lax_allows_unknown_keys(profile):
    lax = convert(*load_profiles(SOURCE.glob("*.yaml")), strict=False)
    profile["PayloadContent"][0]["Rulez"] = []
    assert errors(lax, profile) == []


def test_payload_type_with_several_schema_files(schema, profile):
    # com.apple.MCX is split over several files; any of them may match.
    profile["PayloadContent"] = [
        {
            "PayloadType": "com.apple.MCX",
            "PayloadIdentifier": "x",
            "PayloadUUID": "y",
            "PayloadVersion": 1,
            "DestroyFVKeyOnStandby": True,
        }
    ]
    assert errors(schema, profile) == []


def test_top_level_requires_payload_content(schema, profile):
    del profile["PayloadContent"]
    assert errors(schema, profile)
