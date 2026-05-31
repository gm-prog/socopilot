"""FastAPI dependency injection."""

from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import TokenValidationError, validate_access_token, verify_token
from app.db.session import get_db

security_scheme = HTTPBearer(auto_error=False)
logger = get_logger(__name__)


async def get_current_user_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
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
        logger.info("rest_auth_rejected", reason=exc.reason)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


async def get_optional_user_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
) -> dict | None:
    if credentials is None:
        return None
    return verify_token(credentials.credentials)


class CurrentUser:
    def __init__(self, payload: dict):
        self.user_id = UUID(payload["sub"])
        self.tenant_id = UUID(payload["tenant_id"])
        self.role = payload.get("role", "analyst")


async def get_current_user(
    payload: Annotated[dict, Depends(get_current_user_payload)],
) -> CurrentUser:
    return CurrentUser(payload)


DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
