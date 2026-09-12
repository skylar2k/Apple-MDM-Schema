from dataclasses import dataclass, field
from pydantic import BaseModel, ConfigDict, Field
from enum import StrEnum


class SchemaModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class TypeKind(StrEnum):
    BOOLEAN = "<boolean>"
    STRING = "<string>"  # May include a valuetype key
    INTEGER = "<integer>"
    REAL = "<real>"
    DATE = "<date>"  # deprecated
    DATA = "<data>"
    ARRAY = "<array>"
    DICTIONARY = "<dictionary>"
    ANY = "<any>"


class Presence(StrEnum):
    REQUIRED = "required"
    OPTIONAL = "optional"


class Mode(StrEnum):
    ALLOWED = "allowed"
    REQUIRED = "required"
    FORBIDDEN = "forbidden"
    IGNORED = "ignored"


class SupportedOS(StrEnum):
    iOS = "iOS"
    macOS = "macOS"
    tvOS = "tvOS"
    visionOS = "visionOS"
    watchOS = "watchOS"


class SharedIpad(SchemaModel):
    mode: Mode | None = None
    devicechannel: bool | None = None
    userchannel: bool | None = None
    allowed_scopes: str | None = Field(default=None, alias="allowed-scopes")  # DDM


class UserEnrollment(SchemaModel):
    mode: Mode | None = None
    behavior: str | None = None


class PlatformKeys(SchemaModel):
    introduced: str | None = None
    deprecated: str | None = None
    removed: str | None = None
    accessrights: str | None = None
    multiple: bool | None = None
    devicechannel: bool | None = None
    userchannel: bool | None = None
    supervised: bool | None = None
    requires_dep: bool | None = None
    userapprovedmdm: bool | None = None
    allowmanualinstall: bool | None = None
    sharedipad: SharedIpad | None = None
    userenrollment: UserEnrollment | None = None
    always_skippable: bool | None = Field(
        default=None, alias="always-skippable"
    )  # Only usable in skipkeys.yaml
    allowed_enrollments: str | None = Field(
        default=None, alias="allowed-enrollments"
    )  # DDM
    allowed_scopes: str | None = Field(default=None, alias="allowed-scopes")  # DDM


class ProfilePayload(SchemaModel):
    payloadtype: str
    supportedOS: dict[SupportedOS, PlatformKeys]
    apply: str | None = None
    content: str | None = None


class PayloadKey(SchemaModel):
    key: str
    value_type: TypeKind = Field(alias="type")
    content: str | None
    presence: Presence
    # default: str | int | bool | float | None
    supportedOS: dict[SupportedOS, PlatformKeys] | None = None


class SchemaDocument(SchemaModel):
    title: str
    description: str | None
    payload: ProfilePayload
    payloadkeys: list[PayloadKey] = Field(default_factory=list)
