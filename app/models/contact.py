import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Contact(Base):
    """A person or business representative, shared by one or more leads."""

    __tablename__ = "contacts"
    __table_args__ = (
        CheckConstraint(
            "full_name IS NOT NULL OR email IS NOT NULL OR phone_e164 IS NOT NULL",
            name="ck_contacts_has_identity",
        ),
        CheckConstraint(
            "email IS NULL OR email = lower(email)", name="ck_contacts_email_lowercase"
        ),
        CheckConstraint(
            "phone_e164 IS NULL OR phone_e164 ~ '^\\+[1-9][0-9]{6,14}$'",
            name="ck_contacts_phone_e164",
        ),
        UniqueConstraint("workspace_id", "email", name="uq_contacts_workspace_email"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone_e164: Mapped[str | None] = mapped_column(String(16), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
