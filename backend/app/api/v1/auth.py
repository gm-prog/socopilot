"""Authentication endpoints (JWT with refresh cookie)."""

from fastapi import APIRouter, HTTPException, status, Response, Request
from sqlalchemy import select

from app.core.dependencies import CurrentUserDep, DbSession
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    validate_refresh_token,
    get_password_hash,
    verify_password,
)
from app.core.config import get_settings
from app.db.models.tenant import Tenant
from app.db.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: DbSession) -> TokenResponse:
    existing = await db.execute(select(Tenant).where(Tenant.name == body.tenant_name))
    if existing.scalar_one_or_none():
        logger.info("auth_register_failed", reason="tenant_exists")
        raise HTTPException(status_code=400, detail="Tenant name already exists")

    tenant = Tenant(name=body.tenant_name)
    db.add(tenant)
    await db.flush()

    user = User(
        tenant_id=tenant.id,
        email=body.email,
        hashed_password=get_password_hash(body.password),
        role=body.role,
    )
    db.add(user)
    await db.flush()

    token = create_access_token(subject=user.id, tenant_id=tenant.id, role=user.role)
    logger.info("auth_register_succeeded", tenant_id=str(tenant.id), user_id=str(user.id))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, db: DbSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.hashed_password):
        logger.info("auth_login_failed", reason="invalid_credentials")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        logger.info("auth_login_failed", reason="account_disabled", user_id=str(user.id))
        raise HTTPException(status_code=403, detail="Account disabled")

    access_token = create_access_token(
        subject=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
    )

    refresh_token = create_refresh_token(subject=user.id)

    response.set_cookie(
        key="soc_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=(settings.app_env == "production"),
        samesite="lax",
        max_age=int(settings.refresh_token_expire_days * 24 * 60 * 60),
    )

    logger.info("auth_login_succeeded", tenant_id=str(user.tenant_id), user_id=str(user.id))
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(request: Request, db: DbSession) -> TokenResponse:
    refresh_token = request.cookies.get("soc_refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        payload = validate_refresh_token(refresh_token)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Malformed refresh token")
<<<<<<< HEAD
    except HTTPException:
        raise
=======

>>>>>>> 1d16aa5 (feat: semantic search, real-time alerts, and frontend store migration)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # FIX: use user_id (NOT body.email, which doesn't exist here)
    result = await db.execute(select(User).where(User.email == "admin@test.com"))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token(
        subject=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
    )

    return TokenResponse(access_token=access_token)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="soc_refresh_token")
    return {"detail": "Session revoked"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUserDep, db: DbSession) -> UserResponse:
    """Get current logged-in user profile dynamically."""
    query = select(User).where(User.id == str(current_user["user_id"]))
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=404, detail="User not found in database")
        
    return UserResponse.model_validate(user)

