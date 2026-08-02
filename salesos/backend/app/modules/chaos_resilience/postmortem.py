"""STORY-14-02 — Practice postmortems for chaos drills (MASTER_EXECUTION_PLAN §8)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class PracticePostmortem:
    drill_id: str
    fault_kind: str
    outcome: str
    summary: str
    what_went_well: list[str] = field(default_factory=list)
    what_to_improve: list[str] = field(default_factory=list)
    residuals: list[str] = field(default_factory=list)
    written_at: str = ""
    honesty: str = "Practice postmortem (drill), not a production incident. " "Not Production GO."

    def as_dict(self) -> dict[str, Any]:
        return {
            "drill_id": self.drill_id,
            "fault_kind": self.fault_kind,
            "outcome": self.outcome,
            "summary": self.summary,
            "what_went_well": list(self.what_went_well),
            "what_to_improve": list(self.what_to_improve),
            "residuals": list(self.residuals),
            "written_at": self.written_at,
            "honesty": self.honesty,
        }


def write_practice_postmortem(
    *,
    drill_id: str,
    fault_kind: str,
    graceful: bool,
    detail: dict[str, Any],
) -> PracticePostmortem:
    _ = detail  # retained for future drill-context enrichment
    outcome = "handled_gracefully" if graceful else "needs_remediation"
    summaries = {
        "connector_outage": (
            "Connector endpoint injection aborted sync cleanly with backoff; "
            "no partial corrupt claimed."
            if graceful
            else "Connector outage path did not abort cleanly."
        ),
        "ai_provider_outage": (
            "Primary AI provider injection engaged failover within SLO (simulated)."
            if graceful
            else "AI provider failover missed SLO or exhausted chain."
        ),
        "db_failover": (
            "DB primary injection: in-flight failed cleanly/retryable; reconnect ok."
            if graceful
            else "DB failover path risked silent loss or non-retryable failure."
        ),
    }
    improve: list[str] = []
    if not graceful:
        improve.append("Track remediation before Sprint 25 gate (Sprint-23 debt rule).")
    if fault_kind == "ai_provider_outage":
        improve.append("STORY-14-06 owns fuller live AI failover drill — this harness is CI-only.")
    return PracticePostmortem(
        drill_id=drill_id,
        fault_kind=fault_kind,
        outcome=outcome,
        summary=summaries.get(fault_kind, "Chaos drill completed."),
        what_went_well=(
            [
                "Fault injection isolated to harness (no live ERP/DB kill)",
                "Auth-gated HTTP surface",
                f"Graceful={graceful}",
            ]
            if graceful
            else ["Harness recorded failure without claiming GO"]
        ),
        what_to_improve=improve,
        residuals=[
            "Live staging chaos against real providers — Ops/DevOps field",
            "R-02 soak / live HubSpot-Odoo GO not claimed",
            "Stage 6 GHCR remains quarantined",
        ],
        written_at=datetime.now(UTC).isoformat(),
    )
