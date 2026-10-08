"""Load Apple's device-management profile schemas (YAML) as plain data."""

import pathlib
from collections import defaultdict
from collections.abc import Iterable

import ruamel.yaml


def load_document(path: pathlib.Path) -> dict:
    # Safe loader on purpose: Apple's files use anchors/aliases, and some of
    # them are recursive (e.g. homescreenlayout). Aliases give shared (and
    # sometimes cyclic) objects, which the converter has to cope with.
    doc = ruamel.yaml.YAML(typ="safe").load(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or "payload" not in doc or "payloadkeys" not in doc:
        raise ValueError(f"{path}: not an Apple profile schema document")
    doc["_file"] = path.stem
    return doc


def load_profiles(
    files: Iterable[pathlib.Path],
) -> tuple[dict, dict, dict[str, list[dict]]]:
    """Returns (top_level, common_payload_keys, payload_type -> [documents]).

    A payload type can be described by several files (com.apple.MCX has six),
    so every type maps to a list.
    """
    top_level: dict | None = None
    common: dict | None = None
    payloads: dict[str, list[dict]] = defaultdict(list)

    for file in sorted(files):
        doc = load_document(file)
        payload_type = doc["payload"]["payloadtype"]
        if payload_type == "TopLevel":
            top_level = doc
        elif payload_type == "CommonPayloadKeys":
            common = doc
        else:
            payloads[payload_type].append(doc)

    if top_level is None or common is None:
        raise ValueError("TopLevel.yaml / CommonPayloadKeys.yaml not found")
    return top_level, common, dict(payloads)
