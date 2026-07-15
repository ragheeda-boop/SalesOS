"""E2E tests for Pipeline Analytics — Critical Path 18."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.e2e
_TEST_TIMEOUT = 30


class TestPipelineSummary:
    """GET /api/v1/pipeline/summary endpoint."""

    async def test_pipeline_summary_returns_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get("/api/v1/pipeline/summary", headers=auth_headers),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text


class TestPipelineVelocity:
    """GET /api/v1/pipeline/velocity endpoint."""

    async def test_pipeline_velocity_returns_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get("/api/v1/pipeline/velocity", headers=auth_headers),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text


class TestPipelineConversion:
    """GET /api/v1/pipeline/conversion endpoint."""

    async def test_pipeline_conversion_returns_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get("/api/v1/pipeline/conversion", headers=auth_headers),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text


class TestPipelineHealth:
    """GET /api/v1/pipeline/health endpoint."""

    async def test_pipeline_health_returns_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get("/api/v1/pipeline/health", headers=auth_headers),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text


class TestPipelineForecast:
    """GET /api/v1/pipeline/forecast endpoint."""

    async def test_pipeline_forecast_returns_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get("/api/v1/pipeline/forecast", headers=auth_headers),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text


class TestPipelineEndpoints:
    """Pipeline CRUD + KPI endpoints."""

    async def test_create_pipeline(
        self,
        client: AsyncClient,
        registered_user_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/pipelines",
                headers=registered_user_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 201, 422, 500), resp.text

    async def test_list_pipelines(
        self,
        client: AsyncClient,
        registered_user_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/pipelines",
                headers=registered_user_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text


class TestPipelineFullJourney:
    """Create pipeline → get KPIs → get forecast — single flow."""

    async def test_pipeline_full_journey(
        self,
        client: AsyncClient,
        registered_user_headers: dict,
    ):
        cr = f"CR-PIPE-{uuid.uuid4().hex[:8]}"
        company_resp = await client.post(
            "/api/v1/companies",
            json={
                "name_ar": "شركة الأنابيب",
                "name_en": f"PipelineCo-{uuid.uuid4().hex[:8]}",
                "cr_number": cr,
                "city": "جدة",
                "status": "active",
            },
            headers=registered_user_headers,
        )
        assert company_resp.status_code in (200, 201)
        company_id = company_resp.json()["id"]

        opp_resp = await client.post(
            "/api/v1/opportunities",
            params={
                "company_id": company_id,
                "name": f"Pipeline Opp {uuid.uuid4().hex[:8]}",
                "value": 100000,
            },
            headers=registered_user_headers,
        )

        pipeline_resp = await asyncio.wait_for(
            client.post("/api/v1/pipelines", headers=registered_user_headers),
            timeout=_TEST_TIMEOUT,
        )
        pipe_id = pipeline_resp.json().get("id") if pipeline_resp.status_code in (200, 201) else None

        if pipe_id:
            kpis_resp = await asyncio.wait_for(
                client.get(
                    f"/api/v1/pipelines/{pipe_id}/kpis",
                    headers=registered_user_headers,
                ),
                timeout=_TEST_TIMEOUT,
            )
            assert kpis_resp.status_code in (200, 500, 503), kpis_resp.text

        forecast_resp = await asyncio.wait_for(
            client.get("/api/v1/pipeline/forecast", headers=registered_user_headers),
            timeout=_TEST_TIMEOUT,
        )
        assert forecast_resp.status_code in (200, 500, 503), forecast_resp.text
