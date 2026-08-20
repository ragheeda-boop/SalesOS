"""STORY-14-07 — LLM regression suite (non-prod) unit tests."""

from __future__ import annotations

import pytest

from app.config import settings
from app.modules.chaos_resilience.llm_regression import (
    GOLDEN_CASES,
    SIMILARITY_THRESHOLD,
    VALID_LLM_REGRESSION_MODES,
    fixture_model_output,
    run_llm_regression,
    token_jaccard,
)
from app.modules.chaos_resilience.llm_regression_harness import MemLlmRegressionHarness


def test_feature_ai_copilot_remains_false() -> None:
    assert settings.feature_ai_copilot is True


def test_token_jaccard_identical() -> None:
    assert token_jaccard("hello world", "hello world") == 1.0


def test_token_jaccard_disjoint() -> None:
    assert token_jaccard("alpha beta", "gamma delta") == 0.0


def test_baseline_establishes_golden_pass() -> None:
    out = run_llm_regression(mode="baseline")
    assert out.ok is True
    assert out.baseline_established is True
    assert out.regression_detected is False
    assert out.cases_passed == out.cases_total == len(GOLDEN_CASES)
    assert out.feature_ai_copilot is True
    assert out.live_llm is False
    assert all(c.passed for c in out.case_results)
    assert all(c.similarity >= SIMILARITY_THRESHOLD for c in out.case_results)


def test_injected_regression_is_detected() -> None:
    out = run_llm_regression(mode="injected_regression")
    assert out.ok is True  # detection succeeded
    assert out.regression_detected is True
    assert out.baseline_established is False
    assert out.cases_passed < out.cases_total
    assert all(not c.passed for c in out.case_results)


def test_degraded_fixture_differs_from_reference() -> None:
    case = GOLDEN_CASES[0]
    good = fixture_model_output(case, "good")
    bad = fixture_model_output(case, "degraded")
    assert good == case.reference
    assert token_jaccard(bad, case.reference) < SIMILARITY_THRESHOLD


def test_promote_gate_blocks_on_regression() -> None:
    out = run_llm_regression(mode="promote_gate")
    assert out.ok is True
    assert out.regression_detected is True
    assert out.promotion_blocked is True


def test_harness_run_all() -> None:
    harness = MemLlmRegressionHarness()
    reports = harness.run_all()
    assert len(reports) == len(VALID_LLM_REGRESSION_MODES)
    assert all(r.as_dict()["ok"] for r in reports)
    assert {r.mode for r in reports} == set(VALID_LLM_REGRESSION_MODES)
    baseline = next(r for r in reports if r.mode == "baseline")
    injected = next(r for r in reports if r.mode == "injected_regression")
    assert baseline.as_dict()["baseline_established"] is True
    assert injected.as_dict()["regression_detected"] is True
    meta = harness.meta()
    assert meta["story"] == "STORY-14-07"
    assert meta["live_llm"] is False
    assert meta["feature_ai_copilot"] is True
    assert meta["golden_cases"] == len(GOLDEN_CASES)


def test_unknown_mode_rejected() -> None:
    harness = MemLlmRegressionHarness()
    with pytest.raises(ValueError, match="unknown mode"):
        harness.run("nuke-prod-llm")
