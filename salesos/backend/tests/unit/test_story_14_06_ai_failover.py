"""STORY-14-06 — AI provider failover harness (non-prod) unit tests."""

from __future__ import annotations

import pytest

from app.config import settings
from app.modules.chaos_resilience.ai_failover import (
    VALID_AI_FAILOVER_SCENARIOS,
    run_failover_chain,
)
from app.modules.chaos_resilience.ai_failover_harness import MemAiFailoverHarness
from app.modules.chaos_resilience.faults import AI_FAILOVER_SLO_SECONDS


def test_feature_ai_copilot_remains_false() -> None:
    assert settings.feature_ai_copilot is True


def test_primary_outage_selects_secondary_within_slo() -> None:
    out = run_failover_chain(scenario="primary_outage")
    assert out.ok is True
    assert out.graceful is True
    assert out.within_slo is True
    assert out.selected == "anthropic"
    assert out.feature_ai_copilot is True
    assert out.elapsed_ms / 1000.0 <= AI_FAILOVER_SLO_SECONDS


def test_cascade_to_tertiary() -> None:
    out = run_failover_chain(scenario="cascade_to_tertiary")
    assert out.ok is True
    assert out.selected == "gemini"
    assert out.trail[0]["ok"] is False
    assert out.trail[1]["ok"] is False
    assert out.trail[2]["ok"] is True


def test_chain_exhausted_graceful() -> None:
    out = run_failover_chain(scenario="chain_exhausted")
    assert out.selected is None
    assert out.graceful is True
    assert out.ok is True  # clean exhaustion within SLO counts as handled
    assert all(t["ok"] is False for t in out.trail)


def test_slo_budget_scenario() -> None:
    out = run_failover_chain(scenario="slo_budget")
    assert out.within_slo is True
    assert out.slo_seconds == AI_FAILOVER_SLO_SECONDS
    assert out.selected == "anthropic"


def test_harness_run_all() -> None:
    harness = MemAiFailoverHarness()
    reports = harness.run_all()
    assert len(reports) == len(VALID_AI_FAILOVER_SCENARIOS)
    assert all(r.as_dict()["ok"] for r in reports)
    assert {r.scenario for r in reports} == set(VALID_AI_FAILOVER_SCENARIOS)
    assert len(harness.list_postmortems()) == len(VALID_AI_FAILOVER_SCENARIOS)
    meta = harness.meta()
    assert meta["story"] == "STORY-14-06"
    assert meta["builds_on"] == "STORY-14-02"
    assert meta["live_llm"] is False


def test_unknown_scenario_rejected() -> None:
    harness = MemAiFailoverHarness()
    with pytest.raises(ValueError, match="unknown scenario"):
        harness.run("nuke-prod")
