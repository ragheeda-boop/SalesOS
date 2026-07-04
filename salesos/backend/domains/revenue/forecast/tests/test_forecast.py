"""Tests for Forecast Domain — Projection Engine, not System of Record."""

from datetime import datetime, timedelta, timezone

import pytest

from domains.revenue.forecast.models import (
    ForecastExplanation, ForecastLine, ForecastScenario,
    ForecastSnapshot, ForecastSnapshotStatus,
)
from domains.revenue.forecast.engine import CommercialInput, ForecastEngine
from domains.revenue.forecast.in_memory_repo import InMemoryForecastRepository
from domains.revenue.forecast.service import ForecastService


# ── Models ──

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
    """Forecast must not have fields that duplicate commercial truths."""
    snap = ForecastSnapshot(id="s1", tenant_id="t1")
    assert not hasattr(snap, "opportunity_value")
    assert not hasattr(snap, "grand_total")
    assert not hasattr(snap, "unit_price")


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
    assert len(snap.lines) == 8  # 4 scenarios × 2 inputs
    assert snap.total_expected_revenue > 0

    # Verify all 4 scenarios exist
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

    # Should have explanations from multiple sources
    factors = {e.factor for e in line.explanations}
    assert "weighted_revenue" in factors
    assert "activity_signal" in factors
    assert "quote_approved" in factors
    assert "contract_signed" in factors


def test_engine_contract_locks_revenue():
    """Signed contracts should significantly boost confidence."""
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
    """Overdue stage should increase risk."""
    engine = ForecastEngine()
    overdue = CommercialInput(opportunity_id="o1", opportunity_value=100000, opportunity_probability=0.5,
                              days_in_stage=60, sla_days=30, historical_win_rate=0.7)
    healthy = CommercialInput(opportunity_id="o2", opportunity_value=100000, opportunity_probability=0.5,
                              days_in_stage=5, sla_days=30, historical_win_rate=0.7)

    snap = engine.predict([overdue, healthy])
    overdue_line = snap.by_scenario(ForecastScenario.MOST_LIKELY)[0]
    healthy_line = snap.by_scenario(ForecastScenario.MOST_LIKELY)[1]
    assert overdue_line.risk > healthy_line.risk


# ── Service ──

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

    # Finalize
    snap = await svc.finalize(snap.id)
    assert snap.status == ForecastSnapshotStatus.FINALIZED

    # Revenue should not change (immutable)
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
    assert len(explanations[0]["explanations"]) > 0


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
    """Forecast must never modify commercial domain data."""
    repo = InMemoryForecastRepository()
    svc = ForecastService(repo)

    commercial_data = {"opportunity_value": 100000}
    snap = await svc.create_forecast("t1", [
        CommercialInput(opportunity_id="opp-1", opportunity_value=commercial_data["opportunity_value"],
                        opportunity_probability=0.5, historical_win_rate=0.7),
    ])

    # Verify forecast didn't modify input
    assert commercial_data["opportunity_value"] == 100000
    # Verify snapshot doesn't have commercial fields
    assert not hasattr(snap, "opportunity_value")
