"""STORY-14-03 — Practice postmortems for DR drills."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class PracticePostmortem:
    drill_id: str
    drill_kind: str
    outcome: str
    summary: str
    rto_seconds: float = 0.0
    rpo_seconds: float = 0.0
    within_rto: bool = False
    within_rpo: bool = False
    what_went_well: list[str] = field(default_factory=list)
    what_to_improve: list[str] = field(default_factory=list)
    residuals: list[str] = field(default_factory=list)
    written_at: str = ""
    honesty: str = (
        "Practice postmortem (DR drill), not a production incident. " "Not Production GO."
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "drill_id": self.drill_id,
            "drill_kind": self.drill_kind,
            "outcome": self.outcome,
            "summary": self.summary,
            "rto_seconds": self.rto_seconds,
            "rpo_seconds": self.rpo_seconds,
            "within_rto": self.within_rto,
            "within_rpo": self.within_rpo,
            "what_went_well": list(self.what_went_well),
            "what_to_improve": list(self.what_to_improve),
            "residuals": list(self.residuals),
            "written_at": self.written_at,
            "honesty": self.honesty,
        }


def write_dr_postmortem(
    *,
    drill_id: str,
    drill_kind: str,
    ok: bool,
    rto_seconds: float,
    rpo_seconds: float,
    within_rto: bool,
    within_rpo: bool,
    detail: dict[str, Any],
) -> PracticePostmortem:
    _ = detail
    outcome = "within_slo" if ok else "needs_remediation"
    summary = (
        f"DR {drill_kind}: RTO={rto_seconds:.1f}s (≤4h={within_rto}), "
        f"RPO={rpo_seconds:.1f}s (≤1h={within_rpo})."
    )
    improve: list[str] = []
    if not within_rto:
        improve.append("RTO exceeded 4h target — track remediation before Sprint 25 gate.")
    if not within_rpo:
        improve.append("RPO exceeded 1h target — tighten backup cadence.")
    improve.append("Field Ops: schedule non-prod restore against real backup artifact.")
    return PracticePostmortem(
        drill_id=drill_id,
        drill_kind=drill_kind,
        outcome=outcome,
        summary=summary,
        rto_seconds=rto_seconds,
        rpo_seconds=rpo_seconds,
        within_rto=within_rto,
        within_rpo=within_rpo,
        what_went_well=(
            [
                "Restore path exercised on non-prod fixture",
                "RTO/RPO measured and recorded",
                "Auth-gated drill HTTP",
            ]
            if ok
            else ["Harness recorded SLO miss without claiming GO"]
        ),
        what_to_improve=improve,
        residuals=[
            "Live staging/prod backup restore — Ops/DevOps field",
            "Stage 6 GHCR remains quarantined",
            "No Production GO",
        ],
        written_at=datetime.now(UTC).isoformat(),
    )
