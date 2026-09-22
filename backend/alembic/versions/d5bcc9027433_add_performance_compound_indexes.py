"""add_performance_compound_indexes

Revision ID: d5bcc9027433
Revises: cbd803496cbf
Create Date: 2026-08-05

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'd5bcc9027433'
down_revision: Union[str, None] = 'cbd803496cbf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_raw_events_tenant_received "
        "ON raw_events (tenant_id, received_at DESC);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_normalized_alerts_tenant_last_seen "
        "ON normalized_alerts (tenant_id, last_seen_at DESC);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_investigation_events_alert_created "
        "ON investigation_events (alert_id, created_at);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_investigation_events_alert_created;")
    op.execute("DROP INDEX IF EXISTS ix_normalized_alerts_tenant_last_seen;")
    op.execute("DROP INDEX IF EXISTS ix_raw_events_tenant_received;")
