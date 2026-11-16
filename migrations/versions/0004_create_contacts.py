"""Create contacts.

Revision ID: 0004_create_contacts
Revises: 0003_create_sessions
Create Date: 2026-11-13
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_create_contacts"
down_revision = "0003_create_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("phone_e164", sa.String(length=16), nullable=True),
        sa.Column("company_name", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "full_name IS NOT NULL OR email IS NOT NULL OR phone_e164 IS NOT NULL",
            name="ck_contacts_has_identity",
        ),
        sa.CheckConstraint("email IS NULL OR email = lower(email)", name="ck_contacts_email_lowercase"),
        sa.CheckConstraint(
            "phone_e164 IS NULL OR phone_e164 ~ '^\\+[1-9][0-9]{6,14}$'",
            name="ck_contacts_phone_e164",
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "email", name="uq_contacts_workspace_email"),
    )
    op.create_index("ix_contacts_workspace_id", "contacts", ["workspace_id"], unique=False)
    op.create_index(
        "ix_contacts_workspace_phone_e164",
        "contacts",
        ["workspace_id", "phone_e164"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_contacts_workspace_phone_e164", table_name="contacts")
    op.drop_index("ix_contacts_workspace_id", table_name="contacts")
    op.drop_table("contacts")
