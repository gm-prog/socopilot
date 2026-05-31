"""Search API — OpenSearch + semantic stub."""

from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.config import get_settings
from app.core.dependencies import CurrentUserDep, DbSession
from app.db.models.normalized_alert import NormalizedAlert
from app.db.sync_session import get_sync_db
from app.integrations.opensearch.client import get_search_backend
from app.schemas.phase2 import SemanticSearchRequest, SemanticSearchResponse, SemanticSearchResult
from app.vector.store import VectorStore
from app.workers.tasks.phase2 import _embed_text

router = APIRouter(prefix="/search", tags=["search"])


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

    with get_sync_db() as session:
        matches = VectorStore().semantic_search(
            session,
            tenant_id=current_user.tenant_id,
            query_vector=vector,
            limit=body.limit,
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
