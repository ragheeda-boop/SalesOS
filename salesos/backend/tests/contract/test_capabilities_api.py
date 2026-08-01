"""HTTP regression for Phase 0 criterion 5.4 — decorator capability registry API.

Proves GET /api/v1/capabilities (and by-id) exercise the runtime
capability_framework decorator registry end-to-end over ASGI.

Does not designate a single SoT across the four registries (5.1).
Does not map CAP-### (5.2) or make validate_capability_registries exit 0 (5.3).
Does not modify get_db() / set_config (DEC-085).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import verify_token
from app.main import app

# Built-in decorator IDs from runtime/capability_framework/__init__.py
# (asserted via HTTP only — avoid `import runtime` package side-effects in helpers)
EXPECTED_CORE_IDS = frozenset(
    {
        "identity",
        "company",
        "data-fabric",
        "search",
        "timeline",
        "knowledge-graph",
        "feature-store",
        "decision-engine",
        "event-runtime",
        "activity-intelligence",
        "workflow",
        "marketplace",
        "capability-framework",
    }
)


@asynccontextmanager
async def _client_as(tenant_id: str = "cap-tenant", user_id: str = "cap-user") -> AsyncIterator[AsyncClient]:
    async def override_verify_token() -> dict[str, str]:
        return {"sub": user_id, "tenant_id": tenant_id}

    app.dependency_overrides[verify_token] = override_verify_token
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(verify_token, None)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_list_capabilities_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/capabilities")
    assert resp.status_code == 401, resp.text


@pytest.mark.contract
@pytest.mark.asyncio
async def test_list_capabilities_returns_decorator_registry() -> None:
    async with _client_as() as client:
        resp = await client.get("/api/v1/capabilities")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= len(EXPECTED_CORE_IDS)

    ids = {item["id"] for item in body}
    assert EXPECTED_CORE_IDS.issubset(ids), f"API missing IDs: {EXPECTED_CORE_IDS - ids}"

    for item in body:
        assert "name" in item and item["name"]
        assert "status" in item and item["status"]
        assert "version" in item
        assert isinstance(item.get("tags"), list)
        assert isinstance(item.get("contract"), dict)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_capability_by_id_and_404() -> None:
    async with _client_as() as client:
        ok = await client.get("/api/v1/capabilities/identity")
        assert ok.status_code == 200, ok.text
        payload = ok.json()
        assert payload["id"] == "identity"
        assert payload["status"] == "stable"
        assert isinstance(payload.get("contract"), dict)
        assert "user.read" in payload["contract"].get("permissions", [])

        missing = await client.get("/api/v1/capabilities/does-not-exist-cap-5-4")
        assert missing.status_code == 404, missing.text


@pytest.mark.contract
@pytest.mark.asyncio
async def test_list_capabilities_status_filter() -> None:
    async with _client_as() as client:
        resp = await client.get("/api/v1/capabilities", params={"status": "stable"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body) >= 1
        assert all(item["status"] == "stable" for item in body)

        bad = await client.get("/api/v1/capabilities", params={"status": "not-a-status"})
        assert bad.status_code == 400, bad.text
