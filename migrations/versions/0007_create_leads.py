"""Create leads.

Revision ID: 0007_create_leads
Revises: 0006_create_intake_events
Create Date: 2026-11-13
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007_create_leads"
down_revision = "0006_create_intake_events"
branch_labels = None
depends_on = None

lead_status = postgresql.ENUM(
    "new", "in_progress", "contacted", "closed_won", "closed_lost", name="lead_status", create_type=False
)
qualification_status = postgresql.ENUM(
    "pending", "hot", "warm", "needs_review", "not_a_fit", name="qualification_status", create_type=False
)
crm_sync_status = postgresql.ENUM(
    "not_required", "pending", "synced", "failed", name="crm_sync_status", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    lead_status.create(bind, checkfirst=True)
    qualification_status.create(bind, checkfirst=True)
    crm_sync_status.create(bind, checkfirst=True)
    op.create_table(
        "leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("intake_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assignee_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("enquiry_message", sa.Text(), nullable=True),
        sa.Column(
            "custom_fields",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("lead_status", lead_status, nullable=False, server_default=sa.text("'new'")),
        sa.Column(
            "qualification_status",
            qualification_status,
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("qualification_reason", sa.Text(), nullable=True),
        sa.Column(
            "crm_sync_status",
            crm_sync_status,
            nullable=False,
            server_default=sa.text("'not_required'"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "qualification_reason IS NULL OR qualification_reason <> ''",
            name="ck_leads_qualification_reason_not_blank",
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["intake_event_id"], ["intake_events.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assignee_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("intake_event_id", name="uq_leads_intake_event_id"),
    )
    op.create_index("ix_leads_workspace_id", "leads", ["workspace_id"], unique=False)
    op.create_index("ix_leads_contact_id", "leads", ["contact_id"], unique=False)
    op.create_index("ix_leads_assignee_user_id", "leads", ["assignee_user_id"], unique=False)
    op.create_index(
        "ix_leads_workspace_assignee_status",
        "leads",
        ["workspace_id", "assignee_user_id", "lead_status"],
        unique=False,
    )
    op.create_index(
        "ix_leads_workspace_qualification_created",
        "leads",
        ["workspace_id", "qualification_status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_leads_workspace_qualification_created", table_name="leads")
    op.drop_index("ix_leads_workspace_assignee_status", table_name="leads")
    op.drop_index("ix_leads_assignee_user_id", table_name="leads")
    op.drop_index("ix_leads_contact_id", table_name="leads")
    op.drop_index("ix_leads_workspace_id", table_name="leads")
    op.drop_table("leads")
    bind = op.get_bind()
    crm_sync_status.drop(bind, checkfirst=True)
    qualification_status.drop(bind, checkfirst=True)
    lead_status.drop(bind, checkfirst=True)
