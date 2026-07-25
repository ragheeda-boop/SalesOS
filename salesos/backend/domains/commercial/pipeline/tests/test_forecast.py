"""Tests for Pipeline Forecast Engine — weighted, velocity, confidence, breakdowns."""

from datetime import datetime, timedelta, timezone

import pytest

from domains.commercial.pipeline.engine.forecast_engine import PipelineForecastEngine
from domains.commercial.pipeline.contracts.forecast_models import (
    ForecastBreakdown,
    ForecastMethod,
    ForecastSnapshot,
    PipelineHistoricalPeriod,
)


# ── Forecast Engine ──

def test_forecast_engine_creates_snapshot():
    engine = PipelineForecastEngine()
    opps = [
        {"id": "o1", "value": 100000, "probability": 0.5, "stage": "proposal", "status": "open", "owner_id": "rep1"},
        {"id": "o2", "value": 50000, "probability": 0.25, "stage": "qualification", "status": "open", "owner_id": "rep2"},
    ]
    snapshot = engine.forecast(opportunities=opps, tenant_id="t1")
    assert isinstance(snapshot, ForecastSnapshot)
    assert snapshot.tenant_id == "t1"
    assert snapshot.total_pipeline_value == 150000
    assert snapshot.total_weighted == 62500.0  # 100000*0.5 + 50000*0.25


def test_forecast_weighted_pipeline():
    engine = PipelineForecastEngine()
    opps = [
        {"id": "o1", "value": 200000, "probability": 0.75, "stage": "negotiation", "status": "open"},
        {"id": "o2", "value": 100000, "probability": 0.10, "stage": "prospecting", "status": "open"},
    ]
    snapshot = engine.forecast(opportunities=opps, tenant_id="t1")
    assert snapshot.total_weighted == 160000  # 200000*0.75 + 100000*0.10


def test_forecast_excludes_closed():
    engine = PipelineForecastEngine()
    opps = [
        {"id": "o1", "value": 100000, "probability": 0.5, "status": "open"},
        {"id": "o2", "value": 200000, "probability": 1.0, "status": "won"},
        {"id": "o3", "value": 150000, "probability": 0.0, "status": "lost"},
    ]
    snapshot = engine.forecast(opportunities=opps, tenant_id="t1")
    assert snapshot.total_pipeline_value == 100000
    assert snapshot.total_weighted == 50000


def test_forecast_with_history():
    engine = PipelineForecastEngine()
    engine.set_history([
        PipelineHistoricalPeriod(
            period_label="2026-Q1",
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            total_deals=10,
            closed_won=4,
            closed_lost=6,
            total_revenue=400000,
        ),
        PipelineHistoricalPeriod(
            period_label="2026-Q2",
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            total_deals=12,
            closed_won=5,
            closed_lost=7,
            total_revenue=500000,
        ),
    ])
    opps = [{"id": "o1", "value": 100000, "probability": 0.5, "status": "open"}]
    snapshot = engine.forecast(opportunities=opps, tenant_id="t1", horizon_months=3)
    assert snapshot.total_velocity > 0
    assert snapshot.total_combined > 0
    assert snapshot.overall_confidence > 0


def test_forecast_breakdown_by_rep():
    engine = PipelineForecastEngine()
    opps = [
        {"id": "o1", "value": 100000, "probability": 0.5, "status": "open", "owner_id": "alice"},
        {"id": "o2", "value": 80000, "probability": 0.25, "status": "open", "owner_id": "bob"},
        {"id": "o3", "value": 120000, "probability": 0.75, "status": "open", "owner_id": "alice"},
    ]
    snapshot = engine.forecast(opportunities=opps, tenant_id="t1")
    assert len(snapshot.by_rep) == 2
    alice = next(b for b in snapshot.by_rep if b.label == "alice")
    assert alice.total_pipeline_value == 220000
    assert alice.opportunity_count == 2


def test_forecast_breakdown_by_region():
    engine = PipelineForecastEngine()
    opps = [
        {"id": "o1", "value": 100000, "probability": 0.5, "status": "open", "region": "KSA"},
        {"id": "o2", "value": 80000, "probability": 0.25, "status": "open", "region": "UAE"},
    ]
    snapshot = engine.forecast(opportunities=opps, tenant_id="t1")
    assert len(snapshot.by_region) == 2
    regions = {b.label for b in snapshot.by_region}
    assert "KSA" in regions
    assert "UAE" in regions


def test_forecast_breakdown_by_product():
    engine = PipelineForecastEngine()
    opps = [
        {"id": "o1", "value": 100000, "probability": 0.5, "status": "open", "product": "Enterprise"},
        {"id": "o2", "value": 80000, "probability": 0.25, "status": "open", "product": "SMB"},
    ]
    snapshot = engine.forecast(opportunities=opps, tenant_id="t1")
    assert len(snapshot.by_product) == 2


def test_forecast_confidence_intervals():
    """CI is wider when win_rate > 0 (upside exists) and lower < combined."""
    engine = PipelineForecastEngine()
    opps = [
        {"id": "o1", "value": 100000, "probability": 0.5, "status": "open"},
        {"id": "o2", "value": 50000, "probability": 0.25, "status": "open"},
    ]
    snapshot = engine.forecast(opportunities=opps, tenant_id="t1")
    # Lower bound is always < combined (unless win_rate=1)
    assert snapshot.ci_lower <= snapshot.total_combined
    # Upper bound >= combined (upside based on win_rate)
    assert snapshot.ci_upper >= snapshot.total_combined


def test_forecast_empty_pipeline():
    engine = PipelineForecastEngine()
    snapshot = engine.forecast(opportunities=[], tenant_id="t1")
    assert snapshot.total_pipeline_value == 0
    assert snapshot.total_weighted == 0
    assert snapshot.total_combined == 0


def test_forecast_accuracy_range_string():
    engine = PipelineForecastEngine()
    opps = [
        {"id": "o1", "value": 100000, "probability": 0.5, "status": "open"},
    ]
    snapshot = engine.forecast(opportunities=opps, tenant_id="t1")
    assert "%" in snapshot.forecast_accuracy_range


def test_forecast_to_dict():
    engine = PipelineForecastEngine()
    opps = [
        {"id": "o1", "value": 100000, "probability": 0.5, "status": "open", "owner_id": "rep1", "region": "KSA"},
    ]
    snapshot = engine.forecast(opportunities=opps, tenant_id="t1")
    d = snapshot.to_dict()
    assert "id" in d
    assert "total_pipeline_value" in d
    assert "by_rep" in d
    assert "by_region" in d


def test_forecast_unassigned_owner():
    engine = PipelineForecastEngine()
    opps = [
        {"id": "o1", "value": 100000, "probability": 0.5, "status": "open"},
    ]
    snapshot = engine.forecast(opportunities=opps, tenant_id="t1")
    assert len(snapshot.by_rep) == 1
    assert snapshot.by_rep[0].label == "unassigned"


def test_forecast_combines_weighted_and_velocity():
    """When history exists, combined = weighted*0.6 + velocity*0.4."""
    engine = PipelineForecastEngine()
    engine.set_history([
        PipelineHistoricalPeriod(
            period_label="2026-Q1",
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            total_deals=10, closed_won=5, closed_lost=5,
            total_revenue=500000,
        ),
    ])
    opps = [
        {"id": "o1", "value": 200000, "probability": 0.5, "status": "open"},
    ]
    snapshot = engine.forecast(opportunities=opps, tenant_id="t1")
    assert snapshot.total_velocity > 0
    assert snapshot.total_combined > 0
    # Combined should be between weighted and velocity (blended)
    assert snapshot.total_combined != snapshot.total_weighted or snapshot.total_velocity == 0


def test_forecast_breakdown_confidence_interval():
    engine = PipelineForecastEngine()
    opps = [
        {"id": "o1", "value": 100000, "probability": 0.5, "status": "open", "owner_id": "alice"},
    ]
    snapshot = engine.forecast(opportunities=opps, tenant_id="t1")
    alice = snapshot.by_rep[0]
    assert alice.confidence_interval_lower < alice.combined_value
    assert alice.confidence_interval_upper > alice.combined_value
