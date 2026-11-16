"""Create auth tokens.

Revision ID: 0012_create_auth_tokens
Revises: 0011_create_integrations
Create Date: 2026-11-15
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0012_create_auth_tokens"
down_revision = "0011_create_integrations"
branch_labels = None
depends_on = None

auth_token_purpose = postgresql.ENUM(
    "password_reset", "email_verification", name="auth_token_purpose", create_type=False
)


def upgrade() -> None:
    auth_token_purpose.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "auth_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("purpose", auth_token_purpose, nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("char_length(token_hash) = 64", name="ck_auth_tokens_token_hash_length"),
        sa.CheckConstraint("expires_at > created_at", name="ck_auth_tokens_expiry_after_creation"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_auth_tokens_user_id", "auth_tokens", ["user_id"], unique=False)
    op.create_index("ix_auth_tokens_expires_at", "auth_tokens", ["expires_at"], unique=False)
    op.create_index(
        "ix_auth_tokens_user_purpose_created",
        "auth_tokens",
        ["user_id", "purpose", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_auth_tokens_user_purpose_created", table_name="auth_tokens")
    op.drop_index("ix_auth_tokens_expires_at", table_name="auth_tokens")
    op.drop_index("ix_auth_tokens_user_id", table_name="auth_tokens")
    op.drop_table("auth_tokens")
    auth_token_purpose.drop(op.get_bind(), checkfirst=True)
