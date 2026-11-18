from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.source import SourceStatus, SourceType


class SourceFieldDefinition(BaseModel):
    """A customer-configured input field and its safe Leadflow mapping."""

    model_config = ConfigDict(extra="forbid")
    key: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")
    label: str = Field(min_length=1, max_length=100)
    field_type: Literal["string", "email", "phone", "number", "boolean", "date", "url", "enum"]
    required: bool = False
    maps_to: Literal["contact.full_name", "contact.email", "contact.phone_e164", "contact.company_name", "lead.enquiry_message", "lead.custom_fields"]
    options: list[str] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def validate_options(self) -> "SourceFieldDefinition":
        if self.field_type == "enum" and not self.options:
            raise ValueError("Enum fields require options")
        if self.field_type != "enum" and self.options:
            raise ValueError("Only enum fields may contain options")
        return self


class SourceConfiguration(BaseModel):
    """The allowlist used by the webhook receiver to validate dynamic data fields."""

    model_config = ConfigDict(extra="forbid")
    field_definitions: list[SourceFieldDefinition] = Field(default_factory=list, max_length=50)
    unknown_field_policy: Literal["reject"] = "reject"

    @model_validator(mode="after")
    def validate_unique_keys(self) -> "SourceConfiguration":
        if len({field.key for field in self.field_definitions}) != len(self.field_definitions):
            raise ValueError("Field keys must be unique")
        return self


class SourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    source_type: SourceType
    configuration: SourceConfiguration = Field(default_factory=SourceConfiguration)


class SourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    status: SourceStatus | None = None
    configuration: SourceConfiguration | None = None


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID; workspace_id: UUID; name: str; source_type: SourceType; public_id: str; status: SourceStatus
    configuration: dict; created_at: datetime; updated_at: datetime


class SourceCreated(SourceRead):
    webhook_url: str
    webhook_secret: str | None
