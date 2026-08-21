"""Tests for chaos_resilience.postmortem — factory + serialization, no DB."""

from __future__ import annotations

import pytest

from app.modules.chaos_resilience.postmortem import (
    PracticePostmortem,
    write_practice_postmortem,
)


# ── write_practice_postmortem ────────────────────────────────────────────────


class TestGracefulHandling:
    def test_connector_outage(self):
        pm = write_practice_postmortem(
            drill_id="DR-001",
            fault_kind="connector_outage",
            graceful=True,
            detail={},
        )
        assert pm.outcome == "handled_gracefully"
        assert pm.drill_id == "DR-001"
        assert "abort" in pm.summary.lower() or "cleanly" in pm.summary.lower()
        assert len(pm.what_went_well) == 3
        assert len(pm.what_to_improve) == 0

    def test_ai_provider_outage(self):
        pm = write_practice_postmortem(
            drill_id="DR-002",
            fault_kind="ai_provider_outage",
            graceful=True,
            detail={},
        )
        assert pm.outcome == "handled_gracefully"
        assert "failover" in pm.summary.lower()
        assert len(pm.what_to_improve) == 1
        assert "STORY-14-06" in pm.what_to_improve[0]

    def test_db_failover(self):
        pm = write_practice_postmortem(
            drill_id="DR-003",
            fault_kind="db_failover",
            graceful=True,
            detail={},
        )
        assert pm.outcome == "handled_gracefully"
        assert "reconnect" in pm.summary.lower()


class TestUngracefulHandling:
    def test_connector_outage(self):
        pm = write_practice_postmortem(
            drill_id="DR-010",
            fault_kind="connector_outage",
            graceful=False,
            detail={},
        )
        assert pm.outcome == "needs_remediation"
        assert len(pm.what_to_improve) == 1
        assert "Sprint 25" in pm.what_to_improve[0]
        assert len(pm.what_went_well) == 1

    def test_ai_provider_outage(self):
        pm = write_practice_postmortem(
            drill_id="DR-011",
            fault_kind="ai_provider_outage",
            graceful=False,
            detail={},
        )
        assert pm.outcome == "needs_remediation"
        assert len(pm.what_to_improve) == 2

    def test_unknown_fault_kind(self):
        pm = write_practice_postmortem(
            drill_id="DR-012",
            fault_kind="unknown_thing",
            graceful=False,
            detail={},
        )
        assert pm.outcome == "needs_remediation"
        assert "Chaos drill completed." in pm.summary


# ── PracticePostmortem.as_dict ──────────────────────────────────────────────


class TestAsDict:
    def test_as_dict(self):
        pm = write_practice_postmortem(
            drill_id="DR-020",
            fault_kind="db_failover",
            graceful=True,
            detail={},
        )
        d = pm.as_dict()
        assert d["drill_id"] == "DR-020"
        assert d["fault_kind"] == "db_failover"
        assert d["outcome"] == "handled_gracefully"
        assert isinstance(d["what_went_well"], list)
        assert isinstance(d["what_to_improve"], list)
        assert isinstance(d["residuals"], list)
        assert d["written_at"]  # non-empty timestamp
        assert "Practice postmortem" in d["honesty"]


# ── Honesty string ───────────────────────────────────────────────────────────


class TestHonesty:
    def test_not_production_go(self):
        pm = write_practice_postmortem(
            drill_id="DR-030",
            fault_kind="connector_outage",
            graceful=True,
            detail={},
        )
        assert "Not Production GO" in pm.honesty
