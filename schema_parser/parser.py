from collections.abc import Iterable
import pathlib

import ruamel.yaml
from .models import SchemaDocument

SCHEMA_PAYLOAD_TYPES: list[str] = [
    "TopLevel",
    "CommonPayloadKeys",
    ".GlobalPreferences",
]


def parse_schema(data: str) -> SchemaDocument:
    yaml = ruamel.yaml.YAML(typ="rt")
    data = yaml.load(data)

    return SchemaDocument.model_validate(data)


def load_schema(files: Iterable[pathlib.Path]) -> dict[str, SchemaDocument]:
    profiles: dict[str, SchemaDocument] = {}
    for file in files:
        with open(file) as f:
            profile: SchemaDocument = parse_schema(f.read())
            # We don't care about schema defining payload types, we want the actual different payload types
            if profile.payload.payloadtype in SCHEMA_PAYLOAD_TYPES:
                continue
            profiles[profile.payload.payloadtype] = profile
    return profiles
