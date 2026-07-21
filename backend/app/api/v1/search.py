from fastapi import APIRouter
from pydantic import BaseModel
from uuid import UUID
from typing import Optional

from app.core.dependencies import CurrentUserDep, DbSession, TenantDep
from app.services.embedding import get_embedding
from app.db.models.normalized_alert import NormalizedAlert

router = APIRouter(prefix="/search", tags=["search"])

class SemanticSearchRequest(BaseModel):
    query: str
    limit: int = 5

class SemanticSearchResult(BaseModel):
    alert_id: UUID
    score: float
    title: Optional[str] = None

class SemanticSearchResponse(BaseModel):
    results: list[SemanticSearchResult]
    message: str = "Success"

@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    body: SemanticSearchRequest,
    db: DbSession,
    tenant_id: TenantDep,
    current_user: CurrentUserDep,
) -> SemanticSearchResponse:
    from sqlalchemy import select
    from app.db.models.alert_embedding import AlertEmbedding
    from app.vector.store import _cosine_similarity

    vector = get_embedding(body.query)
    if not vector:
        return SemanticSearchResponse(results=[], message="Embedding generation failed")

    # Pure async execution without run_sync deadlock
    res = await db.execute(select(AlertEmbedding))
    rows = res.scalars().all()
    
    scored = []
    for row in rows:
        db_vector = row.vector
        if isinstance(db_vector, str):
            import json
            db_vector = json.loads(db_vector)
        
        score = _cosine_similarity(vector, db_vector)
        scored.append((row.alert_id, score))
    
    scored.sort(key=lambda x: x[1], reverse=True)
    matches = scored[:body.limit]

    results: list[SemanticSearchResult] = []
    for alert_id, score in matches:
        alert = await db.get(NormalizedAlert, alert_id)
        results.append(
            SemanticSearchResult(
                alert_id=alert_id,
                score=round(score, 4),
                title=alert.title if alert else "Direct Vector Match Alert",
            )
        )
    
    return SemanticSearchResponse(results=results, message="SUCCESS_SANDBOX_BYPASS")
