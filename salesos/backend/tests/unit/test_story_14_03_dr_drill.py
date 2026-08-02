"""STORY-14-03 — DR drill harness unit tests."""

from __future__ import annotations

import pytest

from app.config import settings
from app.modules.dr_drill.harness import MemDrDrillHarness
from app.modules.dr_drill.restore import run_full_backup_restore, run_point_in_time_recovery
from app.modules.dr_drill.targets import (
    DRILL_KINDS,
    RPO_TARGET_SECONDS,
    RTO_TARGET_SECONDS,
)


def test_feature_ai_copilot_remains_false() -> None:
    assert settings.feature_ai_copilot is False


def test_slo_targets_match_checklist() -> None:
    assert RTO_TARGET_SECONDS == 4 * 60 * 60
    assert RPO_TARGET_SECONDS == 60 * 60


def test_full_backup_restore_within_slo() -> None:
    out = run_full_backup_restore(
        restore_duration_seconds=12.0,
        backup_age_seconds=900.0,
    )
    assert out.ok is True
    assert out.within_rto is True
    assert out.within_rpo is True
    assert out.rto_seconds <= RTO_TARGET_SECONDS
    assert out.rpo_seconds <= RPO_TARGET_SECONDS
    assert out.detail["silent_data_loss"] is False
    assert out.detail["target"] == "nonprod_restore_fixture"


def test_pitr_within_slo() -> None:
    out = run_point_in_time_recovery(
        restore_duration_seconds=18.0,
        backup_age_seconds=1800.0,
    )
    assert out.ok is True
    assert out.within_rto is True
    assert out.within_rpo is True
    assert out.detail["within_24h_window"] is True


def test_rpo_miss_detected() -> None:
    out = run_full_backup_restore(
        restore_duration_seconds=10.0,
        backup_age_seconds=RPO_TARGET_SECONDS + 60,
    )
    assert out.within_rpo is False
    assert out.ok is False


def test_rto_miss_detected() -> None:
    out = run_full_backup_restore(
        restore_duration_seconds=RTO_TARGET_SECONDS + 1,
        backup_age_seconds=60,
    )
    assert out.within_rto is False
    assert out.ok is False


def test_harness_run_all_writes_postmortems() -> None:
    harness = MemDrDrillHarness()
    reports = harness.run_all()
    assert len(reports) == len(DRILL_KINDS)
    assert all(r.ok for r in reports)
    assert {r.drill_kind for r in reports} == set(DRILL_KINDS)
    pms = harness.list_postmortems()
    assert len(pms) == 2
    assert all(p.outcome == "within_slo" for p in pms)
    assert all(p.within_rto and p.within_rpo for p in pms)


def test_unknown_drill_rejected() -> None:
    harness = MemDrDrillHarness()
    with pytest.raises(ValueError, match="unknown drill_kind"):
        harness.run("prod_kill")
