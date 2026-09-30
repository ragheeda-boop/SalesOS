"""Marketplace router (/api/v1/marketplace/*) must require the "admin" role,
not just any authenticated user.

_get_registry()/_get_permission_gate() cache a SINGLE, process-wide
PluginRegistry/PermissionGate on app.state -- domains/marketplace has no
tenant_id anywhere in its models or service layer, so this registry is
shared, undifferentiated, across every tenant on the process. Every
endpoint (list/get/install/uninstall/enable/disable/config/permissions)
previously required only `verify_token` (any authenticated user, any role,
any tenant) -- a regular, non-admin end user of any tenant could read or
mutate the entire platform's installed-plugin state on behalf of every
other tenant.

Matches DEC-159's already-ratified fix for the identical shape of gap on
/api/v1/cache/* (report 115): router-level dependency changed from
verify_token to require_role_dep("admin").

This test proves the gate actually rejects a non-admin caller before
reaching any handler logic (no registry mutation happens), and that an
admin caller is still let through to a real install/list round trip.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.dependencies import get_current_user_is_platform_owner, get_current_user_role
from domains.marketplace.router import router as marketplace_router

_VALID_MANIFEST = {
    "id": "test-plugin",
    "name": "Test Plugin",
    "version": "1.0.0",
    "description": "A plugin for testing.",
    "author": "Test Author",
}


def _make_app(role: str = "admin", is_owner: bool = True) -> FastAPI:
    app = FastAPI()
    app.include_router(marketplace_router)
    app.dependency_overrides[get_current_user_role] = lambda: role
    app.dependency_overrides[get_current_user_is_platform_owner] = lambda: is_owner
    return app


def test_non_admin_role_is_rejected_on_every_endpoint():
    with TestClient(_make_app(role="user")) as client:
        assert client.get("/api/v1/marketplace").status_code == 403
        assert client.get("/api/v1/marketplace/test-plugin").status_code == 403
        assert (
            client.post("/api/v1/marketplace/install", json={"manifest": _VALID_MANIFEST}).status_code
            == 403
        )
        assert client.post("/api/v1/marketplace/test-plugin/uninstall").status_code == 403
        assert client.post("/api/v1/marketplace/test-plugin/enable").status_code == 403
        assert client.post("/api/v1/marketplace/test-plugin/disable").status_code == 403
        assert client.get("/api/v1/marketplace/test-plugin/history").status_code == 403
        assert (
            client.post("/api/v1/marketplace/test-plugin/config", json={"config": {}}).status_code
            == 403
        )


def test_manager_role_is_also_rejected_admin_only():
    with TestClient(_make_app(role="manager")) as client:
        assert client.get("/api/v1/marketplace").status_code == 403


def test_tenant_admin_without_platform_owner_marker_is_rejected():
    with TestClient(_make_app(role="admin", is_owner=False)) as client:
        assert client.get("/api/v1/marketplace").status_code == 403
        assert (
            client.post("/api/v1/marketplace/install", json={"manifest": _VALID_MANIFEST}).status_code
            == 403
        )


def test_admin_role_can_install_and_list_a_plugin():
    with TestClient(_make_app(role="admin")) as client:
        install_resp = client.post(
            "/api/v1/marketplace/install", json={"manifest": _VALID_MANIFEST, "config": {}}
        )
        assert install_resp.status_code == 200
        assert install_resp.json()["plugin"]["plugin_id"] == "test-plugin"

        list_resp = client.get("/api/v1/marketplace")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 1
