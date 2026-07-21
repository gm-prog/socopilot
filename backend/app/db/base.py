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


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


# ----------------------------------------------------------------------
# GLOBAL SQLALCHEMY COMPILATION INTERCEPTOR (AUTOMATED ISOLATION)
# ----------------------------------------------------------------------

from sqlalchemy.orm import Query
from sqlalchemy.orm import Query
@event.listens_for(Query, "before_compile", retval=True)
def enforce_tenant_isolation_criteria(query):
    """
    Interceptors query compilation for all entities subclassing TenantMixin.
    Extracts the request-scoped tenant_id from execution_options and binds it natively.
    """
    tenant_id = query.execution_options.get("tenant_id", None)
    
    if tenant_id is not None:
        logger.debug(
            "Enforcing tenant isolation filter during compilation",
            extra={"tenant_id": str(tenant_id)}
        )
        query = query.enable_assertions(False).filter_by_clause(
            with_loader_criteria(
                TenantMixin,
                lambda cls: cls.tenant_id == tenant_id,
                include_aliases=True,
                propagate_to_loaders=True
            )
        )
    else:
        # Check if query targets any isolated entities
        for mapper in (query.context.compile_state.mappers if query.context and query.context.compile_state else []):
            if issubclass(mapper.class_, TenantMixin):
                logger.critical(
                    "CRITICAL: System attempted to query a multi-tenant model without a tenant execution context.",
                    extra={"target_model": mapper.class_.__name__}
                )
                raise RuntimeError(
                    f"Data isolation fault: Query context missing 'tenant_id' for model {mapper.class_.__name__}"
                )

    return query

# Import model modules so Alembic autogenerate sees the complete metadata.
from app.db import models  # noqa: E402,F401
