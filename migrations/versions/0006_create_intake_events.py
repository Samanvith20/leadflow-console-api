"""Create intake events.

Revision ID: 0006_create_intake_events
Revises: 0005_create_sources
Create Date: 2026-11-13
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006_create_intake_events"
down_revision = "0005_create_sources"
branch_labels = None
depends_on = None

intake_event_status = postgresql.ENUM(
    "pending", "quarantined", "processed", "failed", name="intake_event_status", create_type=False
)


def upgrade() -> None:
    intake_event_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "intake_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_event_id", sa.String(length=200), nullable=False),
        sa.Column("raw_payload_ciphertext", sa.Text(), nullable=True),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("status", intake_event_status, nullable=False, server_default=sa.text("'pending'")),
        sa.Column(
            "mapping_warnings",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("purge_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("source_event_id <> ''", name="ck_intake_events_source_event_id_not_blank"),
        sa.CheckConstraint("char_length(payload_hash) = 64", name="ck_intake_events_payload_hash_length"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "source_event_id", name="uq_intake_events_source_event"),
    )
    op.create_index("ix_intake_events_workspace_id", "intake_events", ["workspace_id"], unique=False)
    op.create_index("ix_intake_events_source_id", "intake_events", ["source_id"], unique=False)
    op.create_index("ix_intake_events_purge_at", "intake_events", ["purge_at"], unique=False)
    op.create_index(
        "ix_intake_events_workspace_status_received",
        "intake_events",
        ["workspace_id", "status", "received_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_intake_events_workspace_status_received", table_name="intake_events")
    op.drop_index("ix_intake_events_purge_at", table_name="intake_events")
    op.drop_index("ix_intake_events_source_id", table_name="intake_events")
    op.drop_index("ix_intake_events_workspace_id", table_name="intake_events")
    op.drop_table("intake_events")
    intake_event_status.drop(op.get_bind(), checkfirst=True)
