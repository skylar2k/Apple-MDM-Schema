#!/usr/bin/env python

import json
import pathlib
from devtools import pprint
from pydantic import BaseModel
from schema_parser import (
    parse_schema,
    SchemaDocument,
    # ProfileJsonSchema,
    model_from_payload_keys,
)
from schema_parser.json_schema import make_configuration_profile

APPLE_SCHEMA_PATH: pathlib.Path = pathlib.Path("./device-management/mdm/profiles")


def main():
    profiles: dict[str, SchemaDocument] = {}
    for file in APPLE_SCHEMA_PATH.rglob("*.yaml"):
        with open(file) as f:
            profile = parse_schema(f.read())
            if profile.payload.payloadtype in [
                "TopLevel",
                "CommonPayloadKeys",
                ".GlobalPreferences",
            ]:
                continue
            profiles[profile.payload.payloadtype] = profile

    payload_registry: dict[str, type[BaseModel]] = {}

    for profile in profiles:
        if profile in ["TopLevel", "CommonPayloadKeys", ".GlobalPreferences"]:
            continue

        schema = profiles[profile]
        payload_keys = model_from_payload_keys(
            schema.payloadkeys,
            payload_type=profile,
            model_name=schema.title,
        )
        payload_registry[profile] = payload_keys

    test = make_configuration_profile(payload_registry)
    with open("test.schema.json", "w") as f:
        json.dump(
            test.model_json_schema(True, ref_template="#/$defs/{model}"), f, indent=2
        )
    pprint(test.model_json_schema(True, ref_template="#/$defs/{model}"))


if __name__ == "__main__":
    main()
