"""Add workspace onboarding state.

Revision ID: 0014_workspace_onboarding
Revises: 0013_add_auth_lifecycle_columns
Create Date: 2026-11-16
"""

import sqlalchemy as sa
from alembic import op

revision = "0014_workspace_onboarding"
down_revision = "0013_add_auth_lifecycle_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Track completion separately from flexible onboarding draft data in configuration JSONB."""
    op.add_column(
        "workspaces", sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("workspaces", "onboarding_completed_at")
