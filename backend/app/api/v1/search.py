"""Search API — OpenSearch + semantic + SQL timeline."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.config import get_settings
from app.core.dependencies import CurrentUserDep, DbSession
from app.db.models.normalized_alert import NormalizedAlert
from app.integrations.opensearch.client import get_search_backend
from app.schemas.phase2 import SemanticSearchRequest, SemanticSearchResponse, SemanticSearchResult
from app.vector.store import VectorStore
from app.workers.tasks.phase2 import _embed_text

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/timeline")
async def search_timeline(
    current_user: CurrentUserDep,
    db: DbSession,
    start: datetime | None = None,
    end: datetime | None = None,
    severity: str | None = None,
    limit: int = Query(100, ge=1, le=500),
) -> dict:
    """Timeline search over normalized alerts (detected_at ordering)."""
    q = select(NormalizedAlert).where(NormalizedAlert.tenant_id == current_user.tenant_id)
    if start is not None:
        q = q.where(NormalizedAlert.detected_at >= start)
    if end is not None:
        q = q.where(NormalizedAlert.detected_at <= end)
    if severity:
        q = q.where(NormalizedAlert.severity == severity)
    q = q.order_by(NormalizedAlert.detected_at.desc()).limit(limit)
    result = await db.execute(q)
    alerts = result.scalars().all()
    return {
        "count": len(alerts),
        "items": [
            {
                "alert_id": str(a.id),
                "title": a.title,
                "severity": a.severity,
                "source": a.source,
                "detected_at": a.detected_at.isoformat(),
                "status": a.status,
                "lifecycle_state": a.lifecycle_state,
            }
            for a in alerts
        ],
    }


@router.get("/alerts")
async def search_alerts(
    current_user: CurrentUserDep,
    q: str = Query(min_length=1),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    backend = get_search_backend()
    hits = await backend.search_alerts(
        {"q": q, "tenant_id": str(current_user.tenant_id)},
        limit=limit,
    )
    return {"query": q, "hits": hits, "count": len(hits)}


@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    body: SemanticSearchRequest,
    current_user: CurrentUserDep,
    db: DbSession,
) -> SemanticSearchResponse:
    settings = get_settings()
    vector = _embed_text(body.query, settings.ollama_embed_model)
    if not vector:
        return SemanticSearchResponse(results=[], message="Embedding unavailable")

    matches = await db.run_sync(
        lambda session: VectorStore().semantic_search(
            session,
            tenant_id=current_user.tenant_id,
            query_vector=vector,
            limit=body.limit,
        )
    )

    results: list[SemanticSearchResult] = []
    for alert_id, score in matches:
        alert = await db.get(NormalizedAlert, alert_id)
        results.append(
            SemanticSearchResult(
                alert_id=alert_id,
                score=round(score, 4),
                title=alert.title if alert else None,
            )
        )
    return SemanticSearchResponse(results=results)
