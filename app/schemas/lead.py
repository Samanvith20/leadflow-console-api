from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.lead import CrmSyncStatus, LeadStatus, QualificationStatus
from app.models.source import SourceType
from app.models.user import UserRole


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


class LeadContactSummary(BaseModel):
    """Contact identity included beside a lead without exposing unrelated workspace data."""

    id: UUID
    full_name: str | None
    email: str | None
    phone_e164: str | None
    company_name: str | None


class LeadAssigneeSummary(BaseModel):
    """The active workspace user currently responsible for a lead, if any."""

    id: UUID
    name: str
    email: str
    role: UserRole


class LeadSourceSummary(BaseModel):
    """The intake source that created a lead."""

    id: UUID
    name: str
    source_type: SourceType


class LeadSummaryRead(BaseModel):
    """Lead data needed in the list and Manager overview without extra client-side joins."""

    id: UUID
    contact: LeadContactSummary | None
    source: LeadSourceSummary
    assignee: LeadAssigneeSummary | None
    enquiry_message: str | None
    lead_status: LeadStatus
    qualification_status: QualificationStatus
    created_at: datetime
    updated_at: datetime


class LeadDetailRead(LeadSummaryRead):
    """The complete safe lead view used by the Lead detail screen."""

    custom_fields: dict[str, Any]
    qualification_reason: str | None
    crm_sync_status: CrmSyncStatus


class LeadListResponse(BaseModel):
    """A paginated lead list with a stable total for the current filters."""

    items: list[LeadSummaryRead]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
