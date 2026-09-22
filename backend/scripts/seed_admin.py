"""Seed admin users for SOCOPILOT.

Usage (from repo root):
  python backend/scripts/seed_admin.py

Passwords are read from environment variables to avoid hardcoded credentials:
  SEED_ADMIN_PASSWORD   — password for admin@test.com   (default: random)
  SEED_ADMIN2_PASSWORD  — password for admin@example.com (default: random)

This script uses the application's AsyncSessionLocal and password hashing
utility so created users match application auth behavior.
"""
import asyncio
import os
import secrets

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models.tenant import Tenant
from app.db.models.user import User
from app.core.security import get_password_hash


def _generate_password() -> str:
    return secrets.token_urlsafe(16)


ADMIN_USERS = [
    ("admin@test.com", os.environ.get("SEED_ADMIN_PASSWORD") or _generate_password(), "admin"),
    ("admin@example.com", os.environ.get("SEED_ADMIN2_PASSWORD") or _generate_password(), "admin"),
]
DEFAULT_TENANT_NAME = "default"


async def main() -> None:
    async with AsyncSessionLocal() as session:
        # find or create tenant
        res = await session.execute(select(Tenant).where(Tenant.name == DEFAULT_TENANT_NAME))
        tenant = res.scalar_one_or_none()
        if tenant is None:
            tenant = Tenant(name=DEFAULT_TENANT_NAME, description="Auto-created tenant for local dev")
            session.add(tenant)
            await session.flush()  # populate tenant.id
            print(f"Created tenant {tenant.name} ({tenant.id})")
        else:
            print(f"Found tenant {tenant.name} ({tenant.id})")

        for email, password, role in ADMIN_USERS:
            res = await session.execute(
                select(User).where(User.email == email).where(User.tenant_id == tenant.id)
            )
            user = res.scalar_one_or_none()
            if user is not None:
                print(f"Admin user already exists: {user.email} (id={user.id})")
                continue

            hashed = get_password_hash(password)
            user = User(
                tenant_id=tenant.id,
                email=email,
                hashed_password=hashed,
                role=role,
                is_active=True,
            )
            session.add(user)
            await session.flush()
            print(f"Created admin user {email} (id={user.id}, password={'<from env>' if os.environ.get('SEED_ADMIN_PASSWORD') or os.environ.get('SEED_ADMIN2_PASSWORD') else password})")

        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
