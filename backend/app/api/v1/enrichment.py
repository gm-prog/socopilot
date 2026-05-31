"""Enrichment results API."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.dependencies import CurrentUserDep, DbSession
from app.db.models.enrichment import EnrichmentResult
from app.schemas.phase2 import EnrichmentResultResponse

router = APIRouter(prefix="/enrichment", tags=["enrichment"])


@router.get("/alerts/{alert_id}", response_model=list[EnrichmentResultResponse])
async def get_alert_enrichment(
    alert_id: UUID,
    current_user: CurrentUserDep,
    db: DbSession,
) -> list[EnrichmentResultResponse]:
    result = await db.execute(
        select(EnrichmentResult)
        .where(
            EnrichmentResult.alert_id == alert_id,
            EnrichmentResult.tenant_id == current_user.tenant_id,
        )
        .order_by(EnrichmentResult.created_at.desc())
    )
    return [EnrichmentResultResponse.model_validate(r) for r in result.scalars().all()]


@router.get("/results/{result_id}", response_model=EnrichmentResultResponse)
async def get_enrichment_result(
    result_id: UUID,
    current_user: CurrentUserDep,
    db: DbSession,
) -> EnrichmentResultResponse:
    result = await db.execute(
        select(EnrichmentResult).where(
            EnrichmentResult.id == result_id,
            EnrichmentResult.tenant_id == current_user.tenant_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Enrichment result not found")
    return EnrichmentResultResponse.model_validate(row)
