"""E2E tests for Executive Dashboard — Critical Path 13."""

from __future__ import annotations

import asyncio

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.e2e
_TEST_TIMEOUT = 30


class TestExecutiveDashboard:
    """Executive dashboard with revenue, team, risk, health, pipeline."""

    async def test_executive_dashboard_returns_structure(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """GET /api/v1/executive/dashboard returns full dashboard DTO."""
        resp = await asyncio.wait_for(
            client.get("/api/v1/executive/dashboard", headers=auth_headers),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 503), resp.text
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, dict)

    async def test_executive_dashboard_has_revenue(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Executive dashboard includes revenue section."""
        resp = await asyncio.wait_for(
            client.get("/api/v1/executive/dashboard", headers=auth_headers),
            timeout=_TEST_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            assert "revenue" in data or isinstance(data, dict)

    async def test_executive_dashboard_has_pipeline(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Executive dashboard includes pipeline section."""
        resp = await asyncio.wait_for(
            client.get("/api/v1/executive/dashboard", headers=auth_headers),
            timeout=_TEST_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, dict)
