"""Marketplace Listings router (/marketplace/listings/*) mutating endpoints
must require the "admin" role, not just any authenticated user.

store.py's own docstring: "Owner-platform catalog scope (not tenant RLS
tables)" -- _STORE is a single, process-wide catalog shared by every
tenant. Read endpoints (list_listings/get_listing/meta) correctly stay
open to any authenticated user -- browsing a shared marketplace catalog is
reasonable, like any logged-in user browsing an app store. But every
endpoint that MUTATES that shared catalog (create/delete/submit/certify/
publish/seed) previously required only mere authentication too -- any
authenticated user of any role, any tenant, could delete or falsely
"certify" a listing visible to every other tenant.

Matches DEC-159/report 166's already-ratified fix for the identical shape
of gap. install_listing/list_catalog_installs are untouched -- they are
already correctly tenant-scoped (a tenant recording its own install), not
a catalog mutation, so they stay at plain authentication.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.modules.marketplace_listings.router as listings_router_module
from app.dependencies import get_current_user_role, verify_token
from app.modules.marketplace_listings.router import router as listings_router
from app.modules.marketplace_listings.store import MemMarketplaceListingStore


def _make_app(role: str = "admin") -> FastAPI:
    app = FastAPI()
    app.include_router(listings_router)
    app.dependency_overrides[verify_token] = lambda: {"sub": "test-user"}
    app.dependency_overrides[get_current_user_role] = lambda: role
    # Fresh, isolated store per app instance -- the module default is a
    # process-wide singleton that would otherwise leak state between tests.
    listings_router_module._STORE = MemMarketplaceListingStore()
    return app


_VALID_LISTING = {
    "slug": "test-connector",
    "name": "Test Connector",
    "listing_type": "connector",
    "version": "1.0.0",
    "connector_key": "test",
}


def test_non_admin_role_is_rejected_on_every_mutating_endpoint():
    with TestClient(_make_app(role="user")) as client:
        assert client.post("/marketplace/listings", json=_VALID_LISTING).status_code == 403
        assert client.delete("/marketplace/listings/some-id").status_code == 403
        assert client.post("/marketplace/listings/some-id/submit").status_code == 403
        assert client.post("/marketplace/listings/some-id/certify").status_code == 403
        assert client.post("/marketplace/listings/some-id/publish").status_code == 403
        assert client.post("/marketplace/listings/seed-first-party").status_code == 403
        assert client.post("/marketplace/listings/seed-publish-pack").status_code == 403


def test_manager_role_is_also_rejected_admin_only():
    with TestClient(_make_app(role="manager")) as client:
        assert client.post("/marketplace/listings", json=_VALID_LISTING).status_code == 403


def test_non_admin_can_still_browse_the_shared_catalog():
    """The read/browse endpoints were deliberately left at plain
    authentication -- confirms the fix didn't lock down the intended
    shared-catalog browsing experience."""
    with TestClient(_make_app(role="user")) as client:
        assert client.get("/marketplace/listings").status_code == 200
        assert client.get("/marketplace/listings/meta").status_code == 200


def test_admin_role_can_create_and_delete_a_listing():
    with TestClient(_make_app(role="admin")) as client:
        create_resp = client.post("/marketplace/listings", json=_VALID_LISTING)
        assert create_resp.status_code == 200
        listing_id = create_resp.json()["id"]

        list_resp = client.get("/marketplace/listings")
        assert list_resp.status_code == 200
        assert any(item["slug"] == "test-connector" for item in list_resp.json())

        delete_resp = client.delete(f"/marketplace/listings/{listing_id}")
        assert delete_resp.status_code == 200
        assert delete_resp.json()["deleted"] is True
