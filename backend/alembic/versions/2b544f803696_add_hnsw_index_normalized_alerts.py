"""add_hnsw_index_normalized_alerts

Revision ID: 2b544f803696
Revises: 684b0228c415
Create Date: 2026-06-17
"""

from alembic import op

revision = "2b544f803696"
down_revision = "140da2551283"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE indexname = 'normalized_alerts_embedding_hnsw_idx'
            ) THEN
                CREATE INDEX normalized_alerts_embedding_hnsw_idx
                ON normalized_alerts
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64);
            END IF;
        END $$;
    """)


def downgrade():
    op.execute("""
        DROP INDEX IF EXISTS normalized_alerts_embedding_hnsw_idx;
    """)
