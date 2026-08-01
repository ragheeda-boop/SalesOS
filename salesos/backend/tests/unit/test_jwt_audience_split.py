"""STORY-02-03: JWT issuer/audience split + Owner Platform consumption."""

from __future__ import annotations

import inspect

import pytest

from app.common.exceptions import UnauthorizedError
from app.config import settings
from app.dependencies import verify_token
from app.modules.identity.service import (
    create_access_token,
    create_owner_access_token,
    create_owner_refresh_token,
    create_refresh_token,
    decode_access_token,
    decode_owner_access_token,
    decode_owner_refresh_token,
    decode_refresh_token,
)
from app.owner_auth import (
    get_owner_scoped_tenant_id,
    require_owner_role_dep,
    verify_owner_token,
)


def test_tenant_access_token_audience_claim():
    token = create_access_token("user-1", "tenant-1")
    payload = decode_access_token(token)
    assert payload["iss"] == settings.jwt_issuer
    assert payload["aud"] == settings.jwt_audience
    assert payload["sub"] == "user-1"
    assert payload["tenant_id"] == "tenant-1"
    assert payload["type"] == "access"


def test_owner_access_token_audience_claim():
    token = create_owner_access_token("owner-user-1")
    payload = decode_owner_access_token(token)
    assert payload["iss"] == settings.jwt_issuer
    assert payload["aud"] == settings.jwt_owner_audience
    assert payload["sub"] == "owner-user-1"
    assert payload["type"] == "access"
    assert "tenant_id" not in payload


def test_tenant_refresh_token_audience_claim():
    token = create_refresh_token("user-2", "tenant-2")
    payload = decode_refresh_token(token)
    assert payload["aud"] == settings.jwt_audience
    assert payload["type"] == "refresh"


def test_owner_refresh_token_audience_claim():
    token = create_owner_refresh_token("owner-user-2")
    payload = decode_owner_refresh_token(token)
    assert payload["aud"] == settings.jwt_owner_audience
    assert payload["type"] == "refresh"


def test_tenant_decoder_rejects_owner_token():
    owner_token = create_owner_access_token("owner-user-3")
    with pytest.raises(UnauthorizedError):
        decode_access_token(owner_token)


def test_owner_decoder_rejects_tenant_token():
    tenant_token = create_access_token("user-3", "tenant-3")
    with pytest.raises(UnauthorizedError):
        decode_owner_access_token(tenant_token)


def test_audiences_are_distinct():
    assert settings.jwt_audience != settings.jwt_owner_audience
    assert settings.jwt_audience == "salesos-api"
    assert settings.jwt_owner_audience == "salesos-owner-platform"


@pytest.mark.asyncio
async def test_verify_owner_token_accepts_owner_audience():
    token = create_owner_access_token("owner-dep-1")
    payload = await verify_owner_token(authorization=f"Bearer {token}")
    assert payload["aud"] == settings.jwt_owner_audience
    assert payload["sub"] == "owner-dep-1"


@pytest.mark.asyncio
async def test_verify_owner_token_rejects_tenant_audience():
    tenant_token = create_access_token("user-dep-1", "tenant-dep-1")
    with pytest.raises(UnauthorizedError):
        await verify_owner_token(authorization=f"Bearer {tenant_token}")


@pytest.mark.asyncio
async def test_verify_token_still_rejects_owner_audience():
    """Tenant path must remain salesos-api-only (do not weaken)."""
    owner_token = create_owner_access_token("owner-dep-2")
    with pytest.raises(UnauthorizedError):
        await verify_token(authorization=f"Bearer {owner_token}")


@pytest.mark.asyncio
async def test_verify_token_still_accepts_tenant_audience():
    tenant_token = create_access_token("user-dep-2", "tenant-dep-2")
    payload = await verify_token(authorization=f"Bearer {tenant_token}")
    assert payload["aud"] == settings.jwt_audience


@pytest.mark.asyncio
async def test_owner_scoped_tenant_id_requires_header():
    token = create_owner_access_token("owner-dep-3")
    payload = await verify_owner_token(authorization=f"Bearer {token}")
    with pytest.raises(Exception) as exc_info:
        await get_owner_scoped_tenant_id(x_tenant_id=None, _token_payload=payload)
    assert getattr(exc_info.value, "status_code", None) == 400


@pytest.mark.asyncio
async def test_owner_scoped_tenant_id_from_header():
    token = create_owner_access_token("owner-dep-4")
    payload = await verify_owner_token(authorization=f"Bearer {token}")
    tenant = await get_owner_scoped_tenant_id(x_tenant_id="tenant-scoped-1", _token_payload=payload)
    assert tenant == "tenant-scoped-1"


def test_admin_router_wires_owner_role_dep():
    from app.modules.admin import router as admin_router_mod

    src = inspect.getsource(admin_router_mod)
    assert "require_owner_role_dep" in src
    assert "from app.owner_auth import require_owner_role_dep" in src
    assert "require_role_dep(" not in src.replace("require_owner_role_dep(", "")
    dep_fn = require_owner_role_dep("admin")
    assert inspect.iscoroutinefunction(dep_fn)
    assert "get_current_owner_user_role" in inspect.getsource(dep_fn)
