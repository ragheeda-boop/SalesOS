"""Tests for Pipeline Analytics — velocity, conversion, health_map, forecast."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

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

    def one_or_none(self):
        return FakeMapping(self._one) if self._one else None

    def all(self):
        return [FakeMapping(r) for r in self._rows]


class FakeResult:
    def __init__(self, mappings_obj=None):
        self._mappings = mappings_obj or FakeMappings()

    def mappings(self):
        return self._mappings


# ── Fixtures ─────────────────────────────────────────────────────────────────

VELOCITY_ROWS = [
    {"stage_name": "prospecting", "avg_days": 5.2, "entry_count": 30},
    {"stage_name": "qualification", "avg_days": 10.1, "entry_count": 25},
    {"stage_name": "proposal", "avg_days": 7.5, "entry_count": 20},
    {"stage_name": "negotiation", "avg_days": 12.3, "entry_count": 15},
]

CONVERSION_ROWS = [
    {"stage": "prospecting", "cnt": 100},
    {"stage": "qualification", "cnt": 60},
    {"stage": "proposal", "cnt": 30},
    {"stage": "closed_won", "cnt": 10},
]

HEALTH_ROWS = [
    {
        "id": "opp-1",
        "name": "Deal A",
        "stage": "proposal",
        "value": 500000,
        "currency": "SAR",
        "health_score": 0.85,
        "owner_id": "user-1",
    },
    {
        "id": "opp-2",
        "name": "Deal B",
        "stage": "qualification",
        "value": 200000,
        "currency": "SAR",
        "health_score": 0.50,
        "owner_id": "user-2",
    },
    {
        "id": "opp-3",
        "name": "Deal C",
        "stage": "negotiation",
        "value": 100000,
        "currency": "SAR",
        "health_score": 0.30,
        "owner_id": None,
    },
]

FORECAST_ROWS = [
    {
        "currency": "SAR",
        "total_count": 15,
        "total_value": 2500000.0,
        "weighted_value": 1500000.0,
        "avg_probability": 0.60,
    }
]


def _make_session(velocity_rows=None, conversion_rows=None, health_rows=None, forecast_rows=None):
    """Return a mock session that returns different data based on the SQL query."""

    async def execute(sql_str, params=None):
        text = str(sql_str)
        if "stage_entries" in text or "AVG(EXTRACT" in text:
            return FakeResult(
                FakeMappings(rows=velocity_rows if velocity_rows is not None else VELOCITY_ROWS)
            )
        elif "stage_counts" in text or ("stage" in text and "GROUP BY stage" in text):
            return FakeResult(
                FakeMappings(
                    rows=conversion_rows if conversion_rows is not None else CONVERSION_ROWS
                )
            )
        elif "health_score" in text or "company_features" in text:
            return FakeResult(
                FakeMappings(rows=health_rows if health_rows is not None else HEALTH_ROWS)
            )
        elif "GROUP BY COALESCE(NULLIF(UPPER(TRIM(currency))" in text:
            return FakeResult(
                FakeMappings(rows=forecast_rows if forecast_rows is not None else FORECAST_ROWS)
            )
        return FakeResult(FakeMappings())

    session = AsyncMock()
    session.execute = execute
    return session


@pytest.fixture
def analytics():
    return PipelineAnalytics(db=_make_session(), tenant_id="tenant-1")


# ── Tests: velocity ──────────────────────────────────────────────────────────


class TestVelocity:
    async def test_returns_dict(self, analytics):
        result = await analytics.velocity()
        assert isinstance(result, dict)

    async def test_has_stage_keys(self, analytics):
        result = await analytics.velocity()
        assert "prospecting" in result
        assert "qualification" in result

    async def test_has_avg_days(self, analytics):
        result = await analytics.velocity()
        assert result["prospecting"]["avg_days"] == 5.2

    async def test_has_entries(self, analytics):
        result = await analytics.velocity()
        assert result["prospecting"]["entries"] == 30

    async def test_empty_velocity(self):
        session = _make_session(velocity_rows=[])
        analytics = PipelineAnalytics(db=session, tenant_id="t-1")
        result = await analytics.velocity()
        assert result == {}


# ── Tests: conversion_rates ──────────────────────────────────────────────────


class TestConversionRates:
    async def test_returns_dict(self, analytics):
        result = await analytics.conversion_rates()
        assert isinstance(result, dict)

    async def test_has_stage_arrow_keys(self, analytics):
        result = await analytics.conversion_rates()
        assert any("→" in k for k in result)

    async def test_conversion_bounded(self, analytics):
        result = await analytics.conversion_rates()
        for _k, v in result.items():
            assert 0 <= v <= 10  # Allow >1 if stage counts increase

    async def test_prospecting_to_qualification(self, analytics):
        result = await analytics.conversion_rates()
        key = "prospecting→qualification"
        assert key in result
        assert abs(result[key] - 0.6) < 0.01

    async def test_empty_conversion(self):
        session = _make_session(conversion_rows=[])
        analytics = PipelineAnalytics(db=session, tenant_id="t-1")
        result = await analytics.conversion_rates()
        assert result == {}


# ── Tests: health_map ────────────────────────────────────────────────────────


class TestHealthMap:
    async def test_returns_list(self, analytics):
        result = await analytics.health_map()
        assert isinstance(result, list)

    async def test_healthy_opportunity(self, analytics):
        result = await analytics.health_map()
        healthy = [h for h in result if h["health"] == "healthy"]
        assert len(healthy) >= 1
        assert healthy[0]["health_score"] >= 0.7

    async def test_at_risk_opportunity(self, analytics):
        result = await analytics.health_map()
        at_risk = [h for h in result if h["health"] == "at_risk"]
        assert len(at_risk) >= 1
        assert 0.4 <= at_risk[0]["health_score"] < 0.7

    async def test_critical_opportunity(self, analytics):
        result = await analytics.health_map()
        critical = [h for h in result if h["health"] == "critical"]
        assert len(critical) >= 1
        assert critical[0]["health_score"] < 0.4

    async def test_has_required_fields(self, analytics):
        result = await analytics.health_map()
        for item in result:
            assert "opportunity_id" in item
            assert "name" in item
            assert "stage" in item
            assert "value" in item
            assert "currency" in item
            assert "health" in item
            assert "health_score" in item

    async def test_health_values_are_valid(self, analytics):
        result = await analytics.health_map()
        for item in result:
            assert item["health"] in ("healthy", "at_risk", "critical", "unknown")

    async def test_missing_probability_is_unknown_not_defaulted(self):
        rows = [
            {
                "id": "opp-unknown",
                "name": "No probability",
                "stage": "prospecting",
                "value": 1000,
                "health_score": None,
                "owner_id": "user-1",
            }
        ]
        analytics = PipelineAnalytics(db=_make_session(health_rows=rows), tenant_id="tenant-1")

        result = await analytics.health_map()

        assert result[0]["health"] == "unknown"
        assert result[0]["health_score"] is None

    async def test_owner_field(self, analytics):
        result = await analytics.health_map()
        has_owner = [h for h in result if h.get("owner")]
        assert len(has_owner) >= 1

    async def test_missing_owner_defaults_empty(self, analytics):
        result = await analytics.health_map()
        no_owner = [h for h in result if h["owner"] == ""]
        assert len(no_owner) >= 1


# ── Tests: forecast ──────────────────────────────────────────────────────────


class TestForecast:
    async def test_returns_dict(self, analytics):
        result = await analytics.forecast()
        assert isinstance(result, dict)

    async def test_has_best_case(self, analytics):
        result = await analytics.forecast()
        assert "best_case" in result
        assert result["best_case"] == 2500000.0
        assert result["currency"] == "SAR"

    async def test_has_commit(self, analytics):
        result = await analytics.forecast()
        assert "commit" in result
        assert result["commit"] == 1500000.0

    async def test_has_pipeline(self, analytics):
        result = await analytics.forecast()
        assert "pipeline" in result
        assert result["pipeline"] == 2500000.0

    async def test_has_gap(self, analytics):
        result = await analytics.forecast()
        assert "gap" in result
        assert result["gap"] == 1000000.0

    async def test_has_avg_probability(self, analytics):
        result = await analytics.forecast()
        assert "avg_probability" in result
        assert 0 <= result["avg_probability"] <= 1

    async def test_has_total_deals(self, analytics):
        result = await analytics.forecast()
        assert "total_deals" in result
        assert result["total_deals"] == 15

    async def test_commit_leq_pipeline(self, analytics):
        result = await analytics.forecast()
        assert result["commit"] <= result["pipeline"]

    async def test_forecast_groups_values_by_currency(self):
        rows = [
            {
                "currency": "SAR",
                "total_count": 2,
                "total_value": 1000,
                "weighted_value": 500,
                "avg_probability": 0.5,
            },
            {
                "currency": "USD",
                "total_count": 1,
                "total_value": 900,
                "weighted_value": 450,
                "avg_probability": 0.5,
            },
        ]
        result = await PipelineAnalytics(
            db=_make_session(forecast_rows=rows), tenant_id="tenant-1"
        ).forecast()

        assert result["currency"] is None
        assert result["pipeline"] is None
        assert result["commit"] is None
        assert result["total_deals"] == 3
        assert result["by_currency"] == [
            {
                "currency": "SAR",
                "best_case": 1000.0,
                "commit": 500.0,
                "pipeline": 1000.0,
                "gap": 500.0,
                "avg_probability": 0.5,
                "total_deals": 2,
            },
            {
                "currency": "USD",
                "best_case": 900.0,
                "commit": 450.0,
                "pipeline": 900.0,
                "gap": 450.0,
                "avg_probability": 0.5,
                "total_deals": 1,
            },
        ]

    async def test_forecast_has_no_currency_and_null_money_values_when_empty(self):
        result = await PipelineAnalytics(
            db=_make_session(forecast_rows=[]), tenant_id="tenant-1"
        ).forecast()

        assert result["currency"] is None
        assert result["pipeline"] is None
        assert result["total_deals"] == 0
        assert result["by_currency"] == []
