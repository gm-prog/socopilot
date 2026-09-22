"""SQLAlchemy declarative base, mixins, and global tenant compilation filters."""

import uuid
import logging
from datetime import datetime

from sqlalchemy import DateTime, func, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapper, Mapped, mapped_column, with_loader_criteria

from app.db.mixins import TenantMixin

logger = logging.getLogger("app.db.base")

class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


# ----------------------------------------------------------------------
# GLOBAL TENANT ISOLATION HOOK (opt-in via execution options)
# ----------------------------------------------------------------------
#
# SQLAlchemy 2.0 replacement for the previous Query.before_compile
# interceptor, which never fired on 2.0-style queries (and called a
# non-existent Query.filter_by_clause method), i.e. it provided no
# isolation at all.
#
# Usage: any SELECT/UPDATE/DELETE executed with
#   session.execute(stmt, params, execution_options={"tenant_id": <uuid>})
# automatically gets `tenant_id == <uuid>` applied to every TenantMixin
# entity in the statement, including relationship loads. Queries without
# the execution option are NOT modified — explicit per-query filters
# (as used across the API layer) remain the primary isolation mechanism.

from sqlalchemy import event
from sqlalchemy.orm import Session, with_loader_criteria


@event.listens_for(Session, "do_orm_execute")
def enforce_tenant_isolation_criteria(orm_context):
    tenant_id = orm_context.execution_options.get("tenant_id")

    if tenant_id is None:
        return

    if not (orm_context.is_select or orm_context.is_update or orm_context.is_delete):
        return

    logger.debug(
        "Enforcing tenant isolation criteria via execution options",
        extra={"tenant_id": str(tenant_id)},
    )

    orm_context.statement = orm_context.statement.options(
        with_loader_criteria(
            TenantMixin,
            lambda cls: cls.tenant_id == tenant_id,
            include_aliases=True,
            propagate_to_loaders=True,
        )
    )

# Import model modules so Alembic autogenerate sees the complete metadata.
from app.db import models  # noqa: E402,F401
