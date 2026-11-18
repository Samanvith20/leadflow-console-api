import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
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


class IntakeEventStatus(LowercaseEnum):
    PENDING = "pending"
    QUARANTINED = "quarantined"
    PROCESSED = "processed"
    FAILED = "failed"


class IntakeEvent(Base):
    """Durable, idempotent receipt of one source-delivered enquiry event."""

    __tablename__ = "intake_events"
    __table_args__ = (
        CheckConstraint("source_event_id <> ''", name="ck_intake_events_source_event_id_not_blank"),
        CheckConstraint("char_length(payload_hash) = 64", name="ck_intake_events_payload_hash_length"),
        UniqueConstraint("source_id", "source_event_id", name="uq_intake_events_source_event"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_event_id: Mapped[str] = mapped_column(String(200), nullable=False)
    raw_payload_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[IntakeEventStatus] = mapped_column(
        Enum(IntakeEventStatus, name="intake_event_status", values_callable=enum_values),
        nullable=False,
        default=IntakeEventStatus.PENDING,
        server_default=text("'pending'"),
    )
    mapping_warnings: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    purge_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
