"""Create workspaces.

Revision ID: 0001_create_workspaces
Revises:
Create Date: 2026-11-13
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_create_workspaces"
down_revision = None
branch_labels = None
depends_on = None

workspace_status = postgresql.ENUM(
    "active", "paused", name="workspace_status", create_type=False
)


def upgrade() -> None:
    workspace_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("status", workspace_status, nullable=False, server_default=sa.text("'active'")),
        sa.Column(
            "configuration",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("workspaces")
    workspace_status.drop(op.get_bind(), checkfirst=True)
