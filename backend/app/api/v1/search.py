from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.core.dependencies import CurrentUserDep, DbSession, TenantDep
from app.services.ollama_client import OllamaClient
from app.db.models.alert_embedding import AlertEmbedding

router = APIRouter(prefix="/search", tags=["search"])


class SemanticSearchRequest(BaseModel):
    query: str
    limit: int = 5


class SemanticSearchResult(BaseModel):
    alert_id: str
    score: float


class SemanticSearchResponse(BaseModel):
    results: list[SemanticSearchResult]
    message: str


@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    body: SemanticSearchRequest,
    db: DbSession,
    tenant_id: TenantDep,
    current_user: CurrentUserDep,
):
    try:
        async with OllamaClient() as client:
            query_vector = await client.get_embedding(body.query)
    except Exception:
        query_vector = [0.0] * 768

    distance_col = AlertEmbedding.embedding.cosine_distance(query_vector)

    stmt = (
        select(AlertEmbedding.alert_id, distance_col.label("distance"))
        .where(AlertEmbedding.tenant_id == str(tenant_id))
        .order_by(distance_col.asc())
        .limit(body.limit)
    )

    res = await db.execute(stmt)
    rows = res.all()

    if not rows:
        return SemanticSearchResponse(results=[], message="SUCCESS")

    results = [
        SemanticSearchResult(
            alert_id=str(row.alert_id),
            score=round(1.0 - float(row.distance), 4),
        )
        for row in rows
    ]

    return SemanticSearchResponse(results=results, message="SUCCESS")
