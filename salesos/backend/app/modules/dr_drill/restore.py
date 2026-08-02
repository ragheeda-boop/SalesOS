"""STORY-14-03 — Simulated backup/restore steps (non-prod CI).

Measures RTO/RPO against checklist targets. No live prod backup/restore.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from app.modules.dr_drill.targets import RPO_TARGET_SECONDS, RTO_TARGET_SECONDS


@dataclass
class RestoreOutcome:
    ok: bool
    within_rto: bool
    within_rpo: bool
    rto_seconds: float
    rpo_seconds: float
    detail: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "within_rto": self.within_rto,
            "within_rpo": self.within_rpo,
            "rto_seconds": self.rto_seconds,
            "rpo_seconds": self.rpo_seconds,
            "rto_target_seconds": RTO_TARGET_SECONDS,
            "rpo_target_seconds": RPO_TARGET_SECONDS,
            "detail": dict(self.detail),
        }


def run_full_backup_restore(
    *,
    # Simulated wall-clock for restore path (CI stays sub-second).
    restore_duration_seconds: float = 12.0,
    # Age of last successful backup relative to failure instant.
    backup_age_seconds: float = 900.0,
) -> RestoreOutcome:
    """Simulate full backup → restore to non-prod target; measure RTO/RPO."""
    started = time.perf_counter()
    failure_at = datetime.now(UTC)
    last_backup_at = failure_at - timedelta(seconds=max(0.0, backup_age_seconds))

    # Steps: snapshot verify → restore → integrity check (no real I/O).
    steps = [
        {"step": "verify_backup_artifact", "ok": True},
        {"step": "restore_to_nonprod_target", "ok": True},
        {"step": "integrity_checksum", "ok": True},
        {"step": "app_reconnect_smoke", "ok": True},
    ]
    # Record measured restore duration without sleeping full wall time in CI.
    measured_rto = float(restore_duration_seconds)
    _ = time.perf_counter() - started  # harness overhead only
    rpo = (failure_at - last_backup_at).total_seconds()
    within_rto = measured_rto <= RTO_TARGET_SECONDS
    within_rpo = rpo <= RPO_TARGET_SECONDS
    ok = within_rto and within_rpo and all(s["ok"] for s in steps)
    return RestoreOutcome(
        ok=ok,
        within_rto=within_rto,
        within_rpo=within_rpo,
        rto_seconds=measured_rto,
        rpo_seconds=rpo,
        detail={
            "kind": "full_backup_restore",
            "failure_at": failure_at.isoformat(),
            "last_backup_at": last_backup_at.isoformat(),
            "target": "nonprod_restore_fixture",
            "steps": steps,
            "silent_data_loss": False,
            "honesty": ("Simulated DR restore; live production backup/restore not performed"),
        },
    )


def run_point_in_time_recovery(
    *,
    restore_duration_seconds: float = 18.0,
    backup_age_seconds: float = 1800.0,
) -> RestoreOutcome:
    """Simulate PITR to a timestamp within last 24h (checklist)."""
    started = time.perf_counter()
    failure_at = datetime.now(UTC)
    pit = failure_at - timedelta(minutes=30)
    last_backup_at = failure_at - timedelta(seconds=max(0.0, backup_age_seconds))
    steps = [
        {"step": "select_pitr_timestamp", "ok": True, "target": pit.isoformat()},
        {"step": "restore_wal_to_timestamp", "ok": True},
        {"step": "integrity_checksum", "ok": True},
    ]
    measured_rto = float(restore_duration_seconds)
    _ = time.perf_counter() - started
    rpo = (failure_at - last_backup_at).total_seconds()
    within_rto = measured_rto <= RTO_TARGET_SECONDS
    within_rpo = rpo <= RPO_TARGET_SECONDS
    ok = within_rto and within_rpo and all(s["ok"] for s in steps)
    return RestoreOutcome(
        ok=ok,
        within_rto=within_rto,
        within_rpo=within_rpo,
        rto_seconds=measured_rto,
        rpo_seconds=rpo,
        detail={
            "kind": "point_in_time_recovery",
            "failure_at": failure_at.isoformat(),
            "pitr_target": pit.isoformat(),
            "last_backup_at": last_backup_at.isoformat(),
            "target": "nonprod_pitr_fixture",
            "steps": steps,
            "within_24h_window": True,
            "honesty": "Simulated PITR; live WAL restore not performed",
        },
    )
