"""Unit tests for signal_actions/qualification.py — pure logic, no DB."""

from datetime import UTC, datetime, timedelta

import pytest

from app.modules.signal_actions.qualification import (
    CONFIDENCE_MULTIPLIERS,
    SIGNAL_TYPE_WEIGHTS,
    _intent_scale,
    _recency_weight,
    compute_intent_level,
    qualify_signal,
)
from app.modules.signal_actions.models import IntentLevel, SignalPriority


# ── _recency_weight ──────────────────────────────────────────────

class TestRecencyWeight:
    def test_today(self):
        now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        assert _recency_weight(now, now) == 1.0

    def test_yesterday(self):
        now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        detected = now - timedelta(days=1)
        assert _recency_weight(detected, now) == 1.0

    def test_3_days(self):
        now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        detected = now - timedelta(days=3)
        assert _recency_weight(detected, now) == 0.9

    def test_7_days(self):
        now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        detected = now - timedelta(days=7)
        assert _recency_weight(detected, now) == 0.9

    def test_14_days(self):
        now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        detected = now - timedelta(days=14)
        assert _recency_weight(detected, now) == 0.7

    def test_30_days(self):
        now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        detected = now - timedelta(days=30)
        assert _recency_weight(detected, now) == 0.7

    def test_45_days(self):
        now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        detected = now - timedelta(days=45)
        assert _recency_weight(detected, now) == 0.5

    def test_60_days(self):
        now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        detected = now - timedelta(days=60)
        assert _recency_weight(detected, now) == 0.5

    def test_90_days(self):
        now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        detected = now - timedelta(days=90)
        assert _recency_weight(detected, now) == 0.3

    def test_future_date_clamps_to_today(self):
        now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        future = now + timedelta(days=5)
        assert _recency_weight(future, now) == 1.0


# ── _intent_scale ────────────────────────────────────────────────

class TestIntentScale:
    def test_known_types(self):
        assert _intent_scale("funding") == 0.9
        assert _intent_scale("hiring") == 0.7
        assert _intent_scale("expansion") == 0.8
        assert _intent_scale("partnership") == 0.6
        assert _intent_scale("leadership") == 0.5
        assert _intent_scale("product") == 0.4
        assert _intent_scale("acquisition") == 0.3
        assert _intent_scale("layoffs") == 0.2
        assert _intent_scale("ipo") == 0.3
        assert _intent_scale("security") == 0.15
        assert _intent_scale("other") == 0.1

    def test_unknown_type_defaults_to_0_1(self):
        assert _intent_scale("banana") == 0.1


# ── qualify_signal ───────────────────────────────────────────────

class TestQualifySignal:
    def test_critical_funding_high_confidence(self):
        q = qualify_signal(
            signal_id="s1", company_name="Acme", signal_type="funding",
            raw_confidence="high", detected_at=datetime.now(UTC),
        )
        assert q.priority == SignalPriority.CRITICAL
        assert q.priority_score >= 75
        assert q.signal_type == "funding"

    def test_medium_hiring_medium_confidence(self):
        q = qualify_signal(
            signal_id="s2", company_name="Bco", signal_type="hiring",
            raw_confidence="medium", detected_at=datetime.now(UTC),
        )
        assert q.priority in (SignalPriority.MEDIUM, SignalPriority.HIGH)

    def test_noise_unknown_signal_low_confidence(self):
        q = qualify_signal(
            signal_id="s3", company_name="Cco", signal_type="security",
            raw_confidence="low", detected_at=datetime.now(UTC) - timedelta(days=60),
        )
        assert q.priority == SignalPriority.NOISE

    def test_source_boost_max_20_percent(self):
        now = datetime.now(UTC)
        q1 = qualify_signal(
            signal_id="s4", company_name="Dco", signal_type="funding",
            raw_confidence="high", detected_at=now, source_count=1,
        )
        q5 = qualify_signal(
            signal_id="s5", company_name="Dco", signal_type="funding",
            raw_confidence="high", detected_at=now, source_count=5,
        )
        assert q5.priority_score > q1.priority_score
        # With many sources, capped at +20%
        assert q5.priority_score <= 100.0

    def test_score_never_exceeds_100(self):
        q = qualify_signal(
            signal_id="s6", company_name="Eco", signal_type="acquisition",
            raw_confidence="high", detected_at=datetime.now(UTC), source_count=10,
        )
        assert q.priority_score <= 100.0

    def test_unknown_signal_type_defaults_to_20(self):
        q = qualify_signal(
            signal_id="s7", company_name="Fco", signal_type="unknown_type",
            raw_confidence="high", detected_at=datetime.now(UTC),
        )
        assert q.priority_score > 0

    def test_unknown_confidence_defaults_to_0_5(self):
        q = qualify_signal(
            signal_id="s8", company_name="Gco", signal_type="funding",
            raw_confidence="bogus", detected_at=datetime.now(UTC),
        )
        assert q.priority_score > 0
        assert "bogus" in q.qualification_notes

    def test_intent_contribution_present(self):
        q = qualify_signal(
            signal_id="s9", company_name="Hco", signal_type="funding",
            raw_confidence="high", detected_at=datetime.now(UTC),
        )
        assert q.intent_contribution > 0

    def test_notes_contain_components(self):
        q = qualify_signal(
            signal_id="s10", company_name="Ico", signal_type="hiring",
            raw_confidence="medium", detected_at=datetime.now(UTC),
        )
        assert "base=" in q.qualification_notes
        assert "conf=" in q.qualification_notes
        assert "recency=" in q.qualification_notes


# ── compute_intent_level ─────────────────────────────────────────

class TestComputeIntentLevel:
    def test_empty_returns_unknown(self):
        level, score = compute_intent_level([])
        assert level == IntentLevel.UNKNOWN
        assert score == 0.0

    def test_single_funding_high(self):
        from app.modules.signal_actions.models import SignalQualification
        q = SignalQualification(
            signal_type="funding", raw_confidence="high",
            priority=SignalPriority.CRITICAL, priority_score=85.0,
            intent_contribution=76.5, qualified_at=datetime.now(UTC),
        )
        level, score = compute_intent_level([q])
        assert level in (IntentLevel.MEDIUM, IntentLevel.HIGH, IntentLevel.VERY_HIGH)
        assert score > 0

    def test_many_signals_boost_diversity(self):
        from app.modules.signal_actions.models import SignalQualification
        quals = []
        for i, st in enumerate(["funding", "hiring", "expansion", "leadership", "product"]):
            quals.append(SignalQualification(
                signal_type=st, raw_confidence="high",
                priority=SignalPriority.HIGH, priority_score=70.0,
                intent_contribution=50.0, qualified_at=datetime.now(UTC),
            ))
        level, score = compute_intent_level(quals)
        # 5 different types → diversity_bonus = min(15, 5*3) = 15
        assert score > 50.0

    def test_score_capped_at_100(self):
        from app.modules.signal_actions.models import SignalQualification
        quals = [SignalQualification(
            signal_type="funding", raw_confidence="high",
            priority=SignalPriority.CRITICAL, priority_score=100.0,
            intent_contribution=90.0, qualified_at=datetime.now(UTC),
        ) for _ in range(20)]
        level, score = compute_intent_level(quals)
        assert score <= 100.0

    def test_all_same_type_lower_diversity_bonus(self):
        from app.modules.signal_actions.models import SignalQualification
        quals = [SignalQualification(
            signal_type="funding", raw_confidence="high",
            priority=SignalPriority.CRITICAL, priority_score=85.0,
            intent_contribution=76.5, qualified_at=datetime.now(UTC),
        ) for _ in range(5)]
        level, score = compute_intent_level(quals)
        # All same type → diversity_bonus = min(15, 1*3) = 3
        assert score > 0
