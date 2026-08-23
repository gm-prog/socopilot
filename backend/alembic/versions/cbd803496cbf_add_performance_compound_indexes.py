"""add performance compound indexes

Revision ID: cbd803496cbf
Revises: pgvector_and_indexes
Create Date: 2026-08-05

"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'cbd803496cbf'
down_revision: Union[str, None] = 'pgvector_and_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_index("idx_raw_events_tenant_received", "raw_events", ["tenant_id", "received_at"])
    op.create_index("idx_alerts_tenant_last_seen", "normalized_alerts", ["tenant_id", "last_seen_at"])
    op.create_index("idx_alerts_tenant_status_last_seen", "normalized_alerts", ["tenant_id", "status", "last_seen_at"])
    op.create_index("idx_alerts_tenant_severity_last_seen", "normalized_alerts", ["tenant_id", "severity", "last_seen_at"])

def downgrade() -> None:
    op.drop_index("idx_raw_events_tenant_received", table_name="raw_events")
    op.drop_index("idx_alerts_tenant_last_seen", table_name="normalized_alerts")
    op.drop_index("idx_alerts_tenant_status_last_seen", table_name="normalized_alerts")
    op.drop_index("idx_alerts_tenant_severity_last_seen", table_name="normalized_alerts")
