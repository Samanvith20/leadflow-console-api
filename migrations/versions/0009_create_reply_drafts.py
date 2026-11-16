"""Create reply drafts.

Revision ID: 0009_create_reply_drafts
Revises: 0008_create_background_jobs
Create Date: 2026-11-13
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0009_create_reply_drafts"
down_revision = "0008_create_background_jobs"
branch_labels = None
depends_on = None

reply_draft_status = postgresql.ENUM(
    "draft", "approved", "discarded", name="reply_draft_status", create_type=False
)


def upgrade() -> None:
    reply_draft_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "reply_drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject", sa.String(length=250), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", reply_draft_status, nullable=False, server_default=sa.text("'draft'")),
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("body <> ''", name="ck_reply_drafts_body_not_blank"),
        sa.CheckConstraint("subject IS NULL OR subject <> ''", name="ck_reply_drafts_subject_not_blank"),
        sa.CheckConstraint(
            "status <> 'approved' OR (approved_by_user_id IS NOT NULL AND approved_at IS NOT NULL)",
            name="ck_reply_drafts_approval_details",
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lead_id", name="uq_reply_drafts_lead_id"),
    )
    op.create_index("ix_reply_drafts_workspace_id", "reply_drafts", ["workspace_id"], unique=False)
    op.create_index(
        "ix_reply_drafts_approved_by_user_id", "reply_drafts", ["approved_by_user_id"], unique=False
    )
    op.create_index(
        "ix_reply_drafts_workspace_status", "reply_drafts", ["workspace_id", "status"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_reply_drafts_workspace_status", table_name="reply_drafts")
    op.drop_index("ix_reply_drafts_approved_by_user_id", table_name="reply_drafts")
    op.drop_index("ix_reply_drafts_workspace_id", table_name="reply_drafts")
    op.drop_table("reply_drafts")
    reply_draft_status.drop(op.get_bind(), checkfirst=True)
