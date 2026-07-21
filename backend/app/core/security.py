"""JWT and password utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError

from passlib.context import CryptContext
from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------- EXCEPTIONS ----------------

class TokenValidationError(Exception):
    """Raised when JWT validation fails."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


# ---------------- PASSWORD ----------------

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ---------------- TOKEN ----------------

def create_access_token(
    subject: str | UUID,
    tenant_id: str | UUID,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )

    payload = {
        "sub": str(subject),
        "tenant_id": str(tenant_id),
        "role": role,
        "exp": expire,
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


# ---------------- TOKEN HELPERS ----------------

def normalize_bearer_token(token: str | None) -> str | None:
    if not token:
        return None

    token = token.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()

    return token or None


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()

    token = normalize_bearer_token(token)
    if not token:
        raise TokenValidationError("missing_token")

    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )


def validate_access_token(token: str | None) -> dict[str, Any]:
    token = normalize_bearer_token(token)

    if not token:
        raise TokenValidationError("missing_token")

    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

    except ExpiredSignatureError:
        raise TokenValidationError("expired_token")

    except JWTError:
        raise TokenValidationError("invalid_token")

    if payload.get("type") != "access":
        raise TokenValidationError("invalid_token")

    return payload


def verify_token(token: str) -> dict[str, Any] | None:
    try:
        return validate_access_token(token)
    except TokenValidationError:
        return None


def create_refresh_token(subject: str | UUID, expires_delta: timedelta | None = None) -> str:
    """Create a signed refresh token with a longer expiry and type marker."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=settings.refresh_token_expire_days)
    )

    payload = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
    }

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def validate_refresh_token(token: str) -> dict[str, Any]:
    """Validate a refresh token and return its payload or raise TokenValidationError."""
    token = normalize_bearer_token(token)
    if not token:
        raise TokenValidationError("missing_token")

    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except ExpiredSignatureError:
        raise TokenValidationError("expired_token")
    except JWTError:
        raise TokenValidationError("invalid_token")

    if payload.get("type") != "refresh":
        raise TokenValidationError("invalid_token")

    return payload