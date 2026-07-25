"""Tests for Pipeline Analytics Engine — conversion, velocity, win/loss, stage duration."""

from datetime import datetime, timedelta, timezone

import pytest

from domains.commercial.pipeline.engine.analytics_engine import PipelineAnalyticsEngine
from domains.commercial.pipeline.contracts.forecast_models import PipelineHistoricalPeriod


# ── Conversion Rates ──

def test_conversion_rates_from_entries():
    engine = PipelineAnalyticsEngine()
    entries = [
        {"stage": "prospecting", "duration_days": 5, "next_stage": "qualification"},
        {"stage": "prospecting", "duration_days": 8, "next_stage": "qualification"},
        {"stage": "prospecting", "duration_days": 10, "next_stage": None},
        {"stage": "qualification", "duration_days": 7, "next_stage": "proposal"},
    ]
    opps = [{"id": "o1", "stage": "qualification", "status": "open"}]
    result = engine.compute(opportunities=opps, stage_entries=entries, tenant_id="t1")
    assert len(result.conversion_rates) > 0
    # prospecting → qualification: 2 out of 3
    rates = {f"{r.from_stage}→{r.to_stage}": r.rate for r in result.conversion_rates}
    assert rates.get("prospecting→qualification") == pytest.approx(2 / 3, abs=0.01)


def test_conversion_rates_approximation():
    engine = PipelineAnalyticsEngine()
    opps = [
        {"id": "o1", "stage": "prospecting", "status": "open"},
        {"id": "o2", "stage": "prospecting", "status": "open"},
        {"id": "o3", "stage": "qualification", "status": "open"},
        {"id": "o4", "stage": "proposal", "status": "open"},
    ]
    result = engine.compute(opportunities=opps, stage_entries=[], tenant_id="t1")
    assert len(result.conversion_rates) > 0


def test_empty_pipeline_analytics():
    engine = PipelineAnalyticsEngine()
    result = engine.compute(opportunities=[], stage_entries=[], tenant_id="t1")
    assert result.total_pipeline_value == 0
    assert result.active_deals == 0
    assert result.win_loss.total_won == 0
    assert result.win_loss.total_lost == 0


# ── Velocity ──

def test_velocity_from_entries():
    engine = PipelineAnalyticsEngine()
    entries = [
        {"stage": "prospecting", "duration_days": 5.0, "next_stage": "qualification"},
        {"stage": "qualification", "duration_days": 10.0, "next_stage": "proposal"},
        {"stage": "proposal", "duration_days": 15.0, "next_stage": "negotiation"},
    ]
    opps = [{"id": "o1", "stage": "proposal", "status": "open"}]
    result = engine.compute(opportunities=opps, stage_entries=entries, tenant_id="t1")
    assert result.velocity.avg_days_per_stage.get("prospecting") == 5.0
    assert result.velocity.avg_days_per_stage.get("qualification") == 10.0


def test_velocity_from_history():
    engine = PipelineAnalyticsEngine()
    engine.set_history([
        PipelineHistoricalPeriod(
            period_label="2026-Q1",
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            total_deals=10,
            closed_won=5,
            closed_lost=5,
            total_revenue=500000,
            avg_cycle_days=30.0,
        ),
    ])
    opps = [{"id": "o1", "stage": "proposal", "status": "open"}]
    result = engine.compute(opportunities=opps, stage_entries=[], tenant_id="t1")
    assert result.velocity.avg_cycle_days >= 0


# ── Stage Durations ──

def test_stage_durations():
    engine = PipelineAnalyticsEngine()
    entries = [
        {"stage": "prospecting", "duration_days": 5.0, "next_stage": "qualification"},
        {"stage": "prospecting", "duration_days": 10.0, "next_stage": "qualification"},
        {"stage": "qualification", "duration_days": 8.0, "next_stage": "proposal"},
    ]
    result = engine.compute(opportunities=[], stage_entries=entries, tenant_id="t1")
    assert len(result.stage_durations) == 2
    prosp = next(s for s in result.stage_durations if s.stage == "prospecting")
    assert prosp.avg_days == 7.5
    assert prosp.min_days == 5.0
    assert prosp.max_days == 10.0
    assert prosp.sample_count == 2


def test_stage_durations_empty():
    engine = PipelineAnalyticsEngine()
    result = engine.compute(opportunities=[], stage_entries=[], tenant_id="t1")
    assert len(result.stage_durations) == 0


# ── Win/Loss ──

def test_win_loss():
    engine = PipelineAnalyticsEngine()
    opps = [
        {"id": "o1", "stage": "closed_won", "status": "won"},
        {"id": "o2", "stage": "closed_won", "status": "won"},
        {"id": "o3", "stage": "closed_lost", "status": "lost"},
        {"id": "o4", "stage": "proposal", "status": "open", "days_inactive": 5},
        {"id": "o5", "stage": "qualification", "status": "open", "days_inactive": 20},
    ]
    result = engine.compute(opportunities=opps, stage_entries=[], tenant_id="t1")
    assert result.win_loss.win_rate == pytest.approx(2 / 3, abs=0.01)
    assert result.win_loss.loss_rate == pytest.approx(1 / 3, abs=0.01)
    assert result.win_loss.total_won == 2
    assert result.win_loss.total_lost == 1
    assert result.win_loss.total_stagnant == 1


def test_win_loss_all_active():
    engine = PipelineAnalyticsEngine()
    opps = [
        {"id": "o1", "stage": "proposal", "status": "open"},
        {"id": "o2", "stage": "qualification", "status": "open"},
    ]
    result = engine.compute(opportunities=opps, stage_entries=[], tenant_id="t1")
    assert result.win_loss.win_rate == 0.0
    assert result.win_loss.loss_rate == 0.0
    assert result.win_loss.total_active == 2


# ── Pipeline Value Over Time ──

def test_value_over_time():
    engine = PipelineAnalyticsEngine()
    opps = [
        {"id": "o1", "stage": "proposal", "status": "open", "value": 100000, "probability": 0.5,
         "created_at": "2026-01-15T10:00:00"},
        {"id": "o2", "stage": "qualification", "status": "open", "value": 50000, "probability": 0.25,
         "created_at": "2026-01-20T10:00:00"},
        {"id": "o3", "stage": "closed_won", "status": "won", "value": 200000, "probability": 1.0,
         "created_at": "2026-02-05T10:00:00"},
    ]
    result = engine.compute(opportunities=opps, stage_entries=[], tenant_id="t1")
    assert len(result.value_over_time) >= 1
    jan = next((v for v in result.value_over_time if v.month == "2026-01"), None)
    assert jan is not None
    assert jan.total_value == 150000


# ── Active Deals ──

def test_active_deals_excludes_terminal():
    engine = PipelineAnalyticsEngine()
    opps = [
        {"id": "o1", "stage": "proposal", "status": "open", "value": 100000, "probability": 0.5},
        {"id": "o2", "stage": "closed_won", "status": "won", "value": 200000, "probability": 1.0},
        {"id": "o3", "stage": "closed_lost", "status": "lost", "value": 150000, "probability": 0.0},
    ]
    result = engine.compute(opportunities=opps, stage_entries=[], tenant_id="t1")
    assert result.active_deals == 1
    assert result.total_pipeline_value == 100000
    assert result.total_weighted_value == 50000


# ── to_dict ──

def test_analytics_to_dict():
    engine = PipelineAnalyticsEngine()
    opps = [
        {"id": "o1", "stage": "proposal", "status": "open", "value": 100000, "probability": 0.5,
         "created_at": "2026-01-15T10:00:00"},
        {"id": "o2", "stage": "closed_won", "status": "won", "value": 200000, "probability": 1.0},
    ]
    result = engine.compute(opportunities=opps, stage_entries=[], tenant_id="t1")
    d = result.to_dict()
    assert "conversion_rates" in d
    assert "velocity" in d
    assert "stage_durations" in d
    assert "value_over_time" in d
    assert "win_loss" in d
    assert d["tenant_id"] == "t1"


# ── Stagnation ──

def test_stagnation_rate():
    engine = PipelineAnalyticsEngine()
    opps = [
        {"id": "o1", "stage": "proposal", "status": "open", "days_inactive": 20},
        {"id": "o2", "stage": "qualification", "status": "open", "days_inactive": 3},
        {"id": "o3", "stage": "negotiation", "status": "open", "days_inactive": 15},
    ]
    result = engine.compute(opportunities=opps, stage_entries=[], tenant_id="t1")
    assert result.win_loss.total_stagnant == 2
    assert result.win_loss.stagnation_rate == pytest.approx(2 / 3, abs=0.01)
