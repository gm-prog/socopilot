"""update_embedding_dimension_to_384 (safe vector migration)

Revision ID: c656387cf416
Revises: 82d5e030f361
Create Date: 2026-06-09
"""

from alembic import op


revision = "c656387cf416"
down_revision = "82d5e030f361"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'alerts'
        ) THEN

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'alerts'
                AND column_name = 'embedding'
            ) THEN
                ALTER TABLE alerts ADD COLUMN embedding vector(384);
            END IF;

        END IF;
    END $$;
    """)


def downgrade() -> None:
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'alerts'
            AND column_name = 'embedding'
        ) THEN
            ALTER TABLE alerts DROP COLUMN embedding;
        END IF;
    END $$;
    """)
