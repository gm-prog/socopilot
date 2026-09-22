"""align_embedding_dimensions_to_768

Revision ID: b8d2f5a1c4e7
Revises: 73131b121b0b
Create Date: 2026-09-22

Unifies every pgvector column on 768 dimensions, matching the output of the
configured embedding model (nomic-embed-text):

- normalized_alerts.embedding: vector(384) -> vector(768)
- alert_embeddings.embedding:  vector(1536) -> vector(768)

Vectors whose dimensionality does not match the target are set to NULL before
the column type change (PostgreSQL cannot cast between vector sizes). These
values are regenerable: the phase-2 embedding task re-embeds alerts and
upserts into alert_embeddings, and IngestRepository.persist_alert re-embeds on
creation, so no information that cannot be recomputed is destroyed.
"""

from alembic import op

revision = "b8d2f5a1c4e7"
down_revision = "73131b121b0b"
branch_labels = None
depends_on = None

TARGET_DIM = 768

HNSW_INDEX = "normalized_alerts_embedding_hnsw_idx"
HNSW_PARAMS = "WITH (m = 16, ef_construction = 64)"


def _retype_vector_column(table: str, column: str, to_dim: int, *, null_mismatches: bool) -> None:
    """Retype a vector column to `to_dim`.

    Mismatched-dimension vectors cannot be cast across dimensions. For
    nullable columns (normalized_alerts.embedding) they are nulled so the
    row survives and the vector regenerates later. For non-nullable columns
    (alert_embeddings.embedding, a derived cache) those rows are deleted.
    """
    cleanup = (
        f"UPDATE {table} SET {column} = NULL "
        f"WHERE {column} IS NOT NULL AND vector_dims({column}) <> {to_dim};"
        if null_mismatches
        else f"DELETE FROM {table} "
        f"WHERE {column} IS NOT NULL AND vector_dims({column}) <> {to_dim};"
    )
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = '{table}'
                  AND column_name = '{column}'
            ) THEN
                {cleanup}

                ALTER TABLE {table}
                    ALTER COLUMN {column} TYPE vector({to_dim})
                    USING {column}::text::vector({to_dim});
            END IF;
        END $$;
        """
    )


def upgrade() -> None:
    # normalized_alerts.embedding: 384 -> 768 (drop/recreate the HNSW index
    # around the type change; pgvector requires the index dropped first).
    op.execute(f"DROP INDEX IF EXISTS {HNSW_INDEX};")
    _retype_vector_column("normalized_alerts", "embedding", TARGET_DIM, null_mismatches=True)
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'normalized_alerts'
                  AND column_name = 'embedding'
            ) AND NOT EXISTS (
                SELECT 1 FROM pg_indexes WHERE indexname = '{HNSW_INDEX}'
            ) THEN
                CREATE INDEX {HNSW_INDEX}
                    ON normalized_alerts
                    USING hnsw (embedding vector_cosine_ops)
                    {HNSW_PARAMS};
            END IF;
        END $$;
        """
    )

    # alert_embeddings.embedding: 1536 -> 768
    _retype_vector_column("alert_embeddings", "embedding", TARGET_DIM, null_mismatches=False)


def downgrade() -> None:
    op.execute(f"DROP INDEX IF EXISTS {HNSW_INDEX};")
    _retype_vector_column("normalized_alerts", "embedding", 384, null_mismatches=True)
    _retype_vector_column("alert_embeddings", "embedding", 1536, null_mismatches=False)
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'normalized_alerts'
                  AND column_name = 'embedding'
            ) AND NOT EXISTS (
                SELECT 1 FROM pg_indexes WHERE indexname = '{HNSW_INDEX}'
            ) THEN
                CREATE INDEX {HNSW_INDEX}
                    ON normalized_alerts
                    USING hnsw (embedding vector_cosine_ops)
                    {HNSW_PARAMS};
            END IF;
        END $$;
        """
    )
