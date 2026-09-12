from pydantic import BaseModel, ConfigDict, Field
from enum import StrEnum

type YAMLScalar = str | bool | int | float


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
    valuetype: str | None = None
    presence: Presence = Presence.OPTIONAL
    rangelist: list[YAMLScalar] | None = None
    range: object | None = None  # TODO: Create object
    default: YAMLScalar | None = None
    format: str | None = None
    repetition: object | None = None  # TODO: Create object
    combinetype: str | None = None
    content: str | None = None
    subkeytype: str | None = None
    subkeys: list[PayloadKey] | None = None


class SchemaDocument(SchemaModel):
    title: str
    description: str | None
    payload: ProfilePayload
    payloadkeys: list[PayloadKey] = Field(default_factory=list)
    notes: object | None = None
