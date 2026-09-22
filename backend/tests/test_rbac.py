"""Unit tests for role-based write guards."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.dependencies import require_roles


@pytest.mark.asyncio
async def test_readonly_role_is_rejected_for_write_roles():
    checker = require_roles("analyst", "lead", "admin")
    with pytest.raises(HTTPException) as excinfo:
        await checker(SimpleNamespace(role="readonly"))
    assert excinfo.value.status_code == 403


@pytest.mark.asyncio
async def test_write_roles_are_allowed():
    checker = require_roles("analyst", "lead", "admin")
    for role in ("analyst", "lead", "admin"):
        user = SimpleNamespace(role=role)
        assert (await checker(user)) is user


@pytest.mark.asyncio
async def test_unknown_role_is_rejected():
    checker = require_roles("admin")
    with pytest.raises(HTTPException) as excinfo:
        await checker(SimpleNamespace(role="intern"))
    assert excinfo.value.status_code == 403
