"""Generic webhook alert ingestion."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, status
from kombu.exceptions import OperationalError

from app.connectors.generic_json import GenericJsonConnector
from app.core.dependencies import CurrentUserDep, DbSession
from app.core.logging import get_logger
from app.ingest.event_service import IngestEventService
from app.ingest.service import IngestService
from app.middleware.correlation import CORRELATION_HEADER
from app.schemas.ingest import (
    IngestAlertsRequest,
    IngestAlertsResponse,
    IngestEventQueuedResponse,
    IngestEventRequest,
    IngestItemResponse,
)

router = APIRouter(prefix="/ingest", tags=["ingest"])
logger = get_logger(__name__)
connector = GenericJsonConnector()


# ---------------- EVENT INGESTION (QUEUE) ----------------

@router.post(
    "/event",
    response_model=IngestEventQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_event(
    body: IngestEventRequest,
    current_user: CurrentUserDep,
    db: DbSession,
) -> IngestEventQueuedResponse:
    """
    Queue a raw SOC event for async processing.
    """

    service = IngestEventService(db)

    try:
        return await service.queue_event(
            body=body,
            tenant_id=current_user["tenant_id"],
            user_id=current_user["user_id"],
        )

    except ValueError as exc:
        logger.warning(
            "ingest_event_bad_request",
            error=str(exc),
            tenant_id=str(current_user["tenant_id"]),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except OperationalError as exc:
        logger.exception(
            "ingest_queue_unavailable",
            tenant_id=str(current_user["tenant_id"]),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingest queue unavailable — Redis/Celery not reachable",
        ) from exc

    except RuntimeError as exc:
        logger.exception(
            "ingest_runtime_failure",
            error=str(exc),
            tenant_id=str(current_user["tenant_id"]),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "ingest_queue_failed",
            error=str(exc),
            exception_type=type(exc).__name__,
            tenant_id=str(current_user["tenant_id"]),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal ingest error",
        ) from exc


# ---------------- ALERT INGESTION (BULK/PARSE) ----------------

@router.post(
    "/alerts",
    response_model=IngestAlertsResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_alerts(
    request: Request,
    current_user: CurrentUserDep,
    db: DbSession,
) -> IngestAlertsResponse:
    """
    Ingest generic SIEM alerts.
    Accepts:
      - {"alert": {...}}
      - {"alerts": [...]}
      - raw list
    """

    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body",
        ) from exc

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
        logger.warning(
            "ingest_validation_failed",
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    if not alerts:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No alerts provided",
        )

    service = IngestService(db)
    items: list[IngestItemResponse] = []

    for alert in alerts:
        item = await service.accept_alert(
            tenant_id=current_user["tenant_id"],
            correlation_id=correlation_id,
            payload=body if isinstance(body, dict) else {"alerts": body},
            alert=alert,
            client_ip=client_ip,
        )
        items.append(item)

    logger.info(
        "ingest_accepted",
        count=len(items),
        correlation_id=correlation_id,
        tenant_id=str(current_user["tenant_id"]),
    )

    return IngestAlertsResponse(
        correlation_id=correlation_id,
        accepted=len(items),
        items=items,
    )

from fastapi import UploadFile, File
from app.workers.tasks.ingest_pipeline import parse_and_chunk_document_task

@router.post("/document", status_code=status.HTTP_202_ACCEPTED)
async def ingest_document(
    current_user: CurrentUserDep,
    file: UploadFile = File(...),
):
    file_bytes = await file.read()
    filename = file.filename or "unknown.txt"
    task = parse_and_chunk_document_task.delay(
        tenant_id=str(current_user["tenant_id"]),
        filename=filename,
        file_bytes=file_bytes.hex()
    )
    return {"task_id": task.id, "filename": filename, "status": "queued"}
