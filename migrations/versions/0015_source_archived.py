"""Add archived source status.

Revision ID: 0015_source_archived
Revises: 0014_workspace_onboarding
"""

from alembic import op

revision = "0015_source_archived"
down_revision = "0014_workspace_onboarding"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE source_status ADD VALUE IF NOT EXISTS 'archived'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely without rebuilding the type.
    pass
