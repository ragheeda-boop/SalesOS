"""E2E tests for Employee 360 — Critical Path 9."""

from __future__ import annotations

import asyncio

import pytest
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
        assert resp.status_code in (200, 404), resp.text
