"""PostgreSQL-backed vector store using pgvector native operations."""

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.alert_embedding import AlertEmbedding


class VectorStore:
    """Store and retrieve 768-dimensional embeddings via pgvector."""

    def upsert(
        self,
        session: Session,
        *,
        tenant_id: UUID,
        alert_id: UUID,
        vector: list[float],
    ) -> AlertEmbedding:
        str_alert_id = str(alert_id)
        existing = session.execute(
            select(AlertEmbedding).where(AlertEmbedding.alert_id == str_alert_id)
        ).scalar_one_or_none()

        if existing:
            existing.embedding = vector
            return existing

        emb = AlertEmbedding(
            id=str_alert_id,
            tenant_id=str(tenant_id),
            alert_id=str_alert_id,
            embedding=vector,
        )
        session.add(emb)
        session.flush()
        return emb

    def semantic_search(
        self,
        session: Session,
        *,
        tenant_id: UUID,
        query_vector: list[float],
        limit: int = 10,
    ) -> list[tuple[str, float]]:
        """Native pgvector cosine distance search pushed down to PostgreSQL."""
        distance_col = AlertEmbedding.embedding.cosine_distance(query_vector)

        stmt = (
            select(AlertEmbedding.alert_id, distance_col.label("distance"))
            .where(AlertEmbedding.tenant_id == str(tenant_id))
            .order_by(distance_col.asc())
            .limit(limit)
        )

        rows = session.execute(stmt).all()
        return [(str(row.alert_id), round(1.0 - float(row.distance), 4)) for row in rows]
