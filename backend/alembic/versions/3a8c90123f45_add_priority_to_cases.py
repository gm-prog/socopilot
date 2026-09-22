"""add_priority_to_cases

Revision ID: 3a8c90123f45
Revises: 217d64a797c2
Create Date: 2026-08-05
"""
from alembic import op
import sqlalchemy as sa

revision = '3a8c90123f45'
down_revision = '217d64a797c2'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        'cases',
        sa.Column('priority', sa.String(length=50), server_default='medium', nullable=False)
    )

def downgrade() -> None:
    op.drop_column('cases', 'priority')
