from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator
from enum import StrEnum

type YAMLScalar = str | bool | int | float
type NumericRange = Range[int] | Range[float]
IntOrFloat = TypeVar("IntOrFloat", int, float)


class SchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


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


class Range(SchemaModel, Generic[IntOrFloat]):
    min: IntOrFloat | None = None
    max: IntOrFloat | None = None

    @model_validator(mode="after")
    def validate_range(self):
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("min must be less than or equal to max")
        return self


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
    requiresdep: bool | None = None
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
    title: str | None = None
    supportedOS: dict[SupportedOS, PlatformKeys] | None = None
    type: TypeKind
    subtype: str | None = None  # Deprecated
    valuetype: str | None = None  # Only for strings
    presence: Presence = Presence.OPTIONAL
    rangelist: list[YAMLScalar] | None = None
    range: NumericRange | None = None
    default: YAMLScalar | None = None
    format: str | None = None
    repetition: NumericRange | None = None
    combinetype: str | None = None
    content: str | None = None
    subkeytype: str | None = None
    subkeys: list[PayloadKey] | None = None


class SchemaDocument(SchemaModel):
    title: str  # Title for this schema object
    description: str | None  # Description of this schema object
    payload: ProfilePayload  # Information about the object as a whole
    payloadkeys: list[
        PayloadKey
    ]  # A list of YAML objects representing the command request
    notes: object | None = None
