from uuid import UUID
from sqlalchemy import select
from app.db.models import Tenant

DEFAULT_TENANT_ID = UUID("90e6afbd-08e4-4b4a-9830-54bf37061a77")


async def seed_default_tenant(session):
    result = await session.execute(
        select(Tenant).where(Tenant.id == DEFAULT_TENANT_ID)
    )
    existing = result.scalar_one_or_none()

    if existing:
        print("Tenant already exists, skipping seed")
        return

    tenant = Tenant(
        id=DEFAULT_TENANT_ID,
        name="default-tenant",
        description="seed tenant for local dev"
    )

    session.add(tenant)
    await session.commit()
    print("Default tenant seeded")
