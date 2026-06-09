"""Tenant resolution helpers."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.tenant import Tenant

DEFAULT_TENANT_NAME = "default"


def get_default_tenant_id_sync(session: Session) -> UUID | None:
    """Return the default tenant id when present (created by seed_admin)."""
    return session.execute(
        select(Tenant.id).where(Tenant.name == DEFAULT_TENANT_NAME)
    ).scalar_one_or_none()
