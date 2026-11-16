from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class ContactCreate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    email: EmailStr | None = None
    phone_e164: str | None = Field(default=None, pattern=r"^\+[1-9][0-9]{6,14}$")
    company_name: str | None = Field(default=None, min_length=1, max_length=200)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr | None) -> str | None:
        return str(value).lower() if value is not None else None

    @model_validator(mode="after")
    def require_an_identity(self) -> "ContactCreate":
        if self.full_name is None and self.email is None and self.phone_e164 is None:
            raise ValueError("A contact needs at least a name, email, or phone number")
        return self


class ContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    full_name: str | None
    email: EmailStr | None
    phone_e164: str | None
    company_name: str | None
    created_at: datetime
    updated_at: datetime
