"""Create sources.

Revision ID: 0005_create_sources
Revises: 0004_create_contacts
Create Date: 2026-11-13
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005_create_sources"
down_revision = "0004_create_contacts"
branch_labels = None
depends_on = None

source_type = postgresql.ENUM(
    "website_form",
    "meta",
    "generic_webhook",
    "csv_import",
    "manual_entry",
    "web_chat",
    "whatsapp",
    name="source_type",
    create_type=False,
)
source_status = postgresql.ENUM("active", "paused", name="source_status", create_type=False)


def upgrade() -> None:
    source_type.create(op.get_bind(), checkfirst=True)
    source_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("source_type", source_type, nullable=False),
        sa.Column("public_id", sa.String(length=64), nullable=False),
        sa.Column("webhook_secret_ciphertext", sa.Text(), nullable=True),
        sa.Column("status", source_status, nullable=False, server_default=sa.text("'active'")),
        sa.Column(
            "configuration",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint("workspace_id", "name", name="uq_sources_workspace_name"),
    )
    op.create_index("ix_sources_workspace_id", "sources", ["workspace_id"], unique=False)
    op.create_index("ix_sources_workspace_status", "sources", ["workspace_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sources_workspace_status", table_name="sources")
    op.drop_index("ix_sources_workspace_id", table_name="sources")
    op.drop_table("sources")
    source_status.drop(op.get_bind(), checkfirst=True)
    source_type.drop(op.get_bind(), checkfirst=True)
