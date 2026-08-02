"""STORY-10-04 — CAP-085 Scoring Rules Studio models (deterministic).

Tenant dimension-weight overrides + attribute boosts over platform defaults.
Not Production GO. DEC-085 untouched. No Alembic / FORCE RLS.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

TargetType = Literal["lead", "company", "opportunity"]
BoostOp = Literal["eq", "neq", "gte", "lte", "gt", "lt", "contains", "exists"]

# Mirrors domains.scoring.engine.ScoringEngine._compute_overall defaults.
PLATFORM_DEFAULT_WEIGHTS: dict[str, float] = {
    "buying_intent": 0.30,
    "engagement": 0.20,
    "fit": 0.15,
    "urgency": 0.15,
    "relationship": 0.10,
    "market_signal": 0.10,
}

VALID_DIMENSIONS = frozenset(PLATFORM_DEFAULT_WEIGHTS)
VALID_TARGET_TYPES = frozenset({"lead", "company", "opportunity"})
VALID_BOOST_OPS = frozenset({"eq", "neq", "gte", "lte", "gt", "lt", "contains", "exists"})


class ScoringRuleError(ValueError):
    """Invalid scoring rule definition or evaluation input."""


@dataclass
class ScoringBoost:
    """Deterministic attribute boost applied after weighted dimensions."""

    field: str
    op: BoostOp
    value: Any = None
    delta: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "op": self.op,
            "value": self.value,
            "delta": self.delta,
        }


@dataclass
class ScoringRule:
    """Tenant-scoped scoring rule (in-memory Studio draft)."""

    id: str
    tenant_id: str
    name: str
    target_type: TargetType
    dimension_weights: dict[str, float] = field(default_factory=dict)
    boosts: list[ScoringBoost] = field(default_factory=list)
    active: bool = True
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "target_type": self.target_type,
            "dimension_weights": dict(self.dimension_weights),
            "boosts": [b.as_dict() for b in self.boosts],
            "active": self.active,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def validate_dimension_weights(weights: dict[str, float]) -> dict[str, float]:
    if not weights:
        raise ScoringRuleError("dimension_weights required (non-empty)")
    cleaned: dict[str, float] = {}
    for key, raw in weights.items():
        dim = str(key).strip().lower()
        if dim not in VALID_DIMENSIONS:
            raise ScoringRuleError(f"unknown dimension: {key}")
        try:
            val = float(raw)
        except (TypeError, ValueError) as exc:
            raise ScoringRuleError(f"invalid weight for {dim}") from exc
        if val < 0:
            raise ScoringRuleError(f"weight for {dim} must be >= 0")
        cleaned[dim] = val
    if sum(cleaned.values()) <= 0:
        raise ScoringRuleError("dimension_weights must sum to > 0")
    return cleaned


def validate_boosts(raw_boosts: Sequence[Any] | None) -> list[ScoringBoost]:
    out: list[ScoringBoost] = []
    for item in raw_boosts or []:
        if isinstance(item, ScoringBoost):
            boost = item
        elif isinstance(item, dict):
            field_name = str(item.get("field") or "").strip()
            op = str(item.get("op") or "").strip().lower()
            if not field_name:
                raise ScoringRuleError("boost.field required")
            if op not in VALID_BOOST_OPS:
                raise ScoringRuleError(f"unsupported boost op: {op}")
            try:
                delta = float(item.get("delta", 0.0))
            except (TypeError, ValueError) as exc:
                raise ScoringRuleError("boost.delta must be numeric") from exc
            boost = ScoringBoost(
                field=field_name,
                op=op,  # type: ignore[arg-type]
                value=item.get("value"),
                delta=delta,
            )
        else:
            raise ScoringRuleError("boost must be a mapping or ScoringBoost")
        if boost.op not in VALID_BOOST_OPS:
            raise ScoringRuleError(f"unsupported boost op: {boost.op}")
        if not (boost.field or "").strip():
            raise ScoringRuleError("boost.field required")
        out.append(boost)
    return out


def build_scoring_rule(
    *,
    tenant_id: str,
    name: str,
    target_type: str,
    dimension_weights: dict[str, float],
    boosts: list[dict[str, Any]] | list[ScoringBoost] | None = None,
    active: bool = True,
    rule_id: str = "",
    schema_version: int = 1,
) -> ScoringRule:
    tid = (tenant_id or "").strip()
    if not tid:
        raise ScoringRuleError("tenant_id required")
    nm = (name or "").strip()
    if not nm:
        raise ScoringRuleError("name required")
    tt = (target_type or "").strip().lower()
    if tt not in VALID_TARGET_TYPES:
        raise ScoringRuleError(f"target_type must be one of {sorted(VALID_TARGET_TYPES)}")
    return ScoringRule(
        id=rule_id,
        tenant_id=tid,
        name=nm,
        target_type=tt,  # type: ignore[arg-type]
        dimension_weights=validate_dimension_weights(dimension_weights),
        boosts=validate_boosts(list(boosts or [])),
        active=bool(active),
        schema_version=max(int(schema_version), 1),
    )
