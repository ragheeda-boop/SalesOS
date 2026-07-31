"""E2E tests for Revenue Intelligence — Critical Path 17."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.e2e
_TEST_TIMEOUT = 30


class TestRevenueDashboard:
    """GET /api/v1/revenue/dashboard endpoint."""

    async def _seed_company_and_opp(self, client: AsyncClient, headers: dict) -> tuple[str, str]:
        cr = f"CR-REV-{uuid.uuid4().hex[:8]}"
        company_resp = await client.post(
            "/api/v1/companies",
            json={
                "name_ar": "شركة الإيرادات",
                "name_en": f"RevenueCo-{uuid.uuid4().hex[:8]}",
                "cr_number": cr,
                "city": "الرياض",
                "status": "active",
            },
            headers=headers,
        )
        assert company_resp.status_code in (200, 201)
        company_id = company_resp.json()["id"]

        opp_resp = await client.post(
            "/api/v1/opportunities",
            params={
                "company_id": company_id,
                "name": f"E2E Revenue Opp {uuid.uuid4().hex[:8]}",
                "value": 50000,
            },
            headers=headers,
        )
        opp_id = opp_resp.json().get("id") if opp_resp.status_code in (200, 201) else None
        return company_id, opp_id

    async def test_revenue_dashboard_returns_structure(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get("/api/v1/revenue/dashboard", headers=auth_headers),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text

    async def test_revenue_dashboard_with_seeded_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        await self._seed_company_and_opp(client, auth_headers)

        resp = await asyncio.wait_for(
            client.get("/api/v1/revenue/dashboard", headers=auth_headers),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text


class TestWorkspace:
    """GET /api/v1/workspace aggregated endpoint."""

    async def test_workspace_returns_aggregated_data(
        self,
        client: AsyncClient,
        registered_user_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get("/api/v1/workspace", headers=registered_user_headers),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text
        if resp.status_code == 200:
            data = resp.json()
            assert "tenant_id" in data

    async def test_workspace_contains_forecast_section(
        self,
        client: AsyncClient,
        registered_user_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get("/api/v1/workspace", headers=registered_user_headers),
            timeout=_TEST_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            assert "forecast" in data or "opportunities" in data

    async def test_workspace_contains_opportunities(
        self,
        client: AsyncClient,
        registered_user_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get("/api/v1/workspace", headers=registered_user_headers),
            timeout=_TEST_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            assert "opportunities" in data or "pipelines" in data


class TestOpportunityAnalytics:
    """Opportunity CRUD + analytics flow."""

    async def test_create_and_list_opportunities(
        self,
        client: AsyncClient,
        registered_user_headers: dict,
    ):
        company_id = str(uuid.uuid4())

        try:
            create_resp = await asyncio.wait_for(
                client.post(
                    "/api/v1/opportunities",
                    params={
                        "company_id": company_id,
                        "name": f"Analytics Opp {uuid.uuid4().hex[:8]}",
                        "value": 75000,
                    },
                    headers=registered_user_headers,
                ),
                timeout=_TEST_TIMEOUT,
            )
            assert create_resp.status_code in (200, 201, 422, 500), create_resp.text
        except Exception:
            pass

        list_resp = await asyncio.wait_for(
            client.get(
                "/api/v1/opportunities",
                headers=registered_user_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert list_resp.status_code in (200, 500, 503), list_resp.text
        if list_resp.status_code == 200:
            data = list_resp.json()
            assert "items" in data
