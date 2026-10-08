"""Convert Apple's profile schema documents into one JSON Schema (draft-07).

Layout of the result:

* the document root is the profile envelope (TopLevel.yaml)
* ``PayloadContent`` items are validated by ``#/$defs/Payload``: the common
  payload keys, plus one ``if PayloadType == X then <schema for X>`` per Apple
  payload type. A PayloadType Apple doesn't define matches no ``if`` and so is
  only held to the common keys - custom payloads are allowed.
"""

import re
from typing import Any

SCHEMA_URI = "http://json-schema.org/draft-07/schema#"
ANY_KEY = "ANY"  # Apple's marker for "any key name is allowed here"

SCALAR_TYPES = {
    "<boolean>": {"type": "boolean"},
    "<string>": {"type": "string"},
    "<integer>": {"type": "integer"},
    "<real>": {"type": "number"},
    "<date>": {"type": "string", "format": "date-time"},
    "<data>": {"type": "string", "contentEncoding": "base64"},
}
CONTAINER_TYPES = {"<array>": "array", "<dictionary>": "object"}
VALUETYPE_FORMATS = {"<hostname>": "hostname", "<url>": "uri"}


class Converter:
    def __init__(self, *, strict: bool = True):
        self.strict = strict
        self.common_keys: set[str] = set()
        self.common_required: list[str] = []

    # -- keys -------------------------------------------------------------

    def key_schema(self, key: dict, stack: frozenset[int] = frozenset()) -> dict:
        """Schema for the value of one `payloadkeys` entry."""
        kind = key["type"]
        if kind == "<any>":
            schema: dict[str, Any] = {}
        elif kind in SCALAR_TYPES:
            schema = dict(SCALAR_TYPES[kind])
        elif kind in CONTAINER_TYPES:
            schema = {"type": CONTAINER_TYPES[kind]}
            # A subkey tree that loops back on itself (YAML aliases) can't be
            # inlined; stay open at the point of recursion.
            if id(key) not in stack:
                inner = stack | {id(key)}
                if kind == "<array>":
                    self._array(schema, key, inner)
                else:
                    self._object(schema, key.get("subkeys") or [], inner)
        else:
            raise ValueError(f"unknown type {kind!r} for key {key['key']!r}")

        self._constraints(schema, key)
        return schema

    def _constraints(self, schema: dict, key: dict) -> None:
        if key.get("title"):
            schema["title"] = key["title"]
        if key.get("content"):
            schema["description"] = key["content"]
            schema["markdownDescription"] = key["content"]
        if "default" in key:
            schema["default"] = key["default"]
        if "rangelist" in key:
            schema["enum"] = key["rangelist"]
        if rng := key.get("range"):
            if "min" in rng:
                schema["minimum"] = rng["min"]
            if "max" in rng:
                schema["maximum"] = rng["max"]
        if rep := key.get("repetition"):
            if "min" in rep:
                schema["minItems"] = rep["min"]
            if "max" in rep:
                schema["maxItems"] = rep["max"]
        if key.get("format"):
            schema["pattern"] = key["format"]
        if key.get("valuetype") in VALUETYPE_FORMATS:
            schema["format"] = VALUETYPE_FORMATS[key["valuetype"]]
        if self._deprecated(key):
            schema["deprecated"] = True

    @staticmethod
    def _deprecated(key: dict) -> bool:
        oses = [
            v
            for v in (key.get("supportedOS") or {}).values()
            if v.get("introduced") != "n/a"
        ]
        return bool(oses) and all("deprecated" in v for v in oses)

    def _array(self, schema: dict, key: dict, stack: frozenset[int]) -> None:
        subkeys = key.get("subkeys") or []
        # Apple describes the element type as the array's single subkey.
        if subkeys:
            schema["items"] = self.key_schema(subkeys[0], stack)

    def _object(self, schema: dict, subkeys: list[dict], stack: frozenset[int]) -> None:
        properties, required, extra = self.properties(subkeys, stack)
        if properties:
            schema["properties"] = properties
        if required:
            schema["required"] = required
        if extra is not None:
            schema["additionalProperties"] = extra
        elif subkeys and self.strict:
            schema["additionalProperties"] = False

    def properties(
        self, keys: list[dict], stack: frozenset[int] = frozenset()
    ) -> tuple[dict, list[str], dict | bool | None]:
        """(properties, required, additionalProperties-or-None) for a key list."""
        properties: dict[str, dict] = {}
        required: list[str] = []
        extra: dict | bool | None = None
        for key in keys:
            if key["key"] == ANY_KEY:
                extra = self.key_schema(key, stack) or True
                continue
            properties[key["key"]] = self.key_schema(key, stack)
            if key.get("presence") == "required":
                required.append(key["key"])
        return properties, required, extra

    # -- payloads ---------------------------------------------------------

    def payload_schema(self, doc: dict) -> dict:
        """Schema for one payload dictionary of an Apple payload type."""
        keys = [k for k in doc["payloadkeys"] if k["key"] not in self.common_keys]
        properties, required, extra = self.properties(keys)
        payload_type = doc["payload"]["payloadtype"]

        properties = {
            **{k: {"$ref": f"#/$defs/CommonKeys/properties/{k}"} for k in sorted(self.common_keys)},
            **properties,
            "PayloadType": {"const": payload_type},
        }
        schema: dict[str, Any] = {
            "title": doc["title"],
            "description": doc.get("description"),
            "type": "object",
            "properties": properties,
            "required": sorted({*self.common_required, *required}),
        }
        if extra is not None:
            schema["additionalProperties"] = extra
        elif self.strict:
            schema["additionalProperties"] = False
        return {k: v for k, v in schema.items() if v is not None}

    def build(self, top_level: dict, common: dict, payloads: dict[str, list[dict]]):
        common_props, common_required, _ = self.properties(common["payloadkeys"])
        self.common_keys = set(common_props)
        self.common_required = common_required

        defs: dict[str, dict] = {
            "CommonKeys": {"type": "object", "properties": common_props}
        }
        branches: list[dict] = []
        for payload_type in sorted(payloads):
            names = []
            for doc in payloads[payload_type]:
                # Same payload type split over several files (com.apple.MCX):
                # each file is an alternative shape for the type.
                name = _def_name(doc["_file"])
                defs[name] = self.payload_schema(doc)
                names.append({"$ref": f"#/$defs/{name}"})
            then = names[0] if len(names) == 1 else {"anyOf": names}
            branches.append(
                {
                    "if": {
                        "properties": {"PayloadType": {"const": payload_type}},
                        "required": ["PayloadType"],
                    },
                    "then": then,
                }
            )

        defs["Payload"] = {
            "description": "A payload. Apple-defined PayloadTypes are validated "
            "against their schema; any other PayloadType is accepted with "
            "only the common payload keys checked.",
            "type": "object",
            "properties": {
                **{k: {"$ref": f"#/$defs/CommonKeys/properties/{k}"} for k in common_props},
                "PayloadType": {
                    "type": "string",
                    "description": common_props["PayloadType"].get("description"),
                    "examples": sorted(payloads),
                },
            },
            "required": common_required,
            "allOf": branches,
        }

        top_props, top_required, _ = self.properties(top_level["payloadkeys"])
        # Apple's PayloadContent element is "ANY"; replace with the real thing.
        top_props["PayloadContent"] = {
            **{k: v for k, v in top_props["PayloadContent"].items() if k != "items"},
            "items": {"$ref": "#/$defs/Payload"},
        }
        return {
            "$schema": SCHEMA_URI,
            "title": "Apple configuration profile",
            "description": "Generated from apple/device-management.",
            "type": "object",
            "properties": top_props,
            "required": top_required,
            "additionalProperties": not self.strict,
            "$defs": defs,
        }


def _def_name(file_stem: str) -> str:
    """Make a file stem such as 'com.apple.MCX(WiFi)' safe inside a $ref."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", file_stem)


def convert(top_level: dict, common: dict, payloads: dict, *, strict: bool = True):
    return Converter(strict=strict).build(top_level, common, payloads)
