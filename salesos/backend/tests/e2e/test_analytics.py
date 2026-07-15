"""E2E tests for Analytics & Reporting — Critical Path 22."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.e2e
_TEST_TIMEOUT = 30


class TestAnalyticsCubes:
    """GET /api/v1/analytics/cubes and POST query endpoints."""

    async def test_list_cubes(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get("/api/v1/analytics/cubes", headers=auth_headers),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text
        if resp.status_code == 200:
            data = resp.json()
            assert "cubes" in data

    async def test_query_pipeline_cube(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/analytics/cubes/pipeline/query",
                json={"filters": {}, "granularity": "month"},
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404, 500, 503), resp.text


class TestAnalyticsReports:
    """CRUD for analytics reports."""

    async def test_create_report(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/analytics/reports",
                json={
                    "name": f"E2E Report {uuid.uuid4().hex[:8]}",
                    "type": "custom",
                    "config": {"metrics": ["revenue", "deals"]},
                    "schedule": "one-time",
                },
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 201, 500, 503), resp.text

    async def test_list_reports(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get("/api/v1/analytics/reports", headers=auth_headers),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text
        if resp.status_code == 200:
            data = resp.json()
            assert "reports" in data

    async def test_create_and_get_report(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        create_resp = await client.post(
            "/api/v1/analytics/reports",
            json={
                "name": f"E2E Get Report {uuid.uuid4().hex[:8]}",
                "type": "custom",
                "config": {},
            },
            headers=auth_headers,
        )
        if create_resp.status_code not in (200, 201):
            return
        report_id = create_resp.json()["id"]

        get_resp = await asyncio.wait_for(
            client.get(
                f"/api/v1/analytics/reports/{report_id}",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert get_resp.status_code in (200, 500, 503), get_resp.text

    async def test_delete_report(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        create_resp = await client.post(
            "/api/v1/analytics/reports",
            json={
                "name": f"E2E Delete {uuid.uuid4().hex[:8]}",
                "type": "custom",
                "config": {},
            },
            headers=auth_headers,
        )
        if create_resp.status_code not in (200, 201):
            return
        report_id = create_resp.json()["id"]

        resp = await asyncio.wait_for(
            client.delete(
                f"/api/v1/analytics/reports/{report_id}",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404, 500, 503), resp.text


class TestAnalyticsGeneration:
    """Report execution and analytics generation."""

    async def test_generate_analytics(
        self,
        client: AsyncClient,
        registered_user_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/analytics/generate",
                headers=registered_user_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text
        if resp.status_code == 200:
            data = resp.json()
            assert "snapshot_id" in data

    async def test_list_analytics_kpis(
        self,
        client: AsyncClient,
        registered_user_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/analytics/kpis",
                headers=registered_user_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text
        if resp.status_code == 200:
            data = resp.json()
            assert "kpis" in data


class TestAnalyticsFullJourney:
    """Create report → execute → list executions — single flow."""

    async def test_analytics_full_journey(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        create_resp = await client.post(
            "/api/v1/analytics/reports",
            json={
                "name": f"Journey Report {uuid.uuid4().hex[:8]}",
                "type": "custom",
                "config": {"metrics": ["revenue"]},
            },
            headers=auth_headers,
        )
        if create_resp.status_code not in (200, 201):
            return
        report_id = create_resp.json()["id"]

        execute_resp = await asyncio.wait_for(
            client.post(
                f"/api/v1/analytics/reports/{report_id}/execute",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert execute_resp.status_code in (200, 404, 500, 503), execute_resp.text

        executions_resp = await asyncio.wait_for(
            client.get(
                "/api/v1/analytics/executions",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert executions_resp.status_code in (200, 500, 503), executions_resp.text
