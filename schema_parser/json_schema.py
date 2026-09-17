from typing import Annotated, Any, Literal, Union

from devtools import pprint
from pydantic import BaseModel, WithJsonSchema, create_model
from pydantic.config import JsonDict
from pydantic_core.core_schema import JsonSchema

from .models import *


class CommonPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    PayloadIdentifier: str = Field(alias="PayloadIdentifier")
    PayloadUUID: str = Field(alias="PayloadUUID")
    PayloadVersion: int = Field(alias="PayloadVersion")


TYPE_FORMAT: dict[TypeKind, dict[str, str]] = {
    TypeKind.DATE: {"format": "date-time"},
    TypeKind.DATA: {"format": "base64"},
}


def python_type_for_key(key: PayloadKey) -> Any:
    match key.type:
        case TypeKind.BOOLEAN:
            return bool

        case TypeKind.STRING | TypeKind.DATE | TypeKind.DATA:
            return str

        case TypeKind.INTEGER:
            return int

        case TypeKind.REAL:
            return float

        case TypeKind.ARRAY:
            # if key.subkeys:
            #    item_model = model_from_payload_keys(
            #        key.subkeys,
            #        payload_type=f"{key.key}Item",
            #        model_name=f"{key.key}Item",
            #    )
            #    return list[item_model]

            return list[Any]

        case TypeKind.DICTIONARY:
            # if key.subkeys:
            #    return model_from_payload_keys(
            #        key.subkeys,
            #        payload_type=f"{key.key}Dictionary",
            #        model_name=f"{key.key}Dictionary",
            #    )

            return dict[str, Any]

        case TypeKind.ANY:
            return Any


def model_from_payload_keys(
    payload_keys: list[PayloadKey], *, payload_type: str, model_name: str
) -> type[BaseModel]:
    fields: dict[str, Any] = {}

    for payload_key in payload_keys:
        field_type = python_type_for_key(payload_key)
        if payload_key.type in ["<DATE>", "<DATA>"]:
            type_format = TYPE_FORMAT[payload_key.type]
        else:
            type_format = {}
        fields[payload_key.key] = (
            field_type,
            Field(
                default=payload_key.default,
                alias=payload_key.key,
                description=payload_key.content,
                json_schema_extra=JsonDict(type_format),
            ),
        )

    # Override PayloadType with a discriminator-specific Literal.
    fields["PayloadType"] = (
        Literal[payload_type],
        Field(
            default=payload_type,
            alias="PayloadType",
        ),
    )
    return create_model(
        model_name,
        __base__=CommonPayload,
        **fields,
    )


def make_payload_union(payloads: dict[str, type[BaseModel]]):
    models = tuple(payloads.values())

    if not models:
        raise ValueError("No payload models found")

    return Annotated[Union[models], Field(discriminator="PayloadType")]


def make_configuration_profile(payloads: dict[str, type[BaseModel]]):
    payload_union = make_payload_union(payloads)
    # pprint(payload_union)

    return create_model(
        "ConfigurationProfile",
        __config__=ConfigDict(
            extra="forbid",
            populate_by_name=True,
        ),
        __module__="apple_mdm.generated",
        PayloadDisplayName=(
            str | None,
            Field(default=None, alias="PayloadDisplayName"),
        ),
        PayloadIdentifier=(str, Field(alias="PayloadIdentifier")),
        PayloadUUID=(str, Field(alias="PayloadIdentifier")),
        PayloadVersion=(int, Field(alias="PayloadVersion")),
        PayloadType=(
            Literal["Configuration"],
            Field(
                default="Configuration",
                alias="PayloadType",
            ),
        ),
        PayloadContent=(list[payload_union], Field(alias="PayloadContent")),
    )
