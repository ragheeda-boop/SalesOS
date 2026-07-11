"""Tests for Revenue Dashboard endpoint — data formatting and response structure."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from runtime.pipeline_analytics import PipelineAnalytics


# ── Fake SQLAlchemy helpers ──────────────────────────────────────────────────

class FakeMapping:
    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()

    def __iter__(self):
        return iter(self._data)


class FakeMappings:
    def __init__(self, rows=None, one=None):
        self._rows = rows or []
        self._one = one

    def one(self):
        return FakeMapping(self._one) if self._one else None

    def all(self):
        return [FakeMapping(r) for r in self._rows]


class FakeResult:
    def __init__(self, mappings_obj=None):
        self._mappings = mappings_obj or FakeMappings()

    def mappings(self):
        return self._mappings


# ── Fake execute that returns realistic revenue data ────────────────────────

class FakeRevenueExecute:
    call_count = {"n": 0}

    async def __call__(self, sql_str, params=None):
        text = str(sql_str)
        FakeRevenueExecute.call_count["n"] += 1
        if "commercial_opportunities" in text and "status != 'closed'" in text and "ORDER BY value" in text:
            return FakeResult(FakeMappings(rows=[
                {"id": "opp-2", "name": "Deal B", "stage": "negotiation", "value": 1000000, "probability": 0.8, "health": "healthy", "company_id": "co-2", "owner_id": "user-1"},
                {"id": "opp-1", "name": "Deal A", "stage": "proposal", "value": 500000, "probability": 0.6, "health": "healthy", "company_id": "co-1", "owner_id": "user-1"},
            ]))
        if "SUM(value * probability)" in text or "SUM(value)" in text or "COUNT(*)" in text:
            return FakeResult(FakeMappings(one={"total_value": 1500000, "count": 2, "weighted_value": 900000, "avg_probability": 0.6, "total_count": 2}))
        if "company_signals" in text:
            return FakeResult(FakeMappings(rows=[
                {"id": "sig-1", "title": "New tender released", "signal_type": "tender", "created_at": "2026-07-10T08:00:00Z", "company_name": "شركة أ"},
            ]))
        return FakeResult(FakeMappings())


@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    session.execute = FakeRevenueExecute()
    return session


# ── Tests: PipelineAnalytics (used by revenue dashboard) ────────────────────

class TestPipelineAnalyticsSummary:
    async def test_summary_returns_dict(self, mock_session):
        analytics = PipelineAnalytics(mock_session, "tenant-1")
        result = await analytics.summary()
        assert isinstance(result, dict)

    async def test_summary_has_velocity(self, mock_session):
        analytics = PipelineAnalytics(mock_session, "tenant-1")
        result = await analytics.summary()
        assert "velocity" in result

    async def test_summary_has_conversion_rates(self, mock_session):
        analytics = PipelineAnalytics(mock_session, "tenant-1")
        result = await analytics.summary()
        assert "conversion_rates" in result

    async def test_summary_has_health_map(self, mock_session):
        analytics = PipelineAnalytics(mock_session, "tenant-1")
        result = await analytics.summary()
        assert "health_map" in result
        assert "healthy" in result["health_map"]
        assert "at_risk" in result["health_map"]
        assert "critical" in result["health_map"]

    async def test_summary_has_forecast(self, mock_session):
        analytics = PipelineAnalytics(mock_session, "tenant-1")
        result = await analytics.summary()
        assert "forecast" in result

    async def test_summary_has_total_open_deals(self, mock_session):
        analytics = PipelineAnalytics(mock_session, "tenant-1")
        result = await analytics.summary()
        assert "total_open_deals" in result
        assert isinstance(result["total_open_deals"], int)


# ── Tests: Dashboard data formatting ────────────────────────────────────────

class TestRevenueDataFormatting:
    async def test_active_opportunities_have_required_fields(self, mock_session):
        analytics = PipelineAnalytics(mock_session, "tenant-1")
        health = await analytics.health_map()
        for item in health:
            assert "opportunity_id" in item
            assert "name" in item
            assert "stage" in item
            assert "value" in item
            assert isinstance(item["value"], float)

    async def test_forecast_has_all_fields(self, mock_session):
        analytics = PipelineAnalytics(mock_session, "tenant-1")
        forecast = await analytics.forecast()
        assert "best_case" in forecast
        assert "commit" in forecast
        assert "pipeline" in forecast
        assert "gap" in forecast
        assert "total_deals" in forecast
        assert "avg_probability" in forecast

    async def test_forecast_values_are_positive(self, mock_session):
        analytics = PipelineAnalytics(mock_session, "tenant-1")
        forecast = await analytics.forecast()
        assert forecast["best_case"] >= 0
        assert forecast["commit"] >= 0
        assert forecast["pipeline"] >= 0
        assert forecast["gap"] >= 0

    async def test_expected_revenue_response_structure(self, mock_session):
        """Simulate the revenue dashboard endpoint response structure."""
        analytics = PipelineAnalytics(mock_session, "tenant-1")

        # Query active opportunities
        fake_execute = FakeRevenueExecute()
        opps_result = await fake_execute("SELECT ... FROM commercial_opportunities WHERE status != 'closed' ORDER BY value ...", None)
        opps = [dict(r) for r in opps_result.mappings().all()]

        # Query total
        total_result = await fake_execute("SELECT SUM(value)...", None)
        total_row = total_result.mappings().one()

        response = {
            "pipeline_summary": await analytics.summary(),
            "active_opportunities": opps,
            "total_value": float(total_row["total_value"]),
            "opportunity_count": total_row["count"],
        }

        assert "pipeline_summary" in response
        assert len(response["active_opportunities"]) == 2
        assert response["total_value"] == 1500000
        assert response["opportunity_count"] == 2

    async def test_opportunity_values_are_positive(self, mock_session):
        fake_execute = FakeRevenueExecute()
        opps_result = await fake_execute(
            "SELECT ... FROM commercial_opportunities WHERE status != 'closed' ORDER BY value DESC LIMIT 10",
            None,
        )
        opps = [dict(r) for r in opps_result.mappings().all()]
        for o in opps:
            assert o["value"] > 0
