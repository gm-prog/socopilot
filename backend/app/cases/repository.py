"""Async repository for case CRUD operations."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.case import Case
from app.db.models.case_alert import CaseAlert
from app.db.models.normalized_alert import NormalizedAlert


class CaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_case(
        self,
        tenant_id: UUID,
        *,
        title: str,
        description: str | None,
        severity: str,
        status: str,
        alert_ids: Sequence[UUID],
    ) -> Case:
        unique_alert_ids = list(dict.fromkeys(alert_ids))
        if unique_alert_ids:
            result = await self.session.execute(
                select(NormalizedAlert.id).where(
                    NormalizedAlert.tenant_id == tenant_id,
                    NormalizedAlert.id.in_(unique_alert_ids),
                )
            )
            found_ids = set(result.scalars().all())
            if len(found_ids) != len(unique_alert_ids):
                raise ValueError("One or more alerts were not found for this tenant")

        case = Case(
            tenant_id=tenant_id,
            title=title,
            description=description,
            severity=severity,
            status=status,
        )
        case.case_alerts = [CaseAlert(alert_id=alert_id) for alert_id in unique_alert_ids]
        self.session.add(case)
        await self.session.flush()
        await self.session.refresh(case)
        return case

    async def list_cases(
        self,
        tenant_id: UUID,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Case], int]:
        query = (
            select(Case)
            .where(Case.tenant_id == tenant_id)
            .options(selectinload(Case.case_alerts))
        )
        count_query = select(func.count()).select_from(Case).where(Case.tenant_id == tenant_id)
        total = (await self.session.execute(count_query)).scalar_one()
        offset = (page - 1) * page_size
        result = await self.session.execute(
            query.order_by(Case.updated_at.desc()).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_case(self, tenant_id: UUID, case_id: UUID) -> Case | None:
        result = await self.session.execute(
            select(Case)
            .where(
                Case.id == case_id,
                Case.tenant_id == tenant_id,
            )
            .options(selectinload(Case.case_alerts))
        )
        return result.scalar_one_or_none()
