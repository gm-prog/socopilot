"""Unit tests for app.core.security — JWT and password utilities."""

from datetime import timedelta
from unittest.mock import patch, MagicMock

import pytest

from app.core.security import (
    TokenValidationError,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    get_password_hash,
    normalize_bearer_token,
    validate_access_token,
    validate_refresh_token,
    verify_password,
    verify_token,
)


# ---- helpers ----

def _fake_settings():
    s = MagicMock()
    s.secret_key = "test-secret-key-for-unit-tests"
    s.algorithm = "HS256"
    s.access_token_expire_minutes = 60
    s.refresh_token_expire_days = 7
    return s


# ---- password hashing ----

def test_hash_and_verify_password():
    hashed = get_password_hash("s3cret!")
    assert hashed != "s3cret!"
    assert verify_password("s3cret!", hashed) is True


def test_verify_wrong_password():
    hashed = get_password_hash("correct")
    assert verify_password("wrong", hashed) is False


# ---- normalize_bearer_token ----

def test_normalize_bearer_strips_prefix():
    assert normalize_bearer_token("Bearer abc123") == "abc123"


def test_normalize_bearer_case_insensitive():
    assert normalize_bearer_token("bearer xyz") == "xyz"


def test_normalize_bearer_no_prefix():
    assert normalize_bearer_token("raw-token") == "raw-token"


def test_normalize_bearer_none_input():
    assert normalize_bearer_token(None) is None


def test_normalize_bearer_empty_string():
    assert normalize_bearer_token("") is None


def test_normalize_bearer_only_prefix():
    # "Bearer " → strip() → "Bearer" which does not start with "bearer "
    # so the function returns "Bearer" as-is (treated as a raw token).
    assert normalize_bearer_token("Bearer ") == "Bearer"


# ---- create / decode access token ----

@patch("app.core.security.get_settings", return_value=_fake_settings())
def test_create_and_decode_access_token(mock_settings):
    token = create_access_token("user-1", "tenant-1", "admin")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-1"
    assert payload["tenant_id"] == "tenant-1"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"


@patch("app.core.security.get_settings", return_value=_fake_settings())
def test_create_access_token_custom_expiry(mock_settings):
    token = create_access_token(
        "user-2", "tenant-2", "analyst", expires_delta=timedelta(minutes=5)
    )
    payload = decode_access_token(token)
    assert payload["sub"] == "user-2"


# ---- validate_access_token ----

@patch("app.core.security.get_settings", return_value=_fake_settings())
def test_validate_access_token_success(mock_settings):
    token = create_access_token("u1", "t1", "admin")
    payload = validate_access_token(token)
    assert payload["sub"] == "u1"
    assert payload["type"] == "access"


@patch("app.core.security.get_settings", return_value=_fake_settings())
def test_validate_access_token_with_bearer_prefix(mock_settings):
    token = create_access_token("u2", "t2", "analyst")
    payload = validate_access_token(f"Bearer {token}")
    assert payload["sub"] == "u2"


def test_validate_access_token_missing():
    with pytest.raises(TokenValidationError, match="missing_token"):
        validate_access_token(None)


def test_validate_access_token_empty():
    with pytest.raises(TokenValidationError, match="missing_token"):
        validate_access_token("")


@patch("app.core.security.get_settings", return_value=_fake_settings())
def test_validate_access_token_invalid_jwt(mock_settings):
    with pytest.raises(TokenValidationError, match="invalid_token"):
        validate_access_token("not.a.valid.jwt")


@patch("app.core.security.get_settings", return_value=_fake_settings())
def test_validate_access_token_expired(mock_settings):
    token = create_access_token(
        "u3", "t3", "admin", expires_delta=timedelta(seconds=-1)
    )
    with pytest.raises(TokenValidationError, match="expired_token"):
        validate_access_token(token)


@patch("app.core.security.get_settings", return_value=_fake_settings())
def test_validate_access_token_wrong_type(mock_settings):
    """A refresh token must not pass access-token validation."""
    refresh = create_refresh_token("u4")
    with pytest.raises(TokenValidationError, match="invalid_token"):
        validate_access_token(refresh)


# ---- verify_token (returns None on failure) ----

@patch("app.core.security.get_settings", return_value=_fake_settings())
def test_verify_token_valid(mock_settings):
    token = create_access_token("u5", "t5", "admin")
    result = verify_token(token)
    assert result is not None
    assert result["sub"] == "u5"


@patch("app.core.security.get_settings", return_value=_fake_settings())
def test_verify_token_invalid_returns_none(mock_settings):
    assert verify_token("garbage") is None


# ---- refresh tokens ----

@patch("app.core.security.get_settings", return_value=_fake_settings())
def test_create_and_validate_refresh_token(mock_settings):
    token = create_refresh_token("user-r1")
    payload = validate_refresh_token(token)
    assert payload["sub"] == "user-r1"
    assert payload["type"] == "refresh"


@patch("app.core.security.get_settings", return_value=_fake_settings())
def test_create_refresh_token_custom_expiry(mock_settings):
    token = create_refresh_token("user-r2", expires_delta=timedelta(days=1))
    payload = validate_refresh_token(token)
    assert payload["sub"] == "user-r2"


def test_validate_refresh_token_missing():
    with pytest.raises(TokenValidationError, match="missing_token"):
        validate_refresh_token("")


@patch("app.core.security.get_settings", return_value=_fake_settings())
def test_validate_refresh_token_expired(mock_settings):
    token = create_refresh_token("u-exp", expires_delta=timedelta(seconds=-1))
    with pytest.raises(TokenValidationError, match="expired_token"):
        validate_refresh_token(token)


@patch("app.core.security.get_settings", return_value=_fake_settings())
def test_validate_refresh_token_wrong_type(mock_settings):
    """An access token must not pass refresh-token validation."""
    access = create_access_token("u6", "t6", "admin")
    with pytest.raises(TokenValidationError, match="invalid_token"):
        validate_refresh_token(access)
