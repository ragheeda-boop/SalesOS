"""E2E tests for Employee 360 — Critical Path 9."""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio
from httpx import AsyncClient

pytestmark = pytest.mark.e2e
_TEST_TIMEOUT = 30


class TestEmployee360:
    """Employee 360 view — profile, scoring, signals."""

    async def test_employee_me_360_returns_profile(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """GET /api/v1/employees/me/360 returns full employee view."""
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/employees/me/360",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "profile" in data
        if data["profile"]:
            assert isinstance(data["profile"], dict)

    async def test_employee_360_has_portfolio(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Employee 360 includes portfolio data."""
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/employees/me/360",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "portfolio" in data
        portfolio = data["portfolio"] or {}
        assert isinstance(portfolio, dict)

    async def test_employee_360_has_kpis(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Employee 360 includes KPI data."""
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/employees/me/360",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "kpis" in data
        kpis = data["kpis"] or {}
        assert isinstance(kpis, dict)

    async def test_employee_360_has_ai_coach(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Employee 360 includes AI coach recommendations."""
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/employees/me/360",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "ai_coach" in data
        coach = data["ai_coach"] or []
        assert isinstance(coach, list)

    async def test_employee_360_has_timeline(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Employee 360 response includes timeline field (B-1)."""
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/employees/me/360",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "timeline" in data
        timeline = data["timeline"] or {}
        assert isinstance(timeline, dict)
        assert "events" in timeline

    async def test_employee_360_has_performance(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Employee 360 response includes performance field (B-1)."""
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/employees/me/360",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "performance" in data
        performance = data["performance"] or {}
        assert isinstance(performance, dict)

    @pytest_asyncio.fixture
    async def employee_id(self, client: AsyncClient, auth_headers: dict) -> str:
        """Get authenticated employee ID from /me/360."""
        resp = await asyncio.wait_for(
            client.get("/api/v1/employees/me/360", headers=auth_headers),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code == 200, resp.text
        return resp.json()["profile"]["id"]

    async def test_employee_timeline_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict,
        employee_id: str,
    ):
        """GET /employees/{id}/timeline returns paginated timeline with keyset cursor (B-2)."""
        resp = await asyncio.wait_for(
            client.get(
                f"/api/v1/employees/{employee_id}/timeline",
                params={"page_size": 5},
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404), f"Unexpected {resp.status_code}: {resp.text}"
        if resp.status_code == 200:
            data = resp.json()
            assert "events" in data
            assert isinstance(data["events"], list)

    async def test_employee_timeline_with_source_filter(
        self,
        client: AsyncClient,
        auth_headers: dict,
        employee_id: str,
    ):
        """Timeline endpoint accepts source filter (B-2)."""
        resp = await asyncio.wait_for(
            client.get(
                f"/api/v1/employees/{employee_id}/timeline",
                params={"source": "crm", "page_size": 5},
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404), f"Unexpected {resp.status_code}: {resp.text}"

    async def test_employee_timeline_with_type_filter(
        self,
        client: AsyncClient,
        auth_headers: dict,
        employee_id: str,
    ):
        """Timeline endpoint accepts type filter (B-2)."""
        resp = await asyncio.wait_for(
            client.get(
                f"/api/v1/employees/{employee_id}/timeline",
                params={"type": "email_sent", "page_size": 5},
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404), f"Unexpected {resp.status_code}: {resp.text}"

    async def test_employee_performance_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict,
        employee_id: str,
    ):
        """GET /employees/{id}/performance returns performance insights (B-3)."""
        resp = await asyncio.wait_for(
            client.get(
                f"/api/v1/employees/{employee_id}/performance",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404), f"Unexpected {resp.status_code}: {resp.text}"
        if resp.status_code == 200:
            data = resp.json()
            assert "score_trend" in data
            assert "peer_comparison" in data
            assert "risk_flags" in data
            assert isinstance(data["score_trend"], list)
            assert isinstance(data["peer_comparison"], list)
            assert isinstance(data["risk_flags"], list)

    async def test_work_intelligence_me_returns_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """GET /api/v1/work-intelligence/me returns work analysis."""
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/work-intelligence/me",
                params={"period_days": 30},
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 403, 404, 503), f"Unexpected {resp.status_code}: {resp.text}"
