"""Case CRUD API."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.cases.repository import CaseRepository
from app.core.dependencies import CurrentUserDep, DbSession
from app.schemas.cases import CaseCreateRequest, CaseListResponse, CaseResponse, CaseUpdateRequest

router = APIRouter(prefix="/cases", tags=["cases"])


def _to_case_response(case) -> CaseResponse:
    return CaseResponse(
        id=case.id,
        tenant_id=case.tenant_id,
        title=case.title,
        description=case.description,
        severity=case.severity,
        status=case.status,
        created_at=case.created_at,
        updated_at=case.updated_at,
        alert_ids=[link.alert_id for link in getattr(case, "case_alerts", [])],
    )


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    body: CaseCreateRequest,
    current_user: CurrentUserDep,
    db: DbSession,
) -> CaseResponse:
    repo = CaseRepository(db)
    try:
        case = await repo.create_case(
            current_user.tenant_id,
            title=body.title,
            description=body.description,
            severity=body.severity,
            status=body.status,
            alert_ids=body.alert_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_case_response(case)


@router.get("", response_model=CaseListResponse)
async def list_cases(
    current_user: CurrentUserDep,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> CaseListResponse:
    repo = CaseRepository(db)
    cases, total = await repo.list_cases(current_user.tenant_id, page=page, page_size=page_size)
    return CaseListResponse(
        items=[_to_case_response(case) for case in cases],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: UUID,
    body: CaseUpdateRequest,
    current_user: CurrentUserDep,
    db: DbSession,
) -> CaseResponse:
    repo = CaseRepository(db)
    try:
        case = await repo.update_case(
            current_user.tenant_id,
            case_id,
            title=body.title,
            description=body.description,
            severity=body.severity,
            status=body.status,
            alert_ids=body.alert_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return _to_case_response(case)


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: UUID,
    current_user: CurrentUserDep,
    db: DbSession,
) -> CaseResponse:
    repo = CaseRepository(db)
    case = await repo.get_case(current_user.tenant_id, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return _to_case_response(case)
