"""Tests for Revenue Forecast Domain — Time-series, Combined, Breakdowns."""

from datetime import datetime, timedelta, timezone

import pytest

from domains.revenue.forecast.models import (
    CombinedForecast, ForecastBreakdown, ForecastExplanation, ForecastLine,
    ForecastScenario, ForecastSnapshot, ForecastSnapshotStatus,
    TimeSeriesDataPoint, TimeSeriesForecast,
)
from domains.revenue.forecast.engine import CommercialInput, ForecastEngine
from domains.revenue.forecast.in_memory_repo import InMemoryForecastRepository
from domains.revenue.forecast.service import ForecastService


# ── Existing model tests ──

def test_forecast_snapshot_rollups():
    snap = ForecastSnapshot(id="s1", tenant_id="t1", lines=[
        ForecastLine(scenario=ForecastScenario.MOST_LIKELY, expected_revenue=50000, confidence=0.8, risk=0.1, weighted_revenue=40000),
        ForecastLine(scenario=ForecastScenario.MOST_LIKELY, expected_revenue=30000, confidence=0.6, risk=0.2, weighted_revenue=15000),
    ])
    assert snap.total_expected_revenue == 80000
    assert snap.total_weighted_revenue == 55000
    assert round(snap.overall_confidence, 2) == 0.70
    assert round(snap.overall_risk, 2) == 0.15


def test_forecast_by_scenario():
    snap = ForecastSnapshot(id="s1", tenant_id="t1", lines=[
        ForecastLine(scenario=ForecastScenario.COMMIT, expected_revenue=10000),
        ForecastLine(scenario=ForecastScenario.BEST_CASE, expected_revenue=50000),
    ])
    assert len(snap.by_scenario(ForecastScenario.COMMIT)) == 1
    assert snap.by_scenario(ForecastScenario.COMMIT)[0].expected_revenue == 10000


def test_forecast_does_not_own_facts():
    snap = ForecastSnapshot(id="s1", tenant_id="t1")
    assert not hasattr(snap, "opportunity_value")
    assert not hasattr(snap, "grand_total")


# ── Engine ──

def test_engine_predicts_multiple_scenarios():
    engine = ForecastEngine()
    inputs = [
        CommercialInput(
            opportunity_id="opp-1", opportunity_value=100000, opportunity_probability=0.5,
            opportunity_stage="negotiation", has_recent_activity=True, days_in_stage=10,
            sla_days=30, historical_win_rate=0.7,
        ),
        CommercialInput(
            opportunity_id="opp-2", opportunity_value=50000, opportunity_probability=0.25,
            opportunity_stage="qualification", has_recent_activity=False, days_in_stage=5,
            sla_days=14, historical_win_rate=0.7,
        ),
    ]

    snap = engine.predict(inputs)
    assert len(snap.lines) == 8  # 4 scenarios x 2 inputs
    assert snap.total_expected_revenue > 0

    scenarios = set(l.scenario for l in snap.lines)
    assert ForecastScenario.COMMIT in scenarios
    assert ForecastScenario.BEST_CASE in scenarios
    assert ForecastScenario.MOST_LIKELY in scenarios
    assert ForecastScenario.WORST_CASE in scenarios


def test_engine_explainable():
    engine = ForecastEngine()
    inp = CommercialInput(
        opportunity_id="opp-1", opportunity_value=100000, opportunity_probability=0.5,
        opportunity_stage="negotiation", has_recent_activity=True, days_in_stage=10,
        sla_days=30, quote_approved=True, contract_signed=True, historical_win_rate=0.7,
    )
    snap = engine.predict([inp])
    line = snap.by_scenario(ForecastScenario.MOST_LIKELY)[0]

    factors = {e.factor for e in line.explanations}
    assert "weighted_revenue" in factors
    assert "activity_signal" in factors
    assert "quote_approved" in factors
    assert "contract_signed" in factors


def test_engine_contract_locks_revenue():
    engine = ForecastEngine()
    with_contract = CommercialInput(opportunity_id="o1", opportunity_value=100000, opportunity_probability=0.5,
                                     contract_signed=True, contract_value=100000, historical_win_rate=0.7)
    without = CommercialInput(opportunity_id="o2", opportunity_value=100000, opportunity_probability=0.5,
                              contract_signed=False, historical_win_rate=0.7)

    snap = engine.predict([with_contract, without])
    with_line = snap.by_scenario(ForecastScenario.MOST_LIKELY)[0]
    without_line = snap.by_scenario(ForecastScenario.MOST_LIKELY)[1]
    assert with_line.confidence > without_line.confidence


def test_engine_overdue_penalty():
    engine = ForecastEngine()
    overdue = CommercialInput(opportunity_id="o1", opportunity_value=100000, opportunity_probability=0.5,
                              days_in_stage=60, sla_days=30, historical_win_rate=0.7)
    healthy = CommercialInput(opportunity_id="o2", opportunity_value=100000, opportunity_probability=0.5,
                              days_in_stage=5, sla_days=30, historical_win_rate=0.7)

    snap = engine.predict([overdue, healthy])
    overdue_line = snap.by_scenario(ForecastScenario.MOST_LIKELY)[0]
    healthy_line = snap.by_scenario(ForecastScenario.MOST_LIKELY)[1]
    assert overdue_line.risk > healthy_line.risk


# ── Time-Series Tests ──

def test_time_series_basic():
    engine = ForecastEngine()
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    data = [
        TimeSeriesDataPoint(date=base + timedelta(days=30 * i), value=100000 + i * 10000)
        for i in range(6)
    ]
    result = engine.time_series_forecast(data, horizon_months=3)
    assert result.predicted_value > 0
    assert result.slope > 0
    assert result.data_points_used == 6
    assert result.confidence_lower < result.predicted_value < result.confidence_upper


def test_time_series_insufficient_data():
    engine = ForecastEngine()
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    data = [TimeSeriesDataPoint(date=base, value=100000)]
    result = engine.time_series_forecast(data, horizon_months=3)
    assert result.data_points_used == 1
    assert result.predicted_value == 0.0


def test_time_series_two_points():
    engine = ForecastEngine()
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    data = [
        TimeSeriesDataPoint(date=base, value=100000),
        TimeSeriesDataPoint(date=base + timedelta(days=30), value=120000),
    ]
    result = engine.time_series_forecast(data, horizon_months=3)
    assert result.slope > 0
    assert result.predicted_value > 120000


def test_time_series_flat():
    engine = ForecastEngine()
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    data = [
        TimeSeriesDataPoint(date=base + timedelta(days=30 * i), value=100000)
        for i in range(6)
    ]
    result = engine.time_series_forecast(data, horizon_months=3)
    assert result.slope == 0.0
    assert result.r_squared == 0.0


def test_time_series_confidence_intervals():
    engine = ForecastEngine()
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    data = [
        TimeSeriesDataPoint(date=base + timedelta(days=30 * i), value=100000 + i * 5000)
        for i in range(12)
    ]
    result = engine.time_series_forecast(data, horizon_months=3)
    assert result.confidence_lower < result.predicted_value < result.confidence_upper
    assert result.r_squared > 0.8


# ── Combined Forecast Tests ──

def test_combined_forecast():
    engine = ForecastEngine()
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    historical = [
        TimeSeriesDataPoint(date=base + timedelta(days=30 * i), value=80000 + i * 5000)
        for i in range(6)
    ]
    inputs = [
        CommercialInput(opportunity_id="o1", opportunity_value=200000, opportunity_probability=0.6,
                        historical_win_rate=0.7),
    ]
    result = engine.combined_forecast(inputs, historical, horizon_months=3)
    assert result.combined_value > 0
    assert result.confidence_lower < result.combined_value < result.confidence_upper


def test_combined_forecast_weights():
    engine = ForecastEngine()
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    historical = [
        TimeSeriesDataPoint(date=base + timedelta(days=30 * i), value=100000)
        for i in range(6)
    ]
    inputs = [
        CommercialInput(opportunity_id="o1", opportunity_value=200000, opportunity_probability=0.5,
                        historical_win_rate=0.7),
    ]
    ts_only = engine.combined_forecast(inputs, historical, ts_weight=1.0, pipeline_weight=0.0)
    pl_only = engine.combined_forecast(inputs, historical, ts_weight=0.0, pipeline_weight=1.0)
    assert ts_only.combined_value != pl_only.combined_value


def test_combined_empty_historical():
    engine = ForecastEngine()
    inputs = [
        CommercialInput(opportunity_id="o1", opportunity_value=200000, opportunity_probability=0.5,
                        historical_win_rate=0.7),
    ]
    result = engine.combined_forecast(inputs, [], horizon_months=3)
    assert result.combined_value > 0


# ── Breakdown Tests ──

def test_breakdown_by_rep():
    engine = ForecastEngine()
    inputs = [
        CommercialInput(opportunity_id="o1", opportunity_value=100000, opportunity_probability=0.5,
                        rep_id="rep-1", region="Riyadh", historical_win_rate=0.7),
        CommercialInput(opportunity_id="o2", opportunity_value=80000, opportunity_probability=0.5,
                        rep_id="rep-2", region="Jeddah", historical_win_rate=0.7),
        CommercialInput(opportunity_id="o3", opportunity_value=60000, opportunity_probability=0.5,
                        rep_id="rep-1", region="Riyadh", historical_win_rate=0.7),
    ]
    snap = engine.predict(inputs)
    breakdown = engine.breakdown(snap, "rep_id")
    assert len(breakdown) == 2
    assert breakdown[0].value == "rep-1"
    assert breakdown[0].line_count > breakdown[1].line_count


def test_breakdown_by_region():
    engine = ForecastEngine()
    inputs = [
        CommercialInput(opportunity_id="o1", opportunity_value=100000, opportunity_probability=0.5,
                        rep_id="rep-1", region="Riyadh", historical_win_rate=0.7),
        CommercialInput(opportunity_id="o2", opportunity_value=80000, opportunity_probability=0.5,
                        rep_id="rep-2", region="Riyadh", historical_win_rate=0.7),
    ]
    snap = engine.predict(inputs)
    breakdown = engine.breakdown(snap, "region")
    assert len(breakdown) == 1
    assert breakdown[0].value == "Riyadh"


def test_breakdown_by_product():
    engine = ForecastEngine()
    inputs = [
        CommercialInput(opportunity_id="o1", opportunity_value=100000, opportunity_probability=0.5,
                        product="CRM Pro", historical_win_rate=0.7),
        CommercialInput(opportunity_id="o2", opportunity_value=50000, opportunity_probability=0.5,
                        product="Analytics Plus", historical_win_rate=0.7),
    ]
    snap = engine.predict(inputs)
    breakdown = engine.breakdown(snap, "product")
    assert len(breakdown) == 2


def test_breakdown_by_dimension():
    snap = ForecastSnapshot(id="s1", tenant_id="t1", lines=[
        ForecastLine(scenario=ForecastScenario.MOST_LIKELY, expected_revenue=50000,
                     confidence=0.8, weighted_revenue=40000, metadata={"rep_id": "r1"}),
        ForecastLine(scenario=ForecastScenario.MOST_LIKELY, expected_revenue=30000,
                     confidence=0.6, weighted_revenue=15000, metadata={"rep_id": "r1"}),
        ForecastLine(scenario=ForecastScenario.MOST_LIKELY, expected_revenue=20000,
                     confidence=0.4, weighted_revenue=10000, metadata={"rep_id": "r2"}),
    ])
    result = snap.by_dimension("rep_id", "r1")
    assert len(result) == 2


# ── Service Tests ──

@pytest.mark.asyncio
async def test_create_forecast_snapshot():
    repo = InMemoryForecastRepository()
    svc = ForecastService(repo)
    snap = await svc.create_forecast("t1", [
        CommercialInput(opportunity_id="opp-1", opportunity_value=100000, opportunity_probability=0.5,
                        historical_win_rate=0.7),
    ])
    assert snap.tenant_id == "t1"
    assert snap.status == ForecastSnapshotStatus.CALCULATED
    assert snap.total_expected_revenue > 0


@pytest.mark.asyncio
async def test_snapshot_immutability():
    repo = InMemoryForecastRepository()
    svc = ForecastService(repo)
    snap = await svc.create_forecast("t1", [
        CommercialInput(opportunity_id="opp-1", opportunity_value=100000, opportunity_probability=0.5,
                        historical_win_rate=0.7),
    ])
    original_revenue = snap.total_expected_revenue
    snap = await svc.finalize(snap.id)
    assert snap.status == ForecastSnapshotStatus.FINALIZED
    snap = await svc.get(snap.id)
    assert snap.total_expected_revenue == original_revenue


@pytest.mark.asyncio
async def test_explain():
    repo = InMemoryForecastRepository()
    svc = ForecastService(repo)
    snap = await svc.create_forecast("t1", [
        CommercialInput(opportunity_id="opp-1", opportunity_value=100000, opportunity_probability=0.5,
                        has_recent_activity=True, quote_approved=True, historical_win_rate=0.7),
    ])
    explanations = svc.explain(snap)
    assert len(explanations) > 0
    assert "explanations" in explanations[0]


@pytest.mark.asyncio
async def test_kpis():
    repo = InMemoryForecastRepository()
    svc = ForecastService(repo)
    await svc.create_forecast("t1", [
        CommercialInput(opportunity_id="opp-1", opportunity_value=100000, opportunity_probability=0.5,
                        historical_win_rate=0.7),
    ])
    await svc.create_forecast("t1", [
        CommercialInput(opportunity_id="opp-2", opportunity_value=50000, opportunity_probability=0.8,
                        historical_win_rate=0.7),
    ])
    kpis = await svc.kpis("t1")
    assert kpis.total_snapshots == 2
    assert kpis.latest_expected_revenue > 0


@pytest.mark.asyncio
async def test_no_write_to_commercial_domains():
    repo = InMemoryForecastRepository()
    svc = ForecastService(repo)
    commercial_data = {"opportunity_value": 100000}
    snap = await svc.create_forecast("t1", [
        CommercialInput(opportunity_id="opp-1", opportunity_value=commercial_data["opportunity_value"],
                        opportunity_probability=0.5, historical_win_rate=0.7),
    ])
    assert commercial_data["opportunity_value"] == 100000
    assert not hasattr(snap, "opportunity_value")
