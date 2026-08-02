"""STORY-10-05 — CAP-087 Territory Rules Studio models (deterministic).

Tenant-defined geography / industry / size rules over CAP-017 runtime.
Not Production GO. DEC-085 untouched. No Alembic / FORCE RLS.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

MatchOp = Literal["eq", "neq", "in", "contains", "gte", "lte", "gt", "lt"]

VALID_MATCH_FIELDS = frozenset(
    {
        "region",
        "country",
        "city",
        "industry",
        "sector",
        "company_size",
        "employee_count",
        "account_id",
    }
)
VALID_MATCH_OPS = frozenset({"eq", "neq", "in", "contains", "gte", "lte", "gt", "lt"})


class TerritoryRuleError(ValueError):
    """Invalid territory rule definition or evaluation input."""


@dataclass
class TerritoryMatchCondition:
    """Deterministic attribute match for territory assignment."""

    field: str
    op: MatchOp
    value: Any = None

    def as_dict(self) -> dict[str, Any]:
        return {"field": self.field, "op": self.op, "value": self.value}


@dataclass
class TerritoryRule:
    """Tenant-scoped territory rule (in-memory Studio draft / TerritoryRuleSet row)."""

    id: str
    tenant_id: str
    name: str
    territory_key: str
    region: str = ""
    rep_id: str = ""
    priority: int = 100
    match_conditions: list[TerritoryMatchCondition] = field(default_factory=list)
    active: bool = True
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "territory_key": self.territory_key,
            "region": self.region,
            "rep_id": self.rep_id,
            "priority": self.priority,
            "match_conditions": [c.as_dict() for c in self.match_conditions],
            "active": self.active,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def validate_match_conditions(
    raw: Sequence[Any] | None,
) -> list[TerritoryMatchCondition]:
    out: list[TerritoryMatchCondition] = []
    for item in raw or []:
        if isinstance(item, TerritoryMatchCondition):
            cond = item
        elif isinstance(item, dict):
            field_name = str(item.get("field") or "").strip().lower()
            op = str(item.get("op") or "").strip().lower()
            if not field_name:
                raise TerritoryRuleError("match_conditions.field required")
            if field_name not in VALID_MATCH_FIELDS:
                raise TerritoryRuleError(f"unsupported match field: {field_name}")
            if op not in VALID_MATCH_OPS:
                raise TerritoryRuleError(f"unsupported match op: {op}")
            cond = TerritoryMatchCondition(
                field=field_name,
                op=op,  # type: ignore[arg-type]
                value=item.get("value"),
            )
        else:
            raise TerritoryRuleError("match condition must be a mapping")
        if cond.field not in VALID_MATCH_FIELDS:
            raise TerritoryRuleError(f"unsupported match field: {cond.field}")
        if cond.op not in VALID_MATCH_OPS:
            raise TerritoryRuleError(f"unsupported match op: {cond.op}")
        out.append(cond)
    if not out:
        raise TerritoryRuleError("match_conditions required (non-empty)")
    return out


def build_territory_rule(
    *,
    tenant_id: str,
    name: str,
    territory_key: str,
    match_conditions: list[dict[str, Any]] | list[TerritoryMatchCondition] | None = None,
    region: str = "",
    rep_id: str = "",
    priority: int = 100,
    active: bool = True,
    rule_id: str = "",
    schema_version: int = 1,
) -> TerritoryRule:
    tid = (tenant_id or "").strip()
    if not tid:
        raise TerritoryRuleError("tenant_id required")
    nm = (name or "").strip()
    if not nm:
        raise TerritoryRuleError("name required")
    key = (territory_key or "").strip()
    if not key:
        raise TerritoryRuleError("territory_key required")
    try:
        prio = int(priority)
    except (TypeError, ValueError) as exc:
        raise TerritoryRuleError("priority must be an integer") from exc
    return TerritoryRule(
        id=rule_id,
        tenant_id=tid,
        name=nm,
        territory_key=key,
        region=(region or "").strip(),
        rep_id=(rep_id or "").strip(),
        priority=prio,
        match_conditions=validate_match_conditions(list(match_conditions or [])),
        active=bool(active),
        schema_version=max(int(schema_version), 1),
    )
