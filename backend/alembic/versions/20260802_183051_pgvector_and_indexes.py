"""pgvector conversion and compound performance indexes

Revision ID: pgvector_and_indexes
Revises: 70a_fix_investigation_events
Create Date: 2026-08-03
"""
from alembic import op
import sqlalchemy as sa

revision = 'pgvector_and_indexes'
down_revision = '70a_fix_investigation_events'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Rename 'vector' column to 'embedding' and cast to vector(1536)
    op.execute(
        "ALTER TABLE alert_embeddings "
        "RENAME COLUMN vector TO embedding;"
    )
    op.execute(
        "ALTER TABLE alert_embeddings "
        "ALTER COLUMN embedding TYPE vector(1536) "
        "USING embedding::text::vector(1536);"
    )

    # 3. Add compound performance indexes
    op.create_index(
        'ix_raw_events_tenant_received',
        'raw_events',
        ['tenant_id', sa.text('received_at DESC')],
        if_not_exists=True
    )
    op.create_index(
        'ix_normalized_alerts_tenant_last_seen',
        'normalized_alerts',
        ['tenant_id', sa.text('last_seen_at DESC')],
        if_not_exists=True
    )
    op.create_index(
        'ix_investigation_events_tenant_alert',
        'investigation_events',
        ['tenant_id', 'alert_id', sa.text('created_at ASC')],
        if_not_exists=True
    )


def downgrade() -> None:
    op.drop_index('ix_investigation_events_tenant_alert', table_name='investigation_events')
    op.drop_index('ix_normalized_alerts_tenant_last_seen', table_name='normalized_alerts')
    op.drop_index('ix_raw_events_tenant_received', table_name='raw_events')

    op.execute(
        "ALTER TABLE alert_embeddings "
        "ALTER COLUMN embedding TYPE jsonb "
        "USING embedding::text::jsonb;"
    )
    op.execute(
        "ALTER TABLE alert_embeddings "
        "RENAME COLUMN embedding TO vector;"
    )
