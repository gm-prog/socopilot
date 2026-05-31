"""PostgreSQL-backed vector store (Qdrant-ready abstraction)."""

import math
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.alert_embedding import AlertEmbedding


class VectorStore:
    """Store and retrieve embeddings — stub semantic search via cosine similarity."""

    def upsert(
        self,
        session: Session,
        *,
        tenant_id: UUID,
        alert_id: UUID,
        model_name: str,
        vector: list[float],
        text_source: str = "alert_summary",
    ) -> AlertEmbedding:
        existing = session.execute(
            select(AlertEmbedding).where(AlertEmbedding.alert_id == alert_id)
        ).scalar_one_or_none()
        if existing:
            existing.vector = vector
            existing.model_name = model_name
            existing.text_source = text_source
            return existing
        emb = AlertEmbedding(
            tenant_id=tenant_id,
            alert_id=alert_id,
            model_name=model_name,
            vector=vector,
            text_source=text_source,
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
    ) -> list[tuple[UUID, float]]:
        """Brute-force cosine similarity — replace with Qdrant in Phase 3."""
        rows = session.execute(
            select(AlertEmbedding).where(AlertEmbedding.tenant_id == tenant_id)
        ).scalars()
        scored: list[tuple[UUID, float]] = []
        for row in rows:
            score = _cosine_similarity(query_vector, row.vector)
            scored.append((row.alert_id, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
