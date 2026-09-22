"""add_updated_at_to_alerts

Revision ID: 6d1f2345a789
Revises: 5c0e1234f678
Create Date: 2026-08-05
"""
from alembic import op
import sqlalchemy as sa

revision = '6d1f2345a789'
down_revision = '5c0e1234f678'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        'alerts',
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('alerts', 'updated_at')
