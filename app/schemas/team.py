"""Request and response models for Manager-controlled workspace membership."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.user import UserRole

TeamMemberStatus = Literal["invited", "active", "deactivated"]


class InviteTeamMemberRequest(BaseModel):
    """Information a Manager supplies when inviting a standard workspace User."""

    name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    is_available: bool = True
    max_open_leads: int = Field(default=10, ge=0, le=10_000)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class AcceptTeamInvitationRequest(BaseModel):
    """One-use invitation token and the new User's chosen password."""

    token: str = Field(min_length=32, max_length=512)
    password: str = Field(min_length=12, max_length=128)


class TeamMemberUpdate(BaseModel):
    """Manager-editable operational details; role and email cannot be changed here."""

    name: str | None = Field(default=None, min_length=1, max_length=150)
    is_available: bool | None = None
    max_open_leads: int | None = Field(default=None, ge=0, le=10_000)

    @model_validator(mode="after")
    def require_a_change(self) -> "TeamMemberUpdate":
        if self.name is None and self.is_available is None and self.max_open_leads is None:
            raise ValueError("Provide at least one member field to update")
        return self


class TeamMemberRead(BaseModel):
    """Safe Manager view of one workspace member and their invitation lifecycle."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    email: EmailStr
    role: UserRole
    status: TeamMemberStatus
    is_available: bool
    max_open_leads: int
    invited_at: datetime | None
    invitation_accepted_at: datetime | None
    deactivated_at: datetime | None
    created_at: datetime
    updated_at: datetime
