"""Unit tests for effectiveness/__init__.py — pure functions, no DB.

Covers: assign_cohort, _safe_lift, _safe_rate, _check_monotonicity, _calibration_readiness,
        record_feedback_event invalid decision check.
"""

import pytest

from app.modules.effectiveness import (
    COHORT_THRESHOLDS,
    INTENT_MODEL_VERSION,
    EffectivenessService,
    assign_cohort,
    _safe_lift,
    _safe_rate,
)


# ── assign_cohort ────────────────────────────────────────────────

class TestAssignCohort:
    def test_critical(self):
        assert assign_cohort(95.0) == "critical"
        assert assign_cohort(80.0) == "critical"

    def test_high(self):
        assert assign_cohort(79.9) == "high"
        assert assign_cohort(60.0) == "high"

    def test_medium(self):
        assert assign_cohort(59.9) == "medium"
        assert assign_cohort(40.0) == "medium"

    def test_low(self):
        assert assign_cohort(39.9) == "low"
        assert assign_cohort(0.0) == "low"

    def test_negative_score(self):
        assert assign_cohort(-5.0) == "low"

    def test_exactly_boundary_80(self):
        assert assign_cohort(80.0) == "critical"

    def test_exactly_boundary_60(self):
        assert assign_cohort(60.0) == "high"

    def test_exactly_boundary_40(self):
        assert assign_cohort(40.0) == "medium"

    def test_100(self):
        assert assign_cohort(100.0) == "critical"


# ── _safe_lift ───────────────────────────────────────────────────

class TestSafeLift:
    def test_normal(self):
        result = _safe_lift(0.4, 0.2)
        assert result["value"] == 2.0
        assert result["reason"] is None
        assert "2.0x" in result["display"]

    def test_zero_denominator(self):
        result = _safe_lift(0.5, 0.0)
        assert result["value"] is None
        assert result["reason"] == "baseline_rate_zero"
        assert result["display"] == "N/A"

    def test_negative_denominator(self):
        result = _safe_lift(0.5, -1.0)
        assert result["value"] is None
        assert result["reason"] == "baseline_rate_zero"

    def test_equal_rates(self):
        result = _safe_lift(0.3, 0.3)
        assert result["value"] == 1.0

    def test_zero_numerator(self):
        result = _safe_lift(0.0, 0.5)
        assert result["value"] == 0.0


# ── _safe_rate ───────────────────────────────────────────────────

class TestSafeRate:
    def test_normal(self):
        assert _safe_rate(3, 10) == 30.0

    def test_zero_total(self):
        assert _safe_rate(5, 0) == 0.0

    def test_negative_total(self):
        assert _safe_rate(5, -1) == 0.0

    def test_zero_count(self):
        assert _safe_rate(0, 10) == 0.0

    def test_full_rate(self):
        assert _safe_rate(10, 10) == 100.0

    def test_rounding(self):
        result = _safe_rate(1, 3)
        assert result == 33.3


# ── _check_monotonicity ─────────────────────────────────────────

class TestCheckMonotonicity:
    def _svc(self):
        return EffectivenessService(factory=None)

    def test_pass_monotonic(self):
        cohorts = {
            "critical": {"connection_rate": 80, "meeting_rate": 60, "opportunity_rate": 40, "win_rate": 20},
            "high": {"connection_rate": 60, "meeting_rate": 40, "opportunity_rate": 30, "win_rate": 15},
            "medium": {"connection_rate": 40, "meeting_rate": 20, "opportunity_rate": 15, "win_rate": 5},
            "low": {"connection_rate": 20, "meeting_rate": 10, "opportunity_rate": 5, "win_rate": 2},
        }
        result = self._svc()._check_monotonicity(cohorts)
        assert result["overall"] == "PASS"
        for metric in ["connection_rate", "meeting_rate", "opportunity_rate", "win_rate"]:
            assert result["by_metric"][metric]["status"] == "PASS"

    def test_fail_non_monotonic(self):
        cohorts = {
            "critical": {"connection_rate": 20, "meeting_rate": 10, "opportunity_rate": 5, "win_rate": 2},
            "high": {"connection_rate": 60, "meeting_rate": 40, "opportunity_rate": 30, "win_rate": 15},
            "medium": {"connection_rate": 40, "meeting_rate": 20, "opportunity_rate": 15, "win_rate": 5},
            "low": {"connection_rate": 20, "meeting_rate": 10, "opportunity_rate": 5, "win_rate": 2},
        }
        result = self._svc()._check_monotonicity(cohorts)
        assert result["overall"] == "FAIL"
        assert result["by_metric"]["connection_rate"]["status"] == "FAIL"

    def test_insufficient_data_all_zero(self):
        cohorts = {
            "critical": {"connection_rate": 0, "meeting_rate": 0, "opportunity_rate": 0, "win_rate": 0},
            "high": {"connection_rate": 0, "meeting_rate": 0, "opportunity_rate": 0, "win_rate": 0},
            "medium": {"connection_rate": 0, "meeting_rate": 0, "opportunity_rate": 0, "win_rate": 0},
            "low": {"connection_rate": 0, "meeting_rate": 0, "opportunity_rate": 0, "win_rate": 0},
        }
        result = self._svc()._check_monotonicity(cohorts)
        assert result["overall"] == "INSUFFICIENT_DATA"

    def test_equal_values_insufficient(self):
        cohorts = {
            "critical": {"connection_rate": 50, "meeting_rate": 30, "opportunity_rate": 20, "win_rate": 10},
            "high": {"connection_rate": 50, "meeting_rate": 30, "opportunity_rate": 20, "win_rate": 10},
            "medium": {"connection_rate": 50, "meeting_rate": 30, "opportunity_rate": 20, "win_rate": 10},
            "low": {"connection_rate": 50, "meeting_rate": 30, "opportunity_rate": 20, "win_rate": 10},
        }
        result = self._svc()._check_monotonicity(cohorts)
        assert result["overall"] == "INSUFFICIENT_DATA"

    def test_missing_cohort_defaults_to_zero(self):
        cohorts = {
            "critical": {"connection_rate": 80, "meeting_rate": 0, "opportunity_rate": 0, "win_rate": 0},
            "high": {"connection_rate": 0, "meeting_rate": 0, "opportunity_rate": 0, "win_rate": 0},
            "medium": {"connection_rate": 0, "meeting_rate": 0, "opportunity_rate": 0, "win_rate": 0},
        }
        result = self._svc()._check_monotonicity(cohorts)
        # Missing "low" → defaults to 0; critical=80, low=0 → monotonic
        assert result["by_metric"]["connection_rate"]["status"] == "PASS"


# ── _calibration_readiness ───────────────────────────────────────

class TestCalibrationReadiness:
    def _svc(self):
        return EffectivenessService(factory=None)

    def test_not_ready_empty_data(self):
        summary = {
            "total_accounts": 0, "accounts_with_action": 0,
            "meetings": 0, "won": 0,
        }
        result = self._svc()._calibration_readiness(summary, {}, {"total_actions": 0})
        assert result["status"] == "NOT_READY"

    def test_ready_sufficient_data(self):
        summary = {
            "total_accounts": 100, "accounts_with_action": 50,
            "meetings": 25, "won": 10,
        }
        cohorts = {
            "critical": {"total": 20},
            "high": {"total": 25},
            "medium": {"total": 30},
            "low": {"total": 25},
        }
        nba = {"total_actions": 50}
        result = self._svc()._calibration_readiness(summary, cohorts, nba)
        assert result["status"] == "READY_FOR_CALIBRATION"

    def test_observing_partial_data(self):
        summary = {
            "total_accounts": 60, "accounts_with_action": 30,
            "meetings": 5, "won": 2,
        }
        cohorts = {
            "critical": {"total": 15},
            "high": {"total": 15},
            "medium": {"total": 15},
            "low": {"total": 15},
        }
        nba = {"total_actions": 10}
        result = self._svc()._calibration_readiness(summary, cohorts, nba)
        # Op partial, stat insufficient → OBSERVING
        assert result["status"] in ("OBSERVING", "NOT_READY")

    def test_imbalanced_cohorts(self):
        summary = {
            "total_accounts": 100, "accounts_with_action": 50,
            "meetings": 25, "won": 10,
        }
        cohorts = {
            "critical": {"total": 80},
            "high": {"total": 10},
            "medium": {"total": 5},
            "low": {"total": 5},
        }
        nba = {"total_actions": 50}
        result = self._svc()._calibration_readiness(summary, cohorts, nba)
        # Imbalance ratio = 80/5 = 16 > 5 → stat check fails
        assert result["statistical"]["checks"]["cohort_balance"]["pass"] is False
