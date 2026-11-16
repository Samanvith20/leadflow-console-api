"""Create background jobs.

Revision ID: 0008_create_background_jobs
Revises: 0007_create_leads
Create Date: 2026-11-13
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008_create_background_jobs"
down_revision = "0007_create_leads"
branch_labels = None
depends_on = None

job_type = postgresql.ENUM(
    "process_intake", "qualify_lead", "generate_reply", "sync_crm", name="job_type", create_type=False
)
job_status = postgresql.ENUM(
    "queued", "running", "succeeded", "retry_scheduled", "failed", name="job_status", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    job_type.create(bind, checkfirst=True)
    job_status.create(bind, checkfirst=True)
    op.create_table(
        "background_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("intake_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("job_type", job_type, nullable=False),
        sa.Column("status", job_status, nullable=False, server_default=sa.text("'queued'")),
        sa.Column("job_key", sa.String(length=200), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.Column("run_after", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(length=100), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("attempts >= 0", name="ck_background_jobs_attempts_nonnegative"),
        sa.CheckConstraint("max_attempts > 0", name="ck_background_jobs_max_attempts_positive"),
        sa.CheckConstraint("attempts <= max_attempts", name="ck_background_jobs_attempts_within_limit"),
        sa.CheckConstraint(
            "(job_type = 'process_intake' AND intake_event_id IS NOT NULL AND lead_id IS NULL) "
            "OR (job_type <> 'process_intake' AND lead_id IS NOT NULL)",
            name="ck_background_jobs_target_matches_type",
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["intake_event_id"], ["intake_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "job_key", name="uq_background_jobs_workspace_job_key"),
    )
    op.create_index("ix_background_jobs_workspace_id", "background_jobs", ["workspace_id"], unique=False)
    op.create_index("ix_background_jobs_intake_event_id", "background_jobs", ["intake_event_id"], unique=False)
    op.create_index("ix_background_jobs_lead_id", "background_jobs", ["lead_id"], unique=False)
    op.create_index("ix_background_jobs_run_after", "background_jobs", ["run_after"], unique=False)
    op.create_index(
        "ix_background_jobs_status_run_after",
        "background_jobs",
        ["status", "run_after"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_background_jobs_status_run_after", table_name="background_jobs")
    op.drop_index("ix_background_jobs_run_after", table_name="background_jobs")
    op.drop_index("ix_background_jobs_lead_id", table_name="background_jobs")
    op.drop_index("ix_background_jobs_intake_event_id", table_name="background_jobs")
    op.drop_index("ix_background_jobs_workspace_id", table_name="background_jobs")
    op.drop_table("background_jobs")
    bind = op.get_bind()
    job_status.drop(bind, checkfirst=True)
    job_type.drop(bind, checkfirst=True)
