"""Router-level integration test for Phase 7-A review-queue endpoints.

Unlike test_phase7a_review_queue.py (pure logic) and
test_phase7a_review_queue_db.py (calls ReviewQueueService directly against a
real DB session), this test mounts the ACTUAL FastAPI router the way
`app/boot/routers.py` mounts it in production and issues real HTTP requests
through it. This is the check that would have caught the double
`/review-queue/review-queue/...` prefix bug: a test that only calls the
service class, or only inspects a function signature, can never see a
mount-prefix mismatch because that mismatch lives entirely in how the router
is wired into the app, not in the service or schema code.

No database is touched: `get_service` is overridden to return a stub with
canned data, so this test exercises routing/dependency-wiring only.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_db_session, verify_token
from app.modules.master_data.phase7.review_router import router as phase7a_router
from app.modules.master_data.phase7.review_router import get_service


class _StubService:
    """Canned, DB-free stand-in for ReviewQueueService.

    Figures are the real salesos_test populations (verified 2026-09-26), not
    invented ones. The previous stub claimed 5,753 / 46,736, which matched no
    query: the true strata are 5,903 CORROBORATION_REVIEW and 33,654
    PRIORITIZATION_PP2 out of 53,644 total. A stub that lies about the
    population lets a data assertion pass against fiction.
    """

    # Real, from md_review_queue_state / md_review_candidates on salesos_test.
    P3_TOTAL = 2_661
    SHORT_CR_TOTAL = 36
    TRIAGE_TOTAL = 53_644
    TRIAGE_COUNTS = {
        "P1:CORROBORATION_REVIEW": 5_903,
        "P2:PRIORITIZATION_PP2": 33_654,
    }

    async def list_p3_pairs(self, *, status=None, batch=None, offset=0, limit=500):
        return [
            {
                "id": "00000000-0000-4000-8000-000000000001",
                "subject_key": "1:2",
                "global_company_id": "00000000-0000-4000-8000-0000000000a1",
                "global_company_id_b": None,
                "status": "dispositioned",
                "disposition": "ESCALATE",
            }
        ], self.P3_TOTAL

    async def get_p3_count(self):
        return self.P3_TOTAL

    async def list_short_cr(self):
        return [
            {
                "master_account_id": "MA-0000001",
                "cr_number_raw": "1;2",
                "valid_cr_count": 0,
                "rejected_tokens": ["1", "2"],
                "global_company_id": None,
            }
        ] * self.SHORT_CR_TOTAL

    async def list_triage_candidates(self, *, candidate_type=None, offset=0, limit=500):
        return [
            {
                "global_company_id": "00000000-0000-4000-8000-0000000000a1",
                "candidate_type": "P1",
                "reason": "CORROBORATION_REVIEW",
            }
        ], self.TRIAGE_TOTAL

    async def get_triage_counts(self):
        return dict(self.TRIAGE_COUNTS)

    async def record_disposition(self, *, queue_type, subject_key, disposition, reviewer,
                                 notes=None, evidence=None):
        merged = dict(evidence or {})
        merged.setdefault("linkage_status", "STUB")
        return {
            "id": "stub-id", "queue_type": queue_type, "subject_key": subject_key,
            "global_company_id": None, "evidence_ref": merged,
            "status": "dispositioned", "disposition": disposition, "reviewer": reviewer,
            "reviewed_at": None, "notes": notes,
        }


@pytest.fixture
def app() -> FastAPI:
    """Mount the real router at the SAME prefix used in app/boot/routers.py."""
    application = FastAPI()
    application.include_router(
        phase7a_router,
        prefix="/api/v1/master-data/review-queue",
    )
    application.dependency_overrides[verify_token] = lambda: {"sub": "test-user", "tenant_id": "t1"}
    application.dependency_overrides[get_db_session] = lambda: AsyncMock()
    application.dependency_overrides[get_service] = lambda: _StubService()
    return application


@pytest.fixture
def _bypass_permission_check(monkeypatch):
    """Bypass the identity/permission lookup so this test exercises routing
    only, not the (already-tested-elsewhere) auth/permission subsystem."""

    async def _always_allow(*args, **kwargs):
        return True

    monkeypatch.setattr("app.dependencies.require_permission", _always_allow)


@pytest.mark.asyncio
async def test_mounted_paths_match_expected_frontend_paths(app, _bypass_permission_check):
    """The exact paths the frontend calls must resolve (not 404).

    This is the regression test for the double-prefix bug: before the fix,
    every one of these returned 404 because the live path required an extra
    leading `/review-queue` segment that the frontend never sent.
    """
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer test-token", "X-Tenant-Id": "t1"}
    expected_paths = [
        "/api/v1/master-data/review-queue/p3",
        "/api/v1/master-data/review-queue/p3/count",
        "/api/v1/master-data/review-queue/short-cr",
        "/api/v1/master-data/review-queue/triage",
        "/api/v1/master-data/review-queue/triage/counts",
        "/api/v1/master-data/review-queue/export/p3",
        "/api/v1/master-data/review-queue/export/short-cr",
        "/api/v1/master-data/review-queue/export/triage",
    ]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for path in expected_paths:
            response = await client.get(path, headers=headers, timeout=5)
            assert response.status_code == 200, f"{path} returned {response.status_code}, expected 200"

        # The OLD (buggy) doubled path must NOT be the one that resolves.
        stale = await client.get(
            "/api/v1/master-data/review-queue/review-queue/p3", headers=headers, timeout=5
        )
        assert stale.status_code == 404, (
            "the old double-prefixed path should no longer resolve; "
            f"got {stale.status_code}"
        )


@pytest.mark.asyncio
async def test_disposition_post_path_matches_frontend(app, _bypass_permission_check):
    """POST .../{queue_type}/{subject_key}/disposition resolves at the single-segment path."""
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer test-token", "X-Tenant-Id": "t1"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/master-data/review-queue/P3_PAIR/1%3A2/disposition",
            json={"disposition": "MATCH", "reviewer": "test-reviewer"},
            headers=headers,
            timeout=5,
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["queue_type"] == "P3_PAIR"
        assert body["disposition"] == "MATCH"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
