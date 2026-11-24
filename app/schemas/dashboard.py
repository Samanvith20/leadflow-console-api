"""Dashboard response models built from real workspace lead and audit data."""

from pydantic import BaseModel, Field

from app.schemas.audit_event import AuditEventRead
from app.schemas.lead import LeadSummaryRead


class DashboardMetrics(BaseModel):
    """Counts that help a Manager decide what needs attention now."""

    new_leads: int = Field(ge=0)
    unassigned_leads: int = Field(ge=0)
    awaiting_qualification: int = Field(ge=0)
    reply_drafts_waiting_approval: int = Field(ge=0)


class DashboardRead(BaseModel):
    """Manager overview data sourced only from the current workspace."""

    metrics: DashboardMetrics
    needs_attention: list[LeadSummaryRead]
    recent_activity: list[AuditEventRead]
