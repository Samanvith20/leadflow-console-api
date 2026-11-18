"""Add auth lifecycle columns.

Revision ID: 0013_add_auth_lifecycle_columns
Revises: 0012_create_auth_tokens
Create Date: 2026-11-16
"""

import sqlalchemy as sa
from alembic import op

revision = "0013_add_auth_lifecycle_columns"
down_revision = "0012_create_auth_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("auth_tokens", sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "ix_auth_tokens_active_lookup",
        "auth_tokens",
        ["token_hash", "purpose", "expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_auth_tokens_active_lookup", table_name="auth_tokens")
    op.drop_column("auth_tokens", "invalidated_at")
    op.drop_column("users", "email_verified_at")
