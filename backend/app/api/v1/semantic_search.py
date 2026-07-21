from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.services.embedding import model
from app.core.security import get_current_user
from app.core.dependencies import TenantDep

router = APIRouter()


@router.post("/search/semantic")
def semantic_search(
    body: dict,
    db: Session = Depends(get_db),
    tenant_id: str = "00000000-0000-0000-0000-000000000000",
    # user=Depends(get_current_user),
):
    query_text = body.get("query")
    limit = body.get("limit", 10)

    if not query_text:
        return {"results": [], "message": "query is required"}

    query_vector = model.encode(query_text).tolist()

    sql = text("""
        SELECT
            id,
            title,
            severity,
            status,
            description,
            embedding <=> :embedding AS distance
        FROM normalized_alerts
        WHERE tenant_id = :tenant_id
          AND embedding IS NOT NULL
        ORDER BY embedding <=> :embedding
        LIMIT :limit;
    """)

    rows = db.execute(sql, {
        "embedding": query_vector,
        "tenant_id": user.tenant_id,
        "limit": limit
    }).fetchall()

    return {
        "results": [
            {
                "id": r.id,
                "title": r.title,
                "severity": r.severity,
                "status": r.status,
                "distance": float(r.distance),
            }
            for r in rows
        ]
    }
