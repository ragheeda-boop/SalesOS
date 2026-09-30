"""Pilot decision A: platform owner is an explicit marker, not tenant ``admin``.

Proves against a real migrated database (restricted app role, FORCE RLS):

* a self-registrant becomes admin of their own new tenant and can perform a
  tenant-admin action (``POST /invite``);
* that tenant admin is refused by ``/owner/login``, by an Owner Platform route
  (``require_owner_role_dep``), by platform-global writes
  (``require_platform_owner_dep``, ``POST /tenants``) and by cross-tenant SAML
  configuration;
* once ``users.is_platform_owner`` is set, the same account passes;
* an invitee is ``user``, not admin;
* a second registration cannot join an existing tenant.

Real RS256 tokens throughout; no auth dependency is overridden.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.common.middleware import TenantContextMiddleware
from app.database import engine
from app.dependencies import require_platform_owner_dep
from app.modules.identity.router import router as identity_router
from app.modules.identity.service import (
    create_owner_access_token,
    decode_access_token,
)
from app.modules.sso.saml_router import router as saml_router
from app.owner_auth import require_owner_role_dep

PASSWORD = "Pilot178!Strong#Pass"
OWNER_DETAIL = "Owner Platform requires a designated platform owner"


def _run_isolated(fn):
    """Run ``fn(session)`` on a private NullPool engine in a fresh loop.

    The shared ``engine`` pool is bound to the TestClient's loop, which is
    closed once the client exits.
    """

    async def _inner():
        private = create_async_engine(engine.url, poolclass=NullPool)
        try:
            async with async_sessionmaker(private)() as s:
                return await fn(s)
        finally:
            await private.dispose()

    return asyncio.run(_inner())


def _reset_shared_pool() -> None:
    """Drop pooled connections left bound to a closed TestClient loop."""
    asyncio.run(engine.dispose(close=False))


def _refuse_production_db() -> None:
    async def _check(s) -> str:
        return (await s.execute(text("SELECT current_database()"))).scalar_one()

    name = _run_isolated(_check)
    if name == "salesos":
        pytest.fail("refusing to run against the persistent 'salesos' database")


def _set_platform_owner(user_id: str, tenant_id: str) -> None:
    async def _run(s) -> None:
        await s.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await s.execute(
            text("UPDATE users SET is_platform_owner = true WHERE id = :u"),
            {"u": user_id},
        )
        await s.commit()

    _run_isolated(_run)


def _user_row(email: str, tenant_id: str) -> tuple[str, bool]:
    async def _run(s) -> tuple[str, bool]:
        await s.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        row = (
            await s.execute(
                text("SELECT role, is_platform_owner FROM users WHERE email = :e"),
                {"e": email},
            )
        ).one()
        return row[0], row[1]

    return _run_isolated(_run)


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(TenantContextMiddleware)
    app.include_router(identity_router, prefix="/api/v1/identity")
    app.include_router(saml_router)

    @app.get("/platform-probe", dependencies=[Depends(require_platform_owner_dep())])
    async def platform_probe() -> dict:
        return {"ok": True}

    @app.get("/owner-probe", dependencies=[Depends(require_owner_role_dep("admin"))])
    async def owner_probe() -> dict:
        return {"ok": True}

    return app


def _approve_manager(email: str, organization_name: str) -> None:
    """Seed the platform-owner approval that /register now requires."""

    async def _run(s) -> None:
        await s.execute(
            text(
                "INSERT INTO org_registration_approvals ("
                "id, organization_name, manager_email, manager_full_name, status, "
                "decided_at, created_at, updated_at"
                ") VALUES ("
                "CAST(:id AS uuid), :org, :email, 'Pilot Admin', 'approved', "
                "NOW(), NOW(), NOW())"
            ),
            {"id": str(uuid.uuid4()), "org": organization_name, "email": email},
        )
        await s.commit()

    _run_isolated(_run)


def test_platform_owner_requires_explicit_marker() -> None:
    _refuse_production_db()
    app = _make_app()
    suffix = uuid.uuid4().hex[:10]
    admin_email = f"pilot178-admin-{suffix}@example.com"
    invitee_email = f"pilot178-invitee-{suffix}@example.com"
    _approve_manager(admin_email, f"Pilot Org {suffix}")

    with TestClient(app) as client:
        reg = client.post(
            "/api/v1/identity/register",
            json={"email": admin_email, "password": PASSWORD, "full_name": "Pilot Admin"},
        )
        assert reg.status_code == 201, reg.text
        tenant_id = reg.json()["tenant_id"]
        auth = {"Authorization": f"Bearer {reg.json()['access_token']}"}

        invite = client.post(
            "/api/v1/identity/invite", json={"email": invitee_email}, headers=auth
        )
        assert invite.status_code == 201, invite.text
        assert invite.json()["role"] == "user"
        invitee_temp_password = invite.json()["temporary_password"]

        owner_login = client.post(
            "/api/v1/identity/owner/login",
            json={"email": admin_email, "password": PASSWORD},
        )
        assert owner_login.status_code == 403, owner_login.text
        assert owner_login.json()["detail"] == OWNER_DETAIL

        create_tenant = client.post(
            "/api/v1/identity/tenants",
            json={"name": f"Rogue {suffix}", "slug": f"rogue-{suffix}"},
            headers=auth,
        )
        assert create_tenant.status_code == 403, create_tenant.text

        assert client.get("/platform-probe", headers=auth).status_code == 403

        saml = client.post(
            "/sso/saml/config",
            data={
                "tenant_id": str(uuid.uuid4()),
                "idp_sso_url": "https://idp.example.com/sso",
                "idp_entity_id": "https://idp.example.com/entity",
                "idp_cert": "MIIC",
            },
            headers=auth,
        )
        assert saml.status_code == 403, saml.text

        rejoin = client.post(
            "/api/v1/identity/register",
            json={
                "email": f"pilot178-joiner-{suffix}@example.com",
                "password": PASSWORD,
                "full_name": "Would-be Joiner",
                "tenant_id": tenant_id,
            },
        )
        assert rejoin.status_code == 400, rejoin.text
    _reset_shared_pool()

    role, is_owner = _user_row(admin_email, tenant_id)
    assert (role, is_owner) == ("admin", False)
    invitee_role, invitee_owner = _user_row(invitee_email, tenant_id)
    assert (invitee_role, invitee_owner) == ("user", False)

    user_id = decode_access_token(reg.json()["access_token"])["sub"]

    owner_token = create_owner_access_token(user_id)
    owner_headers = {"Authorization": f"Bearer {owner_token}", "X-Tenant-Id": tenant_id}
    with TestClient(app) as client:
        pre = client.get("/owner-probe", headers=owner_headers)
        assert pre.status_code == 403, pre.text
        assert pre.json()["detail"] == OWNER_DETAIL

        invitee_login = client.post(
            "/api/v1/identity/login",
            json={"email": invitee_email, "password": invitee_temp_password},
        )
        assert invitee_login.status_code == 200, invitee_login.text
        invitee_auth = {"Authorization": f"Bearer {invitee_login.json()['access_token']}"}
        assert client.get("/platform-probe", headers=invitee_auth).status_code == 403
    _reset_shared_pool()

    _set_platform_owner(user_id, tenant_id)

    with TestClient(app) as client:
        owner_login = client.post(
            "/api/v1/identity/owner/login",
            json={"email": admin_email, "password": PASSWORD},
        )
        assert owner_login.status_code == 200, owner_login.text
        assert owner_login.json().get("tenant_id") in (None, "")

        assert client.get("/owner-probe", headers=owner_headers).status_code == 200
        assert client.get("/platform-probe", headers=auth).status_code == 200

        created = client.post(
            "/api/v1/identity/tenants",
            json={"name": f"Owner Tenant {suffix}", "slug": f"owner-tenant-{suffix}"},
            headers=auth,
        )
        assert created.status_code == 201, created.text
    _reset_shared_pool()
