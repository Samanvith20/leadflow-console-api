from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.lead import CrmSyncStatus, LeadStatus, QualificationStatus


class LeadRead(BaseModel):
    """The lead data safe to return to an authorised workspace user."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    contact_id: UUID | None
    intake_event_id: UUID
    assignee_user_id: UUID | None
    enquiry_message: str | None
    custom_fields: dict[str, Any]
    lead_status: LeadStatus
    qualification_status: QualificationStatus
    qualification_reason: str | None
    crm_sync_status: CrmSyncStatus
    created_at: datetime
    updated_at: datetime


class LeadUpdate(BaseModel):
    """Human-controlled changes; AI qualification and CRM sync have separate jobs."""

    assignee_user_id: UUID | None = None
    lead_status: LeadStatus | None = None
    enquiry_message: str | None = Field(default=None, max_length=20_000)
    custom_fields: dict[str, Any] | None = None
