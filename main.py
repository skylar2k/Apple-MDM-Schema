#!/usr/bin/env python

import json
import pathlib
from devtools import pprint
from schema_parser import (
    parse_schema,
    SchemaDocument,
    # ProfileJsonSchema,
    model_from_payload_keys,
)

APPLE_SCHEMA_PATH: pathlib.Path = pathlib.Path("./mdm/profiles/")


def model_top_level(): ...


def main():
    profiles: dict[str, SchemaDocument] = {}
    for file in APPLE_SCHEMA_PATH.rglob("*.yaml"):
        with open(file) as f:
            profile = parse_schema(f.read())
            profiles[profile.payload.payloadtype] = profile

    # json_schema = ProfileJsonSchema(test={})
    # print(json.dumps(json_schema.model_json_schema()))
    # print(json.dumps(profiles["CommonPayloadKeys"].model_json_schema(), indent=2))
    # pprint(profiles["CommonPayloadKeys"])
    for profile in profiles:
        if profile in ["TopLevel", "CommonPayloadKeys", ".GlobalPreferences"]:
            continue

        schema = profiles[profile]
        payload_keys = model_from_payload_keys(
            schema.payloadkeys, payload_type=profile, model_name=profile
        )
        print(profile)
        print(json.dumps(payload_keys.model_json_schema(), indent=2))

    # print(
    #    json.dumps(
    #        model_from_payload_keys(
    #            profiles["TopLevel"].payloadkeys,
    #            payload_type=profiles["TopLevel"].payload.payloadtype,
    #            model_name="TopLevel",
    #        ).model_json_schema(),
    #        indent=2,
    #    )
    # )


if __name__ == "__main__":
    main()
