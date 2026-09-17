#!/usr/bin/env python

import json
import pathlib
from devtools import pprint
from pydantic import BaseModel, ConfigDict, Field, create_model
from schema_parser import (
    parse_schema,
    SchemaDocument,
    # ProfileJsonSchema,
    model_from_payload_keys,
)
from schema_parser.json_schema import make_configuration_profile, make_payload_union

APPLE_SCHEMA_PATH: pathlib.Path = pathlib.Path("./mdm/profiles/")


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
    # pprint(profiles)

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
        # pprint(payload_keys)
        payload_registry[profile] = payload_keys
    # for payload_type, model in payload_registry.items():
    #    print(payload_type, model.__name__)
    #    print(list(model.model_fields))

    test = make_configuration_profile(payload_registry)
    # pprint(test)
    # test = create_model(
    #    "ConfigurationProfile",
    #    __config__=ConfigDict(extra="forbid", populate_by_name=True),
    #    test=test,
    # )
    # pprint(test.model_json_schema(True, ref_template="#/$defs/{model}"))
    with open("test.schema.json", "w") as f:
        json.dump(
            test.model_json_schema(True, ref_template="#/$defs/{model}"), f, indent=2
        )
    pprint(test.model_json_schema(True, ref_template="#/$defs/{model}"))


if __name__ == "__main__":
    main()
