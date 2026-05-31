"""add investigation events

Revision ID: 82d5e030f361
Revises: 69cbf2ae4837
Create Date: 2026-05-31 11:38:25.834108

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82d5e030f361'
down_revision: Union[str, None] = '69cbf2ae4837'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
