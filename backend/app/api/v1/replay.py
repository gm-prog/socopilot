"""Raw event replay API."""

from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException

from app.core.dependencies import CurrentUserDep, DbSession
from app.middleware.correlation import CORRELATION_HEADER
from app.replay.service import ReplayService
from app.schemas.phase2 import ReplayResponse
from fastapi import Request

router = APIRouter(prefix="/replay", tags=["replay"])


@router.post("/{raw_event_id}", response_model=ReplayResponse, status_code=202)
async def replay_raw_event(
    raw_event_id: UUID,
    request: Request,
    current_user: CurrentUserDep,
    db: DbSession,
) -> ReplayResponse:
    """Reprocess a raw event through normalize → dedup → persist → post-ingest."""
    correlation_id = request.headers.get(CORRELATION_HEADER) or str(uuid4())
    service = ReplayService(db)
    try:
        result = await service.replay_raw_event(
            current_user.tenant_id,
            raw_event_id,
            correlation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ReplayResponse(**result)
