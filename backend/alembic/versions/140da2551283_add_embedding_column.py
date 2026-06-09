"""add_embedding_column

Revision ID: 140da2551283
Revises: c656387cf416
Create Date: 2026-06-05 22:47:50.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '140da2551283'
down_revision = 'c656387cf416'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('normalized_alerts', sa.Column('embedding', Vector(768), nullable=True))

def downgrade():
    op.drop_column('normalized_alerts', 'embedding')
