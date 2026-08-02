"""STORY-10-05 — Deterministic territory rule evaluation (CAP-087 → CAP-017).

Config compiler only — does not mutate revenue TerritoryRepository.
Not Production GO.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.modules.tenant_studio.territories import TerritoryMatchCondition, TerritoryRule


@dataclass
class TerritoryAssignResult:
    """Outcome of evaluating account attributes against tenant territory rules."""

    matched: bool
    territory_key: str | None = None
    rule_id: str | None = None
    region: str = ""
    rep_id: str = ""
    source: str = "unmatched"
    explanation: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "matched": self.matched,
            "territory_key": self.territory_key,
            "rule_id": self.rule_id,
            "region": self.region,
            "rep_id": self.rep_id,
            "source": self.source,
            "explanation": list(self.explanation),
        }


def _attr_value(attributes: dict[str, Any], key: str) -> Any:
    if key in attributes:
        return attributes[key]
    # case-insensitive fallback
    lower = {str(k).lower(): v for k, v in attributes.items()}
    return lower.get(key)


def _as_number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def condition_matches(cond: TerritoryMatchCondition, attributes: dict[str, Any]) -> bool:
    raw = _attr_value(attributes, cond.field)
    op = cond.op
    expected = cond.value

    if op == "eq":
        return raw == expected or (raw is not None and str(raw).lower() == str(expected).lower())
    if op == "neq":
        return not (
            raw == expected or (raw is not None and str(raw).lower() == str(expected).lower())
        )
    if op == "contains":
        if raw is None or expected is None:
            return False
        return str(expected).lower() in str(raw).lower()
    if op == "in":
        if not isinstance(expected, list | tuple | set):
            return False
        if raw in expected:
            return True
        raw_l = str(raw).lower() if raw is not None else ""
        return any(str(x).lower() == raw_l for x in expected)
    if op in {"gte", "lte", "gt", "lt"}:
        left = _as_number(raw)
        right = _as_number(expected)
        if left is None or right is None:
            return False
        if op == "gte":
            return left >= right
        if op == "lte":
            return left <= right
        if op == "gt":
            return left > right
        return left < right
    return False


def rule_matches(rule: TerritoryRule, attributes: dict[str, Any]) -> bool:
    if not rule.active:
        return False
    return all(condition_matches(c, attributes) for c in rule.match_conditions)


def assign_territory(
    *,
    rules: list[TerritoryRule],
    attributes: dict[str, Any] | None = None,
) -> TerritoryAssignResult:
    """Pick highest-priority (lowest priority int) matching active rule.

    On no match: honest unmatched — does not invent a territory.
    """
    attrs = dict(attributes or {})
    candidates = [r for r in rules if rule_matches(r, attrs)]
    if not candidates:
        return TerritoryAssignResult(
            matched=False,
            source="unmatched",
            explanation=["no active territory rule matched attributes"],
        )
    # Lower priority number wins; tie-break newest updated_at, then id.
    candidates.sort(key=lambda r: (r.priority, r.updated_at or "", r.id), reverse=False)
    # Among equal priority, prefer lexicographically latest updated_at.
    by_prio: dict[int, list[TerritoryRule]] = {}
    for r in candidates:
        by_prio.setdefault(r.priority, []).append(r)
    best_prio = min(by_prio)
    tied = sorted(by_prio[best_prio], key=lambda r: (r.updated_at or "", r.id), reverse=True)
    winner = tied[0]
    return TerritoryAssignResult(
        matched=True,
        territory_key=winner.territory_key,
        rule_id=winner.id,
        region=winner.region,
        rep_id=winner.rep_id,
        source="tenant_rule",
        explanation=[
            f"matched rule {winner.id} ({winner.name})",
            f"priority={winner.priority}",
        ],
    )
