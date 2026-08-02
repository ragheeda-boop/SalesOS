"""STORY-10-04 — Scoring rule evaluation with fail-safe platform fallback.

Fail-safe (not fail-open): tenant rule errors → platform default score.
Pluggable into existing ScoringEngine dimension weights (CAP-085).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.modules.tenant_studio.scoring_rules import (
    PLATFORM_DEFAULT_WEIGHTS,
    ScoringBoost,
    ScoringRule,
    ScoringRuleError,
)

ScoreSource = Literal["tenant_rule", "platform_default"]


@dataclass
class ScoringEvalResult:
    score: float
    source: ScoreSource
    fallback_used: bool = False
    fallback_reason: str | None = None
    rule_id: str | None = None
    explanation: list[str] = field(default_factory=list)
    dimension_weights_used: dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "source": self.source,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
            "rule_id": self.rule_id,
            "explanation": list(self.explanation),
            "dimension_weights_used": dict(self.dimension_weights_used),
        }


def _clamp01(value: float) -> float:
    return round(min(max(float(value), 0.0), 1.0), 4)


def _match_boost(boost: ScoringBoost, attributes: dict[str, Any]) -> bool:
    key = boost.field
    if boost.op == "exists":
        return key in attributes and attributes[key] is not None
    if key not in attributes:
        return False
    actual = attributes[key]
    expected = boost.value
    if boost.op == "eq":
        return bool(actual == expected)
    if boost.op == "neq":
        return bool(actual != expected)
    if boost.op == "contains":
        return str(expected) in str(actual)
    try:
        a = float(actual)
        e = float(expected)
    except (TypeError, ValueError) as exc:
        raise ScoringRuleError(f"numeric compare failed for boost field {key}") from exc
    if boost.op == "gte":
        return a >= e
    if boost.op == "lte":
        return a <= e
    if boost.op == "gt":
        return a > e
    if boost.op == "lt":
        return a < e
    raise ScoringRuleError(f"unsupported boost op at eval: {boost.op}")


def score_with_weights(
    *,
    dimension_scores: dict[str, float],
    weights: dict[str, float],
    boosts: list[ScoringBoost] | None = None,
    attributes: dict[str, Any] | None = None,
) -> tuple[float, list[str], dict[str, float]]:
    """Weighted dimension score + boosts. Raises ScoringRuleError on bad input."""
    if not weights:
        raise ScoringRuleError("empty weights")
    total_w = sum(float(v) for v in weights.values())
    if total_w <= 0:
        raise ScoringRuleError("weights must sum to > 0")

    dims = {str(k).lower(): float(v) for k, v in (dimension_scores or {}).items()}
    explanation: list[str] = []
    weighted = 0.0
    used_weights: dict[str, float] = {}
    for dim, w in weights.items():
        wf = float(w)
        if wf <= 0:
            continue
        used_weights[dim] = wf
        val = dims.get(dim, 0.0)
        if val < 0 or val > 1:
            raise ScoringRuleError(f"dimension score out of range: {dim}={val}")
        weighted += val * wf
        explanation.append(f"{dim}={val:.4f}*{wf:.4f}")

    if not used_weights:
        raise ScoringRuleError("no positive weights to apply")

    base = weighted / sum(used_weights.values())
    score = base
    attrs = attributes or {}
    for boost in boosts or []:
        if _match_boost(boost, attrs):
            score += float(boost.delta)
            explanation.append(f"boost {boost.field} {boost.op} → +{boost.delta}")
    return _clamp01(score), explanation, used_weights


def platform_default_score(
    dimension_scores: dict[str, float],
    *,
    attributes: dict[str, Any] | None = None,
) -> ScoringEvalResult:
    score, explanation, used = score_with_weights(
        dimension_scores=dimension_scores,
        weights=dict(PLATFORM_DEFAULT_WEIGHTS),
        boosts=None,
        attributes=attributes,
    )
    return ScoringEvalResult(
        score=score,
        source="platform_default",
        fallback_used=False,
        rule_id=None,
        explanation=explanation,
        dimension_weights_used=used,
    )


def apply_tenant_rule(
    rule: ScoringRule,
    dimension_scores: dict[str, float],
    *,
    attributes: dict[str, Any] | None = None,
) -> ScoringEvalResult:
    if not rule.active:
        raise ScoringRuleError("rule inactive")
    score, explanation, used = score_with_weights(
        dimension_scores=dimension_scores,
        weights=dict(rule.dimension_weights),
        boosts=list(rule.boosts),
        attributes=attributes,
    )
    return ScoringEvalResult(
        score=score,
        source="tenant_rule",
        fallback_used=False,
        rule_id=rule.id or None,
        explanation=explanation,
        dimension_weights_used=used,
    )


def evaluate_score(
    *,
    dimension_scores: dict[str, float],
    rule: ScoringRule | None = None,
    attributes: dict[str, Any] | None = None,
) -> ScoringEvalResult:
    """Evaluate with tenant rule when present; fail-safe to platform default."""
    if rule is None:
        return platform_default_score(dimension_scores, attributes=attributes)
    try:
        return apply_tenant_rule(rule, dimension_scores, attributes=attributes)
    except Exception as exc:  # noqa: BLE001 — fail-safe contract
        fallback = platform_default_score(dimension_scores, attributes=attributes)
        fallback.fallback_used = True
        fallback.fallback_reason = str(exc) or type(exc).__name__
        fallback.rule_id = rule.id or None
        fallback.explanation = [
            f"tenant rule error: {fallback.fallback_reason}",
            *fallback.explanation,
        ]
        return fallback


def get_effective_dimension_weights(
    rule: ScoringRule | None,
) -> tuple[dict[str, float], bool, str | None]:
    """Weights for ScoringEngine._compute_overall; fail-safe to platform."""
    if rule is None or not rule.active:
        return dict(PLATFORM_DEFAULT_WEIGHTS), False, None
    try:
        weights = dict(rule.dimension_weights)
        if sum(weights.values()) <= 0:
            raise ScoringRuleError("weights must sum to > 0")
        return weights, False, None
    except Exception as exc:  # noqa: BLE001
        return dict(PLATFORM_DEFAULT_WEIGHTS), True, str(exc) or type(exc).__name__
