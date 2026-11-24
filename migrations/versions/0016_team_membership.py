"""Add invitation lifecycle state for workspace team members.

Revision ID: 0016_team_membership
Revises: 0015_source_archived
"""

import sqlalchemy as sa
from alembic import op

revision = "0016_team_membership"
down_revision = "0015_source_archived"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE auth_token_purpose ADD VALUE IF NOT EXISTS 'team_invitation'")
    op.add_column("users", sa.Column("invited_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "users", sa.Column("invitation_accepted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("users", sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "deactivated_at")
    op.drop_column("users", "invitation_accepted_at")
    op.drop_column("users", "invited_at")
    # PostgreSQL enum values cannot be removed safely without rebuilding the type.
