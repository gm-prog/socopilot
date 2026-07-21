import logging
from uuid import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, declared_attr

logger = logging.getLogger(__name__)

class TenantMixin:
    """Mixin to enforce uniform database isolation by forcing a tenant_id foreign key constraint."""
    
    @declared_attr
    def tenant_id(cls) -> Mapped[UUID]:
        return mapped_column(
            ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )
