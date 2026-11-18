from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.user import UserRead
from app.schemas.workspace import WorkspaceRead


class RegisterRequest(BaseModel):
    """The public first-manager registration payload; role and workspace status are server controlled."""

    workspace_name: str = Field(min_length=1, max_length=150)
    timezone: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class PasswordResetRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=32, max_length=512)
    new_password: str = Field(min_length=12, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=32, max_length=512)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class AuthenticatedUserResponse(BaseModel):
    user: UserRead
    workspace: WorkspaceRead


class MessageResponse(BaseModel):
    message: str


class EmailVerificationResponse(BaseModel):
    email_verified_at: datetime
