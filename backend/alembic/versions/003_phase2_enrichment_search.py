"""Phase 2 — IOCs, enrichment, DLQ, workflow, embeddings

Revision ID: 003
Revises: 002
Create Date: 2026-05-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("normalized_alerts", sa.Column("lifecycle_state", sa.String(50), server_default="new", nullable=False))
    op.add_column("normalized_alerts", sa.Column("assigned_to", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("normalized_alerts", sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("normalized_alerts", sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("normalized_alerts", sa.Column("tags", postgresql.JSONB(), server_default="[]", nullable=False))
    op.add_column("normalized_alerts", sa.Column("analyst_notes", sa.Text(), nullable=True))
    op.add_column("normalized_alerts", sa.Column("enrichment_summary", postgresql.JSONB(), nullable=True))
    op.create_foreign_key("fk_normalized_alerts_assigned_to", "normalized_alerts", "users", ["assigned_to"], ["id"], ondelete="SET NULL")
    op.create_index("ix_normalized_alerts_lifecycle_state", "normalized_alerts", ["lifecycle_state"])

    op.create_table(
        "alert_iocs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alert_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ioc_type", sa.String(50), nullable=False),
        sa.Column("ioc_value", sa.String(1024), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["normalized_alerts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "alert_id", "ioc_type", "ioc_value", name="uq_alert_iocs"),
    )
    op.create_index("ix_alert_iocs_alert_id", "alert_iocs", ["alert_id"])
    op.create_index("ix_alert_iocs_ioc_type", "alert_iocs", ["ioc_type"])
    op.create_index("ix_alert_iocs_ioc_value", "alert_iocs", ["ioc_value"])

    op.create_table(
        "enrichment_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alert_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("ioc_type", sa.String(50), nullable=True),
        sa.Column("ioc_value", sa.String(1024), nullable=True),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["normalized_alerts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_enrichment_jobs_alert_id", "enrichment_jobs", ["alert_id"])
    op.create_index("ix_enrichment_jobs_provider", "enrichment_jobs", ["provider"])
    op.create_index("ix_enrichment_jobs_status", "enrichment_jobs", ["status"])

    op.create_table(
        "enrichment_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alert_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("raw_response", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("summary", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["normalized_alerts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["enrichment_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "ingest_dlq",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("raw_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("alert_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("stage", sa.String(50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(50), server_default="open", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["normalized_alerts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["raw_event_id"], ["raw_events.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingest_dlq_stage", "ingest_dlq", ["stage"])
    op.create_index("ix_ingest_dlq_status", "ingest_dlq", ["status"])

    op.create_table(
        "alert_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alert_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("vector", postgresql.JSONB(), nullable=False),
        sa.Column("text_source", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["normalized_alerts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("alert_id"),
    )


def downgrade() -> None:
    op.drop_table("alert_embeddings")
    op.drop_table("ingest_dlq")
    op.drop_table("enrichment_results")
    op.drop_table("enrichment_jobs")
    op.drop_table("alert_iocs")
    op.drop_constraint("fk_normalized_alerts_assigned_to", "normalized_alerts", type_="foreignkey")
    op.drop_index("ix_normalized_alerts_lifecycle_state", "normalized_alerts")
    op.drop_column("normalized_alerts", "enrichment_summary")
    op.drop_column("normalized_alerts", "analyst_notes")
    op.drop_column("normalized_alerts", "tags")
    op.drop_column("normalized_alerts", "closed_at")
    op.drop_column("normalized_alerts", "assigned_at")
    op.drop_column("normalized_alerts", "assigned_to")
    op.drop_column("normalized_alerts", "lifecycle_state")
