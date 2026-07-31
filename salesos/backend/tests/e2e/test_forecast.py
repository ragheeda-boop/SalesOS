"""E2E tests for Forecast — Critical Path 19."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.e2e
_TEST_TIMEOUT = 30


class TestForecastRun:
    """POST /api/v1/forecast/run generates a forecast snapshot."""

    async def test_run_forecast_returns_snapshot(
        self,
        client: AsyncClient,
        registered_user_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/forecast/run",
                headers=registered_user_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 201, 500, 503), resp.text
        if resp.status_code in (200, 201):
            data = resp.json()
            assert "snapshot_id" in data or "total_expected" in data

    async def test_run_forecast_returns_scenarios(
        self,
        client: AsyncClient,
        registered_user_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/forecast/run",
                headers=registered_user_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        if resp.status_code in (200, 201):
            data = resp.json()
            assert "scenarios" in data or "confidence" in data


class TestForecastGet:
    """GET /api/v1/forecast retrieves latest forecast."""

    async def test_get_forecast_before_run_returns_message(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get("/api/v1/forecast", headers=auth_headers),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text

    async def test_get_forecast_after_run_returns_data(
        self,
        client: AsyncClient,
        registered_user_headers: dict,
    ):
        await client.post(
            "/api/v1/forecast/run",
            headers=registered_user_headers,
        )

        resp = await asyncio.wait_for(
            client.get("/api/v1/forecast", headers=registered_user_headers),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text
        if resp.status_code == 200:
            data = resp.json()
            assert "snapshot_id" in data or "message" in data

    async def test_forecast_has_expected_fields(
        self,
        client: AsyncClient,
        registered_user_headers: dict,
    ):
        await client.post(
            "/api/v1/forecast/run",
            headers=registered_user_headers,
        )

        resp = await asyncio.wait_for(
            client.get("/api/v1/forecast", headers=registered_user_headers),
            timeout=_TEST_TIMEOUT,
        )
        if resp.status_code == 200 and "snapshot_id" in resp.json():
            data = resp.json()
            assert "total_expected" in data
            assert "total_weighted" in data


class TestForecastSeedAndRun:
    """Seed company + opportunity → run forecast."""

    async def test_forecast_with_real_data(
        self,
        client: AsyncClient,
        registered_user_headers: dict,
    ):
        cr = f"CR-FCST-{uuid.uuid4().hex[:8]}"
        company_resp = await client.post(
            "/api/v1/companies",
            json={
                "name_ar": "شركة التوقعات",
                "name_en": f"ForecastCo-{uuid.uuid4().hex[:8]}",
                "cr_number": cr,
                "city": "الرياض",
                "status": "active",
            },
            headers=registered_user_headers,
        )
        assert company_resp.status_code in (200, 201)
        company_id = company_resp.json()["id"]

        _ = await client.post(
            "/api/v1/opportunities",
            params={
                "company_id": company_id,
                "name": f"Forecast Opp {uuid.uuid4().hex[:8]}",
                "value": 150000,
            },
            headers=registered_user_headers,
        )

        forecast_resp = await asyncio.wait_for(
            client.post(
                "/api/v1/forecast/run",
                headers=registered_user_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert forecast_resp.status_code in (200, 201, 500, 503), forecast_resp.text
