from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: UserRole = UserRole.USER
    is_available: bool = True
    max_open_leads: int = Field(default=10, ge=0, le=10_000)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    is_available: bool
    max_open_leads: int
    email_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime
