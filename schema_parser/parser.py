import pathlib

import yaml
from .models import (
    SchemaDocument,
)


def parse_schema(data: str) -> SchemaDocument:
    raw: object = yaml.safe_load(data)

    if not isinstance(raw, dict):
        raise ValueError("The YAML document must contain a mapping")

    return SchemaDocument.model_validate(raw)
