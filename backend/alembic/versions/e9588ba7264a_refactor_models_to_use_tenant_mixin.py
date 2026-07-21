"""refactor_models_to_use_tenant_mixin

Revision ID: e9588ba7264a
Revises: None
Create Date: 2026-07-08

"""
from alembic import op
import sqlalchemy as sa
import pgvector

revision = "e9588ba7264a"
down_revision = "2b544f803696"
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
