import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import LowercaseEnum, enum_values


class ReplyDraftStatus(LowercaseEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    DISCARDED = "discarded"


class ReplyDraft(Base):
    """The single current, editable reply draft for one lead in the MVP."""

    __tablename__ = "reply_drafts"
    __table_args__ = (
        CheckConstraint("body <> ''", name="ck_reply_drafts_body_not_blank"),
        CheckConstraint(
            "subject IS NULL OR subject <> ''", name="ck_reply_drafts_subject_not_blank"
        ),
        CheckConstraint(
            "status <> 'approved' OR (approved_by_user_id IS NOT NULL AND approved_at IS NOT NULL)",
            name="ck_reply_drafts_approval_details",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    subject: Mapped[str | None] = mapped_column(String(250), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ReplyDraftStatus] = mapped_column(
        Enum(ReplyDraftStatus, name="reply_draft_status", values_callable=enum_values),
        nullable=False,
        default=ReplyDraftStatus.DRAFT,
        server_default=text("'draft'"),
    )
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
