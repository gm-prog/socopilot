"""update_embedding_dimension_to_384

Revision ID: c656387cf416
Revises: 82d5e030f361
Create Date: 2026-06-05 14:34:57.401652

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c656387cf416'
down_revision: Union[str, None] = '82d5e030f361'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute('ALTER TABLE alerts ADD COLUMN embedding vector(384);')

def downgrade() -> None:
    op.execute('ALTER TABLE alerts DROP COLUMN embedding;')
