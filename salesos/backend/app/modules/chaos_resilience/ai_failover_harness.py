"""STORY-14-06 — AI provider failover harness (extends 14-02 chaos).

Non-prod / CI only. Not Production GO. feature_ai_copilot remains False.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.config import settings
from app.modules.chaos_resilience.ai_failover import (
    VALID_AI_FAILOVER_SCENARIOS,
    FailoverRunResult,
    run_failover_chain,
)
from app.modules.chaos_resilience.faults import AI_FAILOVER_SLO_SECONDS
from app.modules.chaos_resilience.postmortem import (
    PracticePostmortem,
    write_practice_postmortem,
)


@dataclass
class AiFailoverDrill:
    id: str
    scenario: str
    result: dict[str, Any] = field(default_factory=dict)
    postmortem: dict[str, Any] = field(default_factory=dict)
    ran_at: str = ""
    honesty: str = (
        "STORY-14-06 non-prod AI failover harness (fake providers). "
        "Live LLM kill / feature_ai_copilot / Production GO not claimed."
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "scenario": self.scenario,
            "ok": bool(self.result.get("ok")),
            "graceful": bool(self.result.get("graceful")),
            "within_slo": bool(self.result.get("within_slo")),
            "result": dict(self.result),
            "postmortem": dict(self.postmortem),
            "ran_at": self.ran_at,
            "honesty": self.honesty,
        }


@dataclass
class MemAiFailoverHarness:
    """Process-local AI failover drills + practice postmortems."""

    _drills: dict[str, AiFailoverDrill] = field(default_factory=dict)
    _postmortems: dict[str, PracticePostmortem] = field(default_factory=dict)

    def run(self, scenario: str) -> AiFailoverDrill:
        kind = (scenario or "").strip().lower()
        if kind not in VALID_AI_FAILOVER_SCENARIOS:
            raise ValueError(
                f"unknown scenario={scenario!r}; expected one of "
                f"{sorted(VALID_AI_FAILOVER_SCENARIOS)}"
            )
        outcome: FailoverRunResult = run_failover_chain(scenario=kind)
        drill_id = uuid.uuid4().hex[:12]
        # Reuse 14-02 postmortem writer with AI fault kind for consistency.
        pm = write_practice_postmortem(
            drill_id=drill_id,
            fault_kind="ai_provider_outage",
            graceful=outcome.graceful and outcome.ok,
            detail=outcome.as_dict(),
        )
        # Annotate STORY-14-06 ownership on residual list.
        pm.residuals = [
            "STORY-14-06 CI/non-prod harness — live staging provider kill is Ops field",
            f"feature_ai_copilot={settings.feature_ai_copilot}",
            "No Production GO",
        ]
        pm.summary = (
            f"STORY-14-06 scenario={kind}: selected={outcome.selected!r}, "
            f"within_slo={outcome.within_slo}, elapsed_ms={outcome.elapsed_ms:.3f}."
        )
        report = AiFailoverDrill(
            id=drill_id,
            scenario=kind,
            result=outcome.as_dict(),
            postmortem=pm.as_dict(),
            ran_at=datetime.now(UTC).isoformat(),
        )
        self._drills[drill_id] = report
        self._postmortems[drill_id] = pm
        return report

    def run_all(self) -> list[AiFailoverDrill]:
        return [self.run(s) for s in sorted(VALID_AI_FAILOVER_SCENARIOS)]

    def list_drills(self) -> list[AiFailoverDrill]:
        return sorted(self._drills.values(), key=lambda d: d.ran_at)

    def get_drill(self, drill_id: str) -> AiFailoverDrill | None:
        return self._drills.get(str(drill_id))

    def list_postmortems(self) -> list[PracticePostmortem]:
        return sorted(self._postmortems.values(), key=lambda p: p.written_at)

    def meta(self) -> dict[str, Any]:
        return {
            "story": "STORY-14-06",
            "builds_on": "STORY-14-02",
            "scenarios": sorted(VALID_AI_FAILOVER_SCENARIOS),
            "ai_failover_slo_seconds": AI_FAILOVER_SLO_SECONDS,
            "providers": "fake MemFakeProvider chain (openai→anthropic→gemini)",
            "persistence": "memory",
            "feature_ai_copilot": settings.feature_ai_copilot,
            "live_llm": False,
            "environment": "non-prod/CI",
            "honesty": (
                "Non-prod AI provider failover harness on 14-02 chaos base. "
                "Live LLM / Production GO not claimed."
            ),
        }


DEFAULT_AI_FAILOVER_HARNESS = MemAiFailoverHarness()
