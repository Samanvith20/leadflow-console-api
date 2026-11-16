"""Create integrations.

Revision ID: 0011_create_integrations
Revises: 0010_create_audit_events
Create Date: 2026-11-15
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0011_create_integrations"
down_revision = "0010_create_audit_events"
branch_labels = None
depends_on = None

integration_provider = postgresql.ENUM("hubspot", name="integration_provider", create_type=False)
integration_status = postgresql.ENUM(
    "connected", "disabled", "error", name="integration_status", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    integration_provider.create(bind, checkfirst=True)
    integration_status.create(bind, checkfirst=True)
    op.create_table(
        "integrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", integration_provider, nullable=False),
        sa.Column("external_account_id", sa.String(length=200), nullable=True),
        sa.Column("credentials_ciphertext", sa.Text(), nullable=False),
        sa.Column(
            "configuration",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("status", integration_status, nullable=False, server_default=sa.text("'connected'")),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "credentials_ciphertext <> ''", name="ck_integrations_credentials_not_blank"
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "provider", name="uq_integrations_workspace_provider"),
    )
    op.create_index("ix_integrations_workspace_id", "integrations", ["workspace_id"], unique=False)
    op.create_index(
        "ix_integrations_workspace_status",
        "integrations",
        ["workspace_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_integrations_workspace_status", table_name="integrations")
    op.drop_index("ix_integrations_workspace_id", table_name="integrations")
    op.drop_table("integrations")
    bind = op.get_bind()
    integration_status.drop(bind, checkfirst=True)
    integration_provider.drop(bind, checkfirst=True)
