import ruamel.yaml
from .models import SchemaDocument


def parse_schema(data: str) -> SchemaDocument:
    yaml = ruamel.yaml.YAML(typ="rt")
    data = yaml.load(data)

    return SchemaDocument.model_validate(data)
