#!/usr/bin/env python

import pathlib
import pprint
from schema_parser import parse_schema, SchemaDocument

APPLE_SCHEMA_PATH: pathlib.Path = pathlib.Path("./mdm/profiles/")


def main():
    profiles: dict[str, SchemaDocument] = {}
    for file in APPLE_SCHEMA_PATH.rglob("*.yaml"):
        with open(file) as f:
            profile = parse_schema(f.read())
            profiles[profile.payload.payloadtype] = profile

    pprint.pprint(profiles)


if __name__ == "__main__":
    main()
