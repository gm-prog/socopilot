"""FastAPI dependency injection."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.redis import is_jti_blacklisted
from app.core.security import TokenValidationError, validate_access_token
from app.db.models.user import User
from app.db.session import get_db

security_scheme = HTTPBearer(auto_error=False)
logger = get_logger(__name__)


# -------------------------
# TOKEN EXTRACTION & VALIDATION
# -------------------------

async def get_current_user_payload(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(security_scheme),
    ],
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = validate_access_token(credentials.credentials)
    except TokenValidationError as exc:
        logger.info("auth_rejected", reason=exc.reason)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jti = payload.get("jti")
    if jti and await is_jti_blacklisted(jti):
        logger.info("auth_rejected", reason="token_revoked", jti=jti)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


# -------------------------
# CURRENT USER CONTEXT
# -------------------------

DbSession = Annotated[AsyncSession, Depends(get_db)]

async def get_current_user(
    payload: Annotated[dict, Depends(get_current_user_payload)],
    db: DbSession,
) -> User:
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        user_uuid = UUID(str(user_id))
        result = await db.execute(select(User).where(User.id == user_uuid))
        user = result.scalar_one_or_none()
    except Exception:
        result = await db.execute(select(User).where(User.email == str(user_id)))
        user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


async def get_current_tenant_id(
    current_user: Annotated[User, Depends(get_current_user)],
) -> str:
    return str(current_user.tenant_id)


CurrentUserDep = Annotated[User, Depends(get_current_user)]
TenantDep = Annotated[str, Depends(get_current_tenant_id)]


def require_roles(*allowed_roles: str):
    """Dependency that enforces allowed roles."""
    async def role_checker(current_user: CurrentUserDep):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role forbidden. Allowed roles: {list(allowed_roles)}"
            )
        return current_user
    return role_checker
