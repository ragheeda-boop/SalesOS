"""STORY-14-02 — Chaos drill harness (connector / AI / DB fault injection).

CI in-memory only. Not Production GO. DEC-085 untouched. No FORCE RLS.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.config import settings
from app.modules.chaos_resilience.faults import VALID_FAULT_KINDS
from app.modules.chaos_resilience.handlers import (
    HandlerOutcome,
    handle_ai_provider_outage,
    handle_connector_outage,
    handle_db_failover,
)
from app.modules.chaos_resilience.postmortem import (
    PracticePostmortem,
    write_practice_postmortem,
)


@dataclass
class DrillReport:
    id: str
    fault_kind: str
    ok: bool
    graceful: bool
    handler: dict[str, Any] = field(default_factory=dict)
    postmortem: dict[str, Any] = field(default_factory=dict)
    ran_at: str = ""
    honesty: str = (
        "CI chaos harness only; live connector/AI/DB kill not performed. "
        f"Not Production GO. feature_ai_copilot={settings.feature_ai_copilot}."
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "fault_kind": self.fault_kind,
            "ok": self.ok,
            "graceful": self.graceful,
            "handler": dict(self.handler),
            "postmortem": dict(self.postmortem),
            "ran_at": self.ran_at,
            "honesty": self.honesty,
        }


@dataclass
class MemChaosHarness:
    """Process-local drill history + practice postmortems."""

    _drills: dict[str, DrillReport] = field(default_factory=dict)
    _postmortems: dict[str, PracticePostmortem] = field(default_factory=dict)

    def run(self, fault_kind: str) -> DrillReport:
        kind = (fault_kind or "").strip().lower()
        if kind not in VALID_FAULT_KINDS:
            raise ValueError(
                f"unknown fault_kind={fault_kind!r}; expected one of {sorted(VALID_FAULT_KINDS)}"
            )
        outcome = self._dispatch(kind)
        drill_id = uuid.uuid4().hex[:12]
        pm = write_practice_postmortem(
            drill_id=drill_id,
            fault_kind=kind,
            graceful=outcome.graceful and outcome.ok,
            detail=outcome.detail,
        )
        report = DrillReport(
            id=drill_id,
            fault_kind=kind,
            ok=outcome.ok,
            graceful=outcome.graceful,
            handler=outcome.as_dict(),
            postmortem=pm.as_dict(),
            ran_at=datetime.now(UTC).isoformat(),
        )
        self._drills[drill_id] = report
        self._postmortems[drill_id] = pm
        return report

    def _dispatch(self, kind: str) -> HandlerOutcome:
        if kind == "connector_outage":
            return handle_connector_outage()
        if kind == "ai_provider_outage":
            return handle_ai_provider_outage()
        if kind == "db_failover":
            return handle_db_failover()
        raise ValueError(f"unhandled fault_kind={kind}")

    def list_drills(self) -> list[DrillReport]:
        return sorted(self._drills.values(), key=lambda d: d.ran_at)

    def get_drill(self, drill_id: str) -> DrillReport | None:
        return self._drills.get(str(drill_id))

    def list_postmortems(self) -> list[PracticePostmortem]:
        return sorted(self._postmortems.values(), key=lambda p: p.written_at)

    def run_all(self) -> list[DrillReport]:
        return [self.run(k) for k in sorted(VALID_FAULT_KINDS)]


DEFAULT_CHAOS_HARNESS = MemChaosHarness()
