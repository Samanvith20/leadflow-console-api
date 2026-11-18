import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import LowercaseEnum, enum_values


class JobType(LowercaseEnum):
    PROCESS_INTAKE = "process_intake"
    QUALIFY_LEAD = "qualify_lead"
    GENERATE_REPLY = "generate_reply"
    SYNC_CRM = "sync_crm"


class JobStatus(LowercaseEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    RETRY_SCHEDULED = "retry_scheduled"
    FAILED = "failed"


class BackgroundJob(Base):
    """A durable, retry-safe unit of work run outside the webhook request."""

    __tablename__ = "background_jobs"
    __table_args__ = (
        CheckConstraint("attempts >= 0", name="ck_background_jobs_attempts_nonnegative"),
        CheckConstraint("max_attempts > 0", name="ck_background_jobs_max_attempts_positive"),
        CheckConstraint("attempts <= max_attempts", name="ck_background_jobs_attempts_within_limit"),
        CheckConstraint(
            "(job_type = 'process_intake' AND intake_event_id IS NOT NULL AND lead_id IS NULL) "
            "OR (job_type <> 'process_intake' AND lead_id IS NOT NULL)",
            name="ck_background_jobs_target_matches_type",
        ),
        UniqueConstraint("workspace_id", "job_key", name="uq_background_jobs_workspace_job_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    intake_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("intake_events.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    job_type: Mapped[JobType] = mapped_column(
        Enum(JobType, name="job_type", values_callable=enum_values), nullable=False
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status", values_callable=enum_values),
        nullable=False,
        default=JobStatus.QUEUED,
        server_default=text("'queued'"),
    )
    job_key: Mapped[str] = mapped_column(String(200), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3, server_default=text("3")
    )
    run_after: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
