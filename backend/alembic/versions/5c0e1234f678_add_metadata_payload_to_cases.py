"""add_metadata_payload_to_cases

Revision ID: 5c0e1234f678
Revises: 4b9d0123e567
Create Date: 2026-08-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '5c0e1234f678'
down_revision = '4b9d0123e567'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        'cases',
        sa.Column('metadata_payload', JSONB(astext_type=sa.Text()), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('cases', 'metadata_payload')
