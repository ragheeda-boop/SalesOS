"""Tests for Deal Scorer — multi-factor scoring, health, risk, recommendations."""

from datetime import datetime, timedelta, timezone

import pytest

from domains.commercial.pipeline.engine.deal_scoring import (
    DealHealth,
    DealRisk,
    DealScore,
    DealScoreFactor,
    DealScorer,
)


# ── Basic Scoring ──

def test_score_deal_basic():
    scorer = DealScorer()
    deal = {
        "id": "d1",
        "value": 100000,
        "probability": 0.5,
        "stage": "proposal",
        "age_days": 10,
        "days_in_stage": 5,
        "has_activity": True,
        "activity_count": 3,
    }
    score = scorer.score_deal(deal)
    assert isinstance(score, DealScore)
    assert score.deal_id == "d1"
    assert 0.0 <= score.overall_score <= 1.0
    assert len(score.factors) == 6


def test_score_deal_factors():
    scorer = DealScorer()
    deal = {
        "id": "d1",
        "value": 100000,
        "probability": 0.5,
        "stage": "proposal",
        "age_days": 10,
        "days_in_stage": 5,
        "has_activity": True,
        "activity_count": 3,
    }
    score = scorer.score_deal(deal)
    factor_keys = {f.key for f in score.factors}
    assert "deal_age" in factor_keys
    assert "stage_velocity" in factor_keys
    assert "historical_conversion" in factor_keys
    assert "deal_size" in factor_keys
    assert "probability_alignment" in factor_keys
    assert "activity_signal" in factor_keys


def test_score_deal_excellent_health():
    scorer = DealScorer()
    scorer.configure(avg_deal_size=100000, avg_cycle_days=30)
    deal = {
        "id": "d1",
        "value": 100000,
        "probability": 0.5,
        "stage": "proposal",
        "age_days": 5,
        "days_in_stage": 3,
        "has_activity": True,
        "activity_count": 5,
    }
    score = scorer.score_deal(deal)
    assert score.health in (DealHealth.EXCELLENT, DealHealth.GOOD)


def test_score_deal_at_risk_health():
    scorer = DealScorer()
    scorer.configure(avg_deal_size=100000, avg_cycle_days=30)
    deal = {
        "id": "d1",
        "value": 1000000,
        "probability": 0.10,
        "stage": "prospecting",
        "age_days": 120,
        "days_in_stage": 60,
        "has_activity": False,
        "activity_count": 0,
    }
    score = scorer.score_deal(deal)
    assert score.health in (DealHealth.POOR, DealHealth.AT_RISK, DealHealth.FAIR)


def test_score_deal_risk_levels():
    scorer = DealScorer()
    # Good deal
    good_deal = {
        "id": "d1", "value": 50000, "probability": 0.5, "stage": "proposal",
        "age_days": 10, "days_in_stage": 5, "has_activity": True, "activity_count": 5,
    }
    score = scorer.score_deal(good_deal)
    assert score.risk in (DealRisk.LOW, DealRisk.MEDIUM)


def test_score_deal_recommendation():
    scorer = DealScorer()
    deal = {
        "id": "d1", "value": 50000, "probability": 0.5, "stage": "proposal",
        "age_days": 10, "days_in_stage": 5, "has_activity": True, "activity_count": 3,
    }
    score = scorer.score_deal(deal)
    assert isinstance(score.recommendation, str)
    assert len(score.recommendation) > 0


# ── Batch Scoring ──

def test_score_batch():
    scorer = DealScorer()
    deals = [
        {"id": "d1", "value": 100000, "probability": 0.5, "stage": "proposal", "age_days": 10,
         "days_in_stage": 5, "has_activity": True, "activity_count": 3},
        {"id": "d2", "value": 50000, "probability": 0.25, "stage": "qualification", "age_days": 20,
         "days_in_stage": 10, "has_activity": False, "activity_count": 1},
    ]
    scores = scorer.score_batch(deals)
    assert len(scores) == 2
    assert all(isinstance(s, DealScore) for s in scores)


def test_score_batch_updates_avg_deal_size():
    scorer = DealScorer()
    deals = [
        {"id": "d1", "value": 200000, "probability": 0.5, "stage": "proposal"},
        {"id": "d2", "value": 100000, "probability": 0.25, "stage": "qualification"},
    ]
    scorer.score_batch(deals)
    assert scorer._avg_deal_size == 150000


# ── Factor Details ──

def test_deal_age_score():
    scorer = DealScorer()
    # New deal
    score = scorer.score_deal({"id": "d1", "age_days": 3, "stage": "prospecting", "probability": 0.1})
    age_factor = next(f for f in score.factors if f.key == "deal_age")
    assert age_factor.value == 1.0

    # Old deal
    score = scorer.score_deal({"id": "d2", "age_days": 100, "stage": "prospecting", "probability": 0.1})
    age_factor = next(f for f in score.factors if f.key == "deal_age")
    assert age_factor.value <= 0.4


def test_stage_velocity_score():
    scorer = DealScorer()
    # Fast-moving
    score = scorer.score_deal({"id": "d1", "days_in_stage": 2, "avg_stage_days": 10, "stage": "proposal", "probability": 0.5})
    vel_factor = next(f for f in score.factors if f.key == "stage_velocity")
    assert vel_factor.value >= 0.8

    # Slow-moving
    score = scorer.score_deal({"id": "d2", "days_in_stage": 25, "avg_stage_days": 10, "stage": "proposal", "probability": 0.5})
    vel_factor = next(f for f in score.factors if f.key == "stage_velocity")
    assert vel_factor.value <= 0.3


def test_deal_size_score():
    scorer = DealScorer()
    scorer.configure(avg_deal_size=100000)
    # Average-sized deal
    score = scorer.score_deal({"id": "d1", "value": 100000, "stage": "proposal", "probability": 0.5})
    size_factor = next(f for f in score.factors if f.key == "deal_size")
    assert size_factor.value >= 0.7

    # Outlier
    score = scorer.score_deal({"id": "d2", "value": 1000000, "stage": "proposal", "probability": 0.5})
    size_factor = next(f for f in score.factors if f.key == "deal_size")
    assert size_factor.value <= 0.7


def test_probability_alignment_score():
    scorer = DealScorer()
    # Aligned with stage
    score = scorer.score_deal({"id": "d1", "probability": 0.5, "stage": "proposal"})
    prob_factor = next(f for f in score.factors if f.key == "probability_alignment")
    assert prob_factor.value >= 0.7

    # Misaligned
    score = scorer.score_deal({"id": "d2", "probability": 0.1, "stage": "proposal"})
    prob_factor = next(f for f in score.factors if f.key == "probability_alignment")
    assert prob_factor.value <= 0.7


def test_activity_signal_score():
    scorer = DealScorer()
    # Strong activity
    score = scorer.score_deal({"id": "d1", "has_activity": True, "activity_count": 5, "stage": "proposal", "probability": 0.5})
    act_factor = next(f for f in score.factors if f.key == "activity_signal")
    assert act_factor.value == 1.0

    # No activity
    score = scorer.score_deal({"id": "d2", "has_activity": False, "activity_count": 0, "stage": "proposal", "probability": 0.5})
    act_factor = next(f for f in score.factors if f.key == "activity_signal")
    assert act_factor.value == 0.2


# ── to_dict ──

def test_score_to_dict():
    scorer = DealScorer()
    deal = {"id": "d1", "value": 50000, "probability": 0.5, "stage": "proposal",
            "age_days": 10, "days_in_stage": 5, "has_activity": True, "activity_count": 3}
    score = scorer.score_deal(deal)
    d = score.to_dict()
    assert d["deal_id"] == "d1"
    assert "overall_score" in d
    assert "health" in d
    assert "risk" in d
    assert "factors" in d
    assert "recommendation" in d
    assert len(d["factors"]) == 6


def test_top_factors():
    scorer = DealScorer()
    deal = {"id": "d1", "value": 50000, "probability": 0.5, "stage": "proposal",
            "age_days": 10, "days_in_stage": 5, "has_activity": True, "activity_count": 3}
    score = scorer.score_deal(deal)
    top = score.top_factors
    assert len(top) <= 3
    assert all(isinstance(f, DealScoreFactor) for f in top)
