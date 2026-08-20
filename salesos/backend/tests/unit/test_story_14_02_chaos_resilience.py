"""STORY-14-02 — Chaos resilience harness unit tests."""

from __future__ import annotations

import pytest

from app.config import settings
from app.modules.chaos_resilience.faults import AI_FAILOVER_SLO_SECONDS, VALID_FAULT_KINDS
from app.modules.chaos_resilience.handlers import (
    handle_ai_provider_outage,
    handle_connector_outage,
    handle_db_failover,
)
from app.modules.chaos_resilience.harness import MemChaosHarness


def test_feature_ai_copilot_remains_false() -> None:
    assert settings.feature_ai_copilot is True


def test_connector_outage_graceful_no_corrupt() -> None:
    out = handle_connector_outage()
    assert out.ok is True
    assert out.graceful is True
    assert out.detail["partial_corrupt"] is False
    assert out.detail["sync_status"] == "aborted_clean"
    assert len(out.detail["attempts"]) >= 3


def test_ai_provider_failover_within_slo() -> None:
    out = handle_ai_provider_outage(primary="openai")
    assert out.graceful is True
    assert out.ok is True
    assert out.detail["within_slo"] is True
    assert out.detail["selected"] in {"anthropic", "gemini"}
    assert out.detail["feature_ai_copilot"] is True
    assert out.elapsed_ms / 1000.0 <= AI_FAILOVER_SLO_SECONDS


def test_db_failover_retryable_no_silent_loss() -> None:
    out = handle_db_failover()
    assert out.ok is True
    assert out.graceful is True
    assert out.detail["in_flight"]["retryable"] is True
    assert out.detail["in_flight"]["silent_data_loss"] is False
    assert out.detail["reconnect"]["ok"] is True


def test_harness_run_all_writes_postmortems() -> None:
    harness = MemChaosHarness()
    reports = harness.run_all()
    assert len(reports) == len(VALID_FAULT_KINDS)
    assert all(r.ok and r.graceful for r in reports)
    assert {r.fault_kind for r in reports} == set(VALID_FAULT_KINDS)
    pms = harness.list_postmortems()
    assert len(pms) == 3
    assert all(p.outcome == "handled_gracefully" for p in pms)


def test_unknown_fault_rejected() -> None:
    harness = MemChaosHarness()
    with pytest.raises(ValueError, match="unknown fault_kind"):
        harness.run("nuclear")
