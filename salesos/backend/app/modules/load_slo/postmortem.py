"""STORY-14-01 — Practice postmortems for load/SLO runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class PracticePostmortem:
    run_id: str
    profile: str
    outcome: str
    summary: str
    tenants: int = 0
    p95_latency_ms: float = 0.0
    error_rate: float = 0.0
    within_slo: bool = False
    what_went_well: list[str] = field(default_factory=list)
    what_to_improve: list[str] = field(default_factory=list)
    residuals: list[str] = field(default_factory=list)
    written_at: str = ""
    honesty: str = (
        "Practice postmortem (load/SLO harness), not a production incident. "
        "Not Production GO."
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "profile": self.profile,
            "outcome": self.outcome,
            "summary": self.summary,
            "tenants": self.tenants,
            "p95_latency_ms": self.p95_latency_ms,
            "error_rate": self.error_rate,
            "within_slo": self.within_slo,
            "what_went_well": list(self.what_went_well),
            "what_to_improve": list(self.what_to_improve),
            "residuals": list(self.residuals),
            "written_at": self.written_at,
            "honesty": self.honesty,
        }


def write_load_postmortem(
    *,
    run_id: str,
    profile: str,
    ok: bool,
    tenants: int,
    p95_latency_ms: float,
    error_rate: float,
    within_slo: bool,
    remediation_items: list[str],
) -> PracticePostmortem:
    outcome = "within_slo" if ok else "needs_remediation"
    summary = (
        f"Load {profile}: tenants={tenants}, p95={p95_latency_ms:.1f}ms, "
        f"error_rate={error_rate:.4f}, within_slo={within_slo}."
    )
    improve = list(remediation_items)
    improve.append("DevOps: schedule non-prod field harness (k6/locust) at 50 tenants.")
    return PracticePostmortem(
        run_id=run_id,
        profile=profile,
        outcome=outcome,
        summary=summary,
        tenants=tenants,
        p95_latency_ms=p95_latency_ms,
        error_rate=error_rate,
        within_slo=within_slo,
        what_went_well=(
            [
                "50-tenant pooled-tier shape exercised in CI",
                "SLO gates measured and recorded",
                "Remediation plan emitted (held or needs_remediation)",
                "Auth-gated load HTTP",
            ]
            if ok
            else ["Harness recorded SLO miss with documented remediation"]
        ),
        what_to_improve=improve,
        residuals=[
            "Field 2h sustained soak — DevOps residual",
            "Live prod traffic / prod kill not performed",
            "Stage 6 GHCR remains quarantined",
            "No Production GO",
        ],
        written_at=datetime.now(UTC).isoformat(),
    )
