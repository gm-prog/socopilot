"""add_updated_at_to_pipeline_jobs

Revision ID: 8f3b4567c890
Revises: 7e2a3456b789
Create Date: 2026-08-05
"""
from alembic import op
import sqlalchemy as sa

revision = '8f3b4567c890'
down_revision = '7e2a3456b789'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        'pipeline_jobs',
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('pipeline_jobs', 'updated_at')
