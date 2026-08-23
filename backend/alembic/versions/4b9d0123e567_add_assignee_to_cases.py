"""add_assignee_to_cases

Revision ID: 4b9d0123e567
Revises: 3a8c90123f45
Create Date: 2026-08-05
"""
from alembic import op
import sqlalchemy as sa

revision = '4b9d0123e567'
down_revision = '3a8c90123f45'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        'cases',
        sa.Column('assignee', sa.String(length=255), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('cases', 'assignee')
