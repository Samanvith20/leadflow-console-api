from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.reply_draft import ReplyDraftStatus


class ReplyDraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    lead_id: UUID
    subject: str | None
    body: str
    status: ReplyDraftStatus
    approved_by_user_id: UUID | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ReplyDraftUpdate(BaseModel):
    subject: str | None = Field(default=None, min_length=1, max_length=250)
    body: str | None = Field(default=None, min_length=1, max_length=20_000)
