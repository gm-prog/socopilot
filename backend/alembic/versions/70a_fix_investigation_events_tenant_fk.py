"""Fix investigation_events tenant_id and FK target

Revision ID: 70a_fix_investigation_events
Revises: e9588ba7264a
Create Date: 2026-08-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '70a_fix_investigation_events'
down_revision: Union[str, None] = 'e9588ba7264a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Clean up legacy constraints if present
    op.execute("ALTER TABLE investigation_events DROP CONSTRAINT IF EXISTS investigation_events_alert_id_fkey")
    op.execute("ALTER TABLE investigation_events DROP CONSTRAINT IF EXISTS fk_investigation_events_alert_id_normalized_alerts")
    op.execute("ALTER TABLE investigation_events DROP CONSTRAINT IF EXISTS fk_investigation_events_tenant_id_tenants")

    # 2. Handle tenant_id addition safely
    # If rows exist without tenant_id, backfill from normalized_alerts via alert_id before making NOT NULL
    op.add_column('investigation_events', sa.Column('tenant_id', sa.UUID(), nullable=True))
    
    op.execute("""
        UPDATE investigation_events ie
        SET tenant_id = na.tenant_id
        FROM normalized_alerts na
        WHERE ie.alert_id = na.id AND ie.tenant_id IS NULL
    """)
    
    # Purge any orphaned events that cannot be linked to a valid tenant
    op.execute("DELETE FROM investigation_events WHERE tenant_id IS NULL")
    
    # Enforce NOT NULL constraint
    op.alter_column('investigation_events', 'tenant_id', nullable=False)

    # 3. Apply foreign key constraints
    op.create_foreign_key(
        'fk_investigation_events_tenant_id_tenants',
        'investigation_events', 'tenants',
        ['tenant_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_investigation_events_alert_id_normalized_alerts',
        'investigation_events', 'normalized_alerts',
        ['alert_id'], ['id'],
        ondelete='CASCADE'
    )

    # 4. Compound index for tenant-isolated timeline queries
    op.create_index(
        'ix_investigation_events_tenant_alert_created',
        'investigation_events',
        ['tenant_id', 'alert_id', 'created_at']
    )


def downgrade() -> None:
    op.drop_index('ix_investigation_events_tenant_alert_created', table_name='investigation_events')
    op.drop_constraint('fk_investigation_events_alert_id_normalized_alerts', 'investigation_events', type_='foreignkey')
    op.drop_constraint('fk_investigation_events_tenant_id_tenants', 'investigation_events', type_='foreignkey')
    op.drop_column('investigation_events', 'tenant_id')
    op.create_foreign_key(
        'investigation_events_alert_id_fkey',
        'investigation_events', 'alerts',
        ['alert_id'], ['id'],
        ondelete='CASCADE'
    )
