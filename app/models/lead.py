import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import LowercaseEnum, enum_values


class LeadStatus(LowercaseEnum):
    """The sales-work state of an enquiry that passed intake validation."""

    NEW = "new"
    IN_PROGRESS = "in_progress"
    CONTACTED = "contacted"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class QualificationStatus(LowercaseEnum):
    """The outcome of Leadflow's deterministic rules and AI-assisted review."""

    PENDING = "pending"
    HOT = "hot"
    WARM = "warm"
    NEEDS_REVIEW = "needs_review"
    NOT_A_FIT = "not_a_fit"


class CrmSyncStatus(LowercaseEnum):
    """A compact current state for the lead's eventual CRM sync."""

    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"


class Lead(Base):
    """A usable enquiry created only after its intake event passes basic validation."""

    __tablename__ = "leads"
    __table_args__ = (
        CheckConstraint(
            "qualification_reason IS NULL OR qualification_reason <> ''",
            name="ck_leads_qualification_reason_not_blank",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    intake_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("intake_events.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    assignee_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    enquiry_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    custom_fields: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    lead_status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus, name="lead_status", values_callable=enum_values),
        nullable=False,
        default=LeadStatus.NEW,
        server_default=text("'new'"),
    )
    qualification_status: Mapped[QualificationStatus] = mapped_column(
        Enum(QualificationStatus, name="qualification_status", values_callable=enum_values),
        nullable=False,
        default=QualificationStatus.PENDING,
        server_default=text("'pending'"),
    )
    qualification_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    crm_sync_status: Mapped[CrmSyncStatus] = mapped_column(
        Enum(CrmSyncStatus, name="crm_sync_status", values_callable=enum_values),
        nullable=False,
        default=CrmSyncStatus.NOT_REQUIRED,
        server_default=text("'not_required'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
