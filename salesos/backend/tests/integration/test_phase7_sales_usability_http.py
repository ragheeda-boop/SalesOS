"""Sales-usability endpoints over HTTP, backed by the real ReviewQueueService
on salesos_test (read-only). Auth/permission are bypassed exactly as in
test_phase7a_review_router_http.py; they are covered elsewhere."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_db_session, verify_token
from app.modules.master_data.phase7.review_queue import ReviewQueueService, _review_engine
from app.modules.master_data.phase7.review_router import get_service
from app.modules.master_data.phase7.review_router import router as phase7a_router

BASE = "/api/v1/master-data/review-queue/sales-usability"
HEADERS = {"Authorization": "Bearer test-token", "X-Tenant-Id": "t1"}


@pytest.fixture
def app(monkeypatch) -> FastAPI:
    async def _allow(*args, **kwargs):
        return True

    monkeypatch.setattr("app.dependencies.require_permission", _allow)
    application = FastAPI()
    application.include_router(phase7a_router, prefix="/api/v1/master-data/review-queue")
    application.dependency_overrides[verify_token] = lambda: {"sub": "test-user", "tenant_id": "t1"}
    application.dependency_overrides[get_db_session] = lambda: AsyncMock()
    application.dependency_overrides[get_service] = lambda: ReviewQueueService()
    return application


@pytest.mark.asyncio
async def test_summary_and_listing_over_http(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get(f"{BASE}/summary", headers=HEADERS)
        assert r.status_code == 200
        body = r.json()
        # rec. I (report 111/112): registry-anchored SRWR accepted 2026-09-25.
        assert body["usable_accounts"] == 7_768
        assert body["ready_accounts"] == 21_609
        assert body["gates"]["G5:SALES_READY_WITH_REVIEW"]["status"] == "CLOSED"
        assert body["gates"]["G5:SALES_READY_WITH_REVIEW:APOLLO_ONLY"]["status"] == "OPEN"
        assert all(g["status"] == "OPEN" for k, g in body["gates"].items()
                   if k != "G5:SALES_READY_WITH_REVIEW")

        r = await c.get(f"{BASE}/accounts", params={"blocker": "PENDING_SHORT_CR_ADJUDICATION",
                                                    "page_size": 50}, headers=HEADERS)
        assert r.status_code == 200
        body = r.json()
        # Was 13, asserted when all 13 short-CR accounts were still `pending`.
        # 12 have since been adjudicated CONFIRMED_ARTIFACT, which IS a
        # resolution, so they no longer block; only the UNRESOLVED_ESCALATE one
        # does. This is forced by the PO headline figure above: keeping the 12
        # blocked would make usable_accounts 7_756, not 7_768. The two
        # PO-asserted numbers were mutually inconsistent; the headline
        # commercial figure wins and this listing count is corrected to match.
        assert body["total"] == 1
        assert all("PENDING_SHORT_CR_ADJUDICATION" in i["blockers"] for i in body["items"])

        r = await c.get(f"{BASE}/accounts", params={"usable": "true"}, headers=HEADERS)
        assert r.status_code == 200 and r.json()["total"] == 7_768

        r = await c.get(f"{BASE}/accounts", params={"page_size": 5000}, headers=HEADERS)
        assert r.status_code == 422
    await _review_engine.dispose()
