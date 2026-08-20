"""STORY-14-07 — LLM regression harness (non-prod / CI).

Not Production GO. feature_ai_copilot remains False. No live LLM.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.config import settings
from app.modules.chaos_resilience.llm_regression import (
    GOLDEN_CASES,
    SIMILARITY_THRESHOLD,
    VALID_LLM_REGRESSION_MODES,
    RegressionRunResult,
    run_llm_regression,
)
from app.modules.chaos_resilience.postmortem import (
    PracticePostmortem,
    write_practice_postmortem,
)


@dataclass
class LlmRegressionDrill:
    id: str
    mode: str
    result: dict[str, Any] = field(default_factory=dict)
    postmortem: dict[str, Any] = field(default_factory=dict)
    ran_at: str = ""
    honesty: str = (
        "STORY-14-07 non-prod LLM regression suite (golden fixtures). "
        "Live LLM / feature_ai_copilot / Production GO not claimed."
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "mode": self.mode,
            "ok": bool(self.result.get("ok")),
            "baseline_established": bool(self.result.get("baseline_established")),
            "regression_detected": bool(self.result.get("regression_detected")),
            "promotion_blocked": bool(self.result.get("promotion_blocked")),
            "result": dict(self.result),
            "postmortem": dict(self.postmortem),
            "ran_at": self.ran_at,
            "honesty": self.honesty,
        }


@dataclass
class MemLlmRegressionHarness:
    """Process-local LLM regression drills + practice postmortems."""

    _drills: dict[str, LlmRegressionDrill] = field(default_factory=dict)
    _postmortems: dict[str, PracticePostmortem] = field(default_factory=dict)

    def run(self, mode: str) -> LlmRegressionDrill:
        kind = (mode or "").strip().lower()
        if kind not in VALID_LLM_REGRESSION_MODES:
            raise ValueError(
                f"unknown mode={mode!r}; expected one of " f"{sorted(VALID_LLM_REGRESSION_MODES)}"
            )
        outcome: RegressionRunResult = run_llm_regression(mode=kind)
        drill_id = uuid.uuid4().hex[:12]
        pm = write_practice_postmortem(
            drill_id=drill_id,
            fault_kind="ai_provider_outage",
            graceful=outcome.ok,
            detail=outcome.as_dict(),
        )
        pm.residuals = [
            "STORY-14-07 CI/non-prod golden suite — live provider model update watch is Ops field",
            f"feature_ai_copilot={settings.feature_ai_copilot}",
            "No Production GO",
            "No live LLM calls",
        ]
        pm.what_to_improve = [
            "Ops residual: wire suite to real provider model-update events post-GA",
        ]
        pm.summary = (
            f"STORY-14-07 mode={kind}: ok={outcome.ok}, "
            f"baseline_established={outcome.baseline_established}, "
            f"regression_detected={outcome.regression_detected}, "
            f"promotion_blocked={outcome.promotion_blocked}, "
            f"cases={outcome.cases_passed}/{outcome.cases_total}."
        )
        report = LlmRegressionDrill(
            id=drill_id,
            mode=kind,
            result=outcome.as_dict(),
            postmortem=pm.as_dict(),
            ran_at=datetime.now(UTC).isoformat(),
        )
        self._drills[drill_id] = report
        self._postmortems[drill_id] = pm
        return report

    def run_all(self) -> list[LlmRegressionDrill]:
        return [self.run(m) for m in sorted(VALID_LLM_REGRESSION_MODES)]

    def list_drills(self) -> list[LlmRegressionDrill]:
        return sorted(self._drills.values(), key=lambda d: d.ran_at)

    def get_drill(self, drill_id: str) -> LlmRegressionDrill | None:
        return self._drills.get(str(drill_id))

    def list_postmortems(self) -> list[PracticePostmortem]:
        return sorted(self._postmortems.values(), key=lambda p: p.written_at)

    def meta(self) -> dict[str, Any]:
        return {
            "story": "STORY-14-07",
            "builds_on": ["STORY-14-02", "domains.ai.AIEvaluator metrics pattern"],
            "modes": sorted(VALID_LLM_REGRESSION_MODES),
            "similarity_threshold": SIMILARITY_THRESHOLD,
            "golden_cases": len(GOLDEN_CASES),
            "persistence": "memory",
            "feature_ai_copilot": settings.feature_ai_copilot,
            "live_llm": False,
            "environment": "non-prod/CI",
            "honesty": (
                "Non-prod LLM regression suite: golden outputs + token Jaccard. "
                "Detects injected quality regression. Live LLM / Production GO not claimed."
            ),
        }


DEFAULT_LLM_REGRESSION_HARNESS = MemLlmRegressionHarness()
