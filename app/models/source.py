import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import LowercaseEnum, enum_values


class SourceType(LowercaseEnum):
    WEBSITE_FORM = "website_form"
    META = "meta"
    GENERIC_WEBHOOK = "generic_webhook"
    CSV_IMPORT = "csv_import"
    MANUAL_ENTRY = "manual_entry"
    WEB_CHAT = "web_chat"
    WHATSAPP = "whatsapp"


class SourceStatus(LowercaseEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Source(Base):
    """A workspace intake channel and its webhook security/configuration boundary."""

    __tablename__ = "sources"
    __table_args__ = (UniqueConstraint("workspace_id", "name", name="uq_sources_workspace_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="source_type", values_callable=enum_values), nullable=False
    )
    public_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    webhook_secret_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SourceStatus] = mapped_column(
        Enum(SourceStatus, name="source_status", values_callable=enum_values),
        nullable=False,
        default=SourceStatus.ACTIVE,
        server_default=text("'active'"),
    )
    configuration: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
