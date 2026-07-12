"""AI Evaluation framework — built-in metrics and batch evaluation."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from domains.ai.models import AIEvaluation, EvaluationMetric


def exact_match(output: str, expected: str) -> float:
    return 1.0 if output.strip() == expected.strip() else 0.0


def contains_keyword(output: str, keyword: str) -> float:
    return 1.0 if keyword.lower() in output.lower() else 0.0


def length_check(output: str, min_len: int = 1, max_len: int | None = None) -> float:
    length = len(output.strip())
    if length < min_len:
        return 0.0
    if max_len is not None and length > max_len:
        return 0.0
    return 1.0


def json_valid(output: str) -> float:
    try:
        json.loads(output)
        return 1.0
    except (json.JSONDecodeError, ValueError):
        return 0.0


def confidence_threshold(output: str, threshold: float = 0.7) -> float:
    try:
        data = json.loads(output)
        confidence = float(data.get("confidence", 0))
        return 1.0 if confidence >= threshold else 0.0
    except (json.JSONDecodeError, ValueError, TypeError):
        return 0.0


BUILTIN_METRICS = {
    "exact_match": exact_match,
    "contains_keyword": contains_keyword,
    "length_check": length_check,
    "json_valid": json_valid,
    "confidence_threshold": confidence_threshold,
}


class AIEvaluator:
    def __init__(self, registry: Any | None = None) -> None:
        self._registry = registry
        self._evaluations: list[AIEvaluation] = []

    def evaluate(
        self,
        prompt_id: str,
        input: str,
        output: str,
        expected: str | None = None,
        metrics: list[str] | None = None,
        thresholds: dict[str, float] | None = None,
    ) -> AIEvaluation:
        metric_results: list[EvaluationMetric] = []
        thresholds = thresholds or {}
        names = metrics or list(BUILTIN_METRICS.keys())

        passed_count = 0
        for name in names:
            fn = BUILTIN_METRICS.get(name)
            if fn is None:
                continue
            threshold = thresholds.get(name, 0.5)
            if name == "exact_match":
                value = fn(output, expected or "")
            elif name == "contains_keyword":
                keyword = expected or output
                value = fn(output, keyword)
            elif name == "length_check":
                value = fn(output, min_len=1)
            elif name == "json_valid":
                value = fn(output)
            elif name == "confidence_threshold":
                value = fn(output, threshold=threshold)
            else:
                value = fn(output)
            metric_results.append(EvaluationMetric(
                name=name, value=value, threshold=threshold, passed=value >= threshold,
            ))
            if value >= threshold:
                passed_count += 1

        score = passed_count / max(len(metric_results), 1)
        evaluation = AIEvaluation(
            id=uuid.uuid4().hex[:12],
            prompt_id=prompt_id,
            input=input,
            output=output,
            expected=expected,
            score=score,
            metrics=metric_results,
            timestamp=datetime.now(timezone.utc),
        )
        self._evaluations.append(evaluation)
        return evaluation

    def evaluate_batch(self, results: list[dict[str, Any]]) -> list[AIEvaluation]:
        evaluations = []
        for r in results:
            evaluations.append(self.evaluate(
                prompt_id=r["prompt_id"],
                input=r.get("input", ""),
                output=r["output"],
                expected=r.get("expected"),
                metrics=r.get("metrics"),
                thresholds=r.get("thresholds"),
            ))
        return evaluations

    def get_metrics(self, prompt_id: str) -> dict[str, Any]:
        relevant = [e for e in self._evaluations if e.prompt_id == prompt_id]
        if not relevant:
            return {"prompt_id": prompt_id, "total_evaluations": 0}

        total = len(relevant)
        avg_score = sum(e.score for e in relevant) / total
        metric_avgs: dict[str, float] = {}
        metric_pass_rates: dict[str, float] = {}
        for e in relevant:
            for m in e.metrics:
                if m.name not in metric_avgs:
                    metric_avgs[m.name] = 0.0
                    metric_pass_rates[m.name] = 0.0
                metric_avgs[m.name] += m.value
                metric_pass_rates[m.name] += 1.0 if m.passed else 0.0
        for k in metric_avgs:
            metric_avgs[k] /= total
            metric_pass_rates[k] = metric_pass_rates[k] / total * 100

        return {
            "prompt_id": prompt_id,
            "total_evaluations": total,
            "average_score": round(avg_score, 3),
            "metrics": {
                k: {"average_value": round(v, 3), "pass_rate": round(metric_pass_rates[k], 1)}
                for k, v in metric_avgs.items()
            },
        }
