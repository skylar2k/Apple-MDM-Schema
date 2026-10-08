#!/usr/bin/env python
"""Generate a single JSON Schema for configuration profiles (as YAML or JSON)
from the schemas in apple/device-management."""

import argparse
import json
import pathlib

from schema_parser import convert, load_profiles

DEFAULT_SOURCE = pathlib.Path("device-management/mdm/profiles")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=pathlib.Path, default=DEFAULT_SOURCE)
    parser.add_argument("-o", "--output", type=pathlib.Path, default="profile.schema.json")
    parser.add_argument(
        "--lax",
        action="store_true",
        help="allow keys Apple's schema doesn't list (default: reject them, to catch typos)",
    )
    args = parser.parse_args()

    top_level, common, payloads = load_profiles(args.source.glob("*.yaml"))
    schema = convert(top_level, common, payloads, strict=not args.lax)
    args.output.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n")
    print(f"{args.output}: {len(payloads)} Apple payload types")


if __name__ == "__main__":
    main()
