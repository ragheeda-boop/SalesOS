from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from .models import EmployeeScore, EmployeeSignal
from .repository import EmployeeSignalRepository


class EmployeeScoringEngine:
    """Computes employee scores using signal data.
    Factors: signal volume, recency, type diversity, workflow completion rate.
    """

    def __init__(
        self,
        repository: EmployeeSignalRepository,
        scoring_engine: ScoringEngine | None = None,
    ):
        self._repository = repository
        self._scoring_engine = scoring_engine

    async def compute_score(
        self, employee_id: str, tenant_id: str,
        signals: list[EmployeeSignal] | None = None,
    ) -> EmployeeScore:
        if signals is None:
            signals, _, _ = await self._repository.get_by_employee(
                employee_id, tenant_id, limit=500,
            )

        signal_volume = self._compute_signal_volume(signals)
        recency = self._compute_recency(signals)
        diversity = self._compute_diversity(signals)
        completion = self._compute_completion_rate(signals)

        overall = round(
            0.30 * signal_volume +
            0.25 * recency +
            0.20 * diversity +
            0.25 * completion,
            4,
        )

        ci_low, ci_high = self._compute_confidence_interval(overall, len(signals))

        score = EmployeeScore(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            tenant_id=tenant_id,
            overall_score=overall,
            signal_volume_score=round(signal_volume, 4),
            recency_score=round(recency, 4),
            diversity_score=round(diversity, 4),
            completion_rate=round(completion, 4),
            confidence_interval_low=round(ci_low, 4),
            confidence_interval_high=round(ci_high, 4),
            signal_count=len(signals),
        )

        await self._repository.save_score(score)
        return score

    def _compute_signal_volume(self, signals: list[EmployeeSignal]) -> float:
        if not signals:
            return 0.0
        volume = min(len(signals) / 100.0, 1.0)
        return volume

    def _compute_recency(self, signals: list[EmployeeSignal]) -> float:
        if not signals:
            return 0.0
        now = datetime.now(timezone.utc)
        max_days = 90
        max_ts = max(s.timestamp for s in signals if s.timestamp)
        if not max_ts:
            return 0.0
        if max_ts.tzinfo is None:
            max_ts = max_ts.replace(tzinfo=timezone.utc)
        days_since = (now - max_ts).total_seconds() / 86400
        recency = max(0.0, 1.0 - (days_since / max_days))
        return recency

    def _compute_diversity(self, signals: list[EmployeeSignal]) -> float:
        if not signals:
            return 0.0
        types = set(s.signal_type for s in signals)
        sources = set(s.source for s in signals)
        type_score = min(len(types) / 6.0, 1.0)
        source_score = min(len(sources) / 3.0, 1.0)
        return 0.6 * type_score + 0.4 * source_score

    def _compute_completion_rate(self, signals: list[EmployeeSignal]) -> float:
        if not signals:
            return 0.0
        completed = sum(
            1 for s in signals
            if s.signal_type in ("task_completed", "workflow_completed", "approval_completed")
        )
        total_workflow = sum(
            1 for s in signals
            if s.source == "workflow"
        )
        if total_workflow == 0:
            return 0.5 if completed > 0 else 0.0
        return completed / total_workflow

    def _compute_confidence_interval(self, score: float, n: int) -> tuple[float, float]:
        if n < 5:
            margin = 0.25
        elif n < 20:
            margin = 0.15
        elif n < 50:
            margin = 0.10
        else:
            margin = 0.05
        low = max(0.0, score - margin)
        high = min(1.0, score + margin)
        return (low, high)

    async def get_decision_context_factors(
        self, score: EmployeeScore,
    ) -> list[dict[str, Any]]:
        return [
            {
                "source_layer": "measurement",
                "source_domain": "employee_scoring",
                "key": "employee_overall_score",
                "value": score.overall_score,
                "label": "Employee Overall Score",
                "severity": "info" if score.overall_score >= 0.5 else "warning",
            },
            {
                "source_layer": "measurement",
                "source_domain": "employee_scoring",
                "key": "employee_signal_volume",
                "value": score.signal_volume_score,
                "label": "Signal Volume",
                "severity": "info",
            },
            {
                "source_layer": "measurement",
                "source_domain": "employee_scoring",
                "key": "employee_diversity",
                "value": score.diversity_score,
                "label": "Signal Diversity",
                "severity": "info",
            },
            {
                "source_layer": "measurement",
                "source_domain": "employee_scoring",
                "key": "employee_completion_rate",
                "value": score.completion_rate,
                "label": "Workflow Completion Rate",
                "severity": "info" if score.completion_rate >= 0.5 else "warning",
            },
        ]
