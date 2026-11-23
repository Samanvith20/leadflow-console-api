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


class IntegrationProvider(LowercaseEnum):
    HUBSPOT = "hubspot"


class IntegrationStatus(LowercaseEnum):
    CONNECTED = "connected"
    DISABLED = "disabled"
    ERROR = "error"


class Integration(Base):
    """An encrypted connection between a workspace and an external CRM."""

    __tablename__ = "integrations"
    __table_args__ = (
        CheckConstraint(
            "credentials_ciphertext <> ''", name="ck_integrations_credentials_not_blank"
        ),
        UniqueConstraint("workspace_id", "provider", name="uq_integrations_workspace_provider"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[IntegrationProvider] = mapped_column(
        Enum(IntegrationProvider, name="integration_provider", values_callable=enum_values),
        nullable=False,
    )
    external_account_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    credentials_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    status: Mapped[IntegrationStatus] = mapped_column(
        Enum(IntegrationStatus, name="integration_status", values_callable=enum_values),
        nullable=False,
        default=IntegrationStatus.CONNECTED,
        server_default=text("'connected'"),
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
