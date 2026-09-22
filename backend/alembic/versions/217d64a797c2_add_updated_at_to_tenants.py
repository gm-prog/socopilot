"""add_updated_at_to_tenants

Revision ID: 217d64a797c2
Revises: d5bcc9027433
Create Date: 2026-08-05
"""
from alembic import op
import sqlalchemy as sa

revision = '217d64a797c2'
down_revision = 'd5bcc9027433'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        'tenants',
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        )
    )

def downgrade() -> None:
    op.drop_column('tenants', 'updated_at')
