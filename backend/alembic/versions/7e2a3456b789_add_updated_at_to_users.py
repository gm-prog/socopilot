"""add_updated_at_to_users

Revision ID: 7e2a3456b789
Revises: 6d1f2345a789
Create Date: 2026-08-05
"""
from alembic import op
import sqlalchemy as sa

revision = '7e2a3456b789'
down_revision = '6d1f2345a789'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('users', 'updated_at')
