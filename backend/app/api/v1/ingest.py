"""Generic webhook alert ingestion."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, status

from app.connectors.generic_json import GenericJsonConnector
from app.core.dependencies import CurrentUserDep, DbSession
from app.core.logging import get_logger
from app.ingest.service import IngestService
from app.middleware.correlation import CORRELATION_HEADER
from app.schemas.ingest import IngestAlertsRequest, IngestAlertsResponse, IngestItemResponse

router = APIRouter(prefix="/ingest", tags=["ingest"])
logger = get_logger(__name__)
connector = GenericJsonConnector()


@router.post("/alerts", response_model=IngestAlertsResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_alerts(
    request: Request,
    current_user: CurrentUserDep,
    db: DbSession,
) -> IngestAlertsResponse:
    """
    Ingest generic JSON SIEM alerts.

  Accepts a single alert object, `{"alert": {...}}`, or `{"alerts": [...]}`.
    """
    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

    correlation_id = request.headers.get(CORRELATION_HEADER) or str(uuid4())
    client_ip = request.client.host if request.client else None

    try:
        if isinstance(body, dict) and ("alert" in body or "alerts" in body):
            alerts = IngestAlertsRequest.model_validate(body).items()
        elif isinstance(body, list):
            alerts = [connector.parse(item) for item in body]
        else:
            alerts = connector.parse_batch(body)
    except Exception as exc:
        logger.warning("ingest_validation_failed", error=str(exc))
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if not alerts:
        raise HTTPException(status_code=422, detail="No alerts provided")

    service = IngestService(db)
    items: list[IngestItemResponse] = []

    for alert in alerts:
        item = await service.accept_alert(
            tenant_id=current_user.tenant_id,
            correlation_id=correlation_id,
            payload=body if isinstance(body, dict) else {"alerts": body},
            alert=alert,
            client_ip=client_ip,
        )
        items.append(item)

    logger.info("ingest_accepted", count=len(items), correlation_id=correlation_id)
    return IngestAlertsResponse(
        correlation_id=correlation_id,
        accepted=len(items),
        items=items,
    )
