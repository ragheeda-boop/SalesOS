"""STORY-14-03 — DR drill harness (backup/restore, RTO/RPO measured).

CI/non-prod only. Not Production GO. DEC-085 untouched. No FORCE RLS.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.modules.dr_drill.postmortem import (
    PracticePostmortem,
    write_dr_postmortem,
)
from app.modules.dr_drill.restore import (
    RestoreOutcome,
    run_full_backup_restore,
    run_point_in_time_recovery,
)
from app.modules.dr_drill.targets import DRILL_KINDS


@dataclass
class DrDrillReport:
    id: str
    drill_kind: str
    ok: bool
    within_rto: bool
    within_rpo: bool
    rto_seconds: float
    rpo_seconds: float
    restore: dict[str, Any] = field(default_factory=dict)
    postmortem: dict[str, Any] = field(default_factory=dict)
    ran_at: str = ""
    honesty: str = (
        "CI/non-prod DR harness only; live production backup/restore not performed. "
        "Not Production GO. feature_ai_copilot=False."
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "drill_kind": self.drill_kind,
            "ok": self.ok,
            "within_rto": self.within_rto,
            "within_rpo": self.within_rpo,
            "rto_seconds": self.rto_seconds,
            "rpo_seconds": self.rpo_seconds,
            "restore": dict(self.restore),
            "postmortem": dict(self.postmortem),
            "ran_at": self.ran_at,
            "honesty": self.honesty,
        }


@dataclass
class MemDrDrillHarness:
    _drills: dict[str, DrDrillReport] = field(default_factory=dict)
    _postmortems: dict[str, PracticePostmortem] = field(default_factory=dict)

    def run(self, drill_kind: str) -> DrDrillReport:
        kind = (drill_kind or "").strip().lower()
        if kind not in DRILL_KINDS:
            raise ValueError(
                f"unknown drill_kind={drill_kind!r}; expected one of {sorted(DRILL_KINDS)}"
            )
        outcome = self._dispatch(kind)
        drill_id = uuid.uuid4().hex[:12]
        pm = write_dr_postmortem(
            drill_id=drill_id,
            drill_kind=kind,
            ok=outcome.ok,
            rto_seconds=outcome.rto_seconds,
            rpo_seconds=outcome.rpo_seconds,
            within_rto=outcome.within_rto,
            within_rpo=outcome.within_rpo,
            detail=outcome.detail,
        )
        report = DrDrillReport(
            id=drill_id,
            drill_kind=kind,
            ok=outcome.ok,
            within_rto=outcome.within_rto,
            within_rpo=outcome.within_rpo,
            rto_seconds=outcome.rto_seconds,
            rpo_seconds=outcome.rpo_seconds,
            restore=outcome.as_dict(),
            postmortem=pm.as_dict(),
            ran_at=datetime.now(UTC).isoformat(),
        )
        self._drills[drill_id] = report
        self._postmortems[drill_id] = pm
        return report

    def _dispatch(self, kind: str) -> RestoreOutcome:
        if kind == "full_backup_restore":
            return run_full_backup_restore()
        if kind == "point_in_time_recovery":
            return run_point_in_time_recovery()
        raise ValueError(f"unhandled drill_kind={kind}")

    def list_drills(self) -> list[DrDrillReport]:
        return sorted(self._drills.values(), key=lambda d: d.ran_at)

    def get_drill(self, drill_id: str) -> DrDrillReport | None:
        return self._drills.get(str(drill_id))

    def list_postmortems(self) -> list[PracticePostmortem]:
        return sorted(self._postmortems.values(), key=lambda p: p.written_at)

    def run_all(self) -> list[DrDrillReport]:
        return [self.run(k) for k in sorted(DRILL_KINDS)]


DEFAULT_DR_HARNESS = MemDrDrillHarness()
