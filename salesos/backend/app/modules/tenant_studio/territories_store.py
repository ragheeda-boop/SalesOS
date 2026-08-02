"""STORY-10-05 — In-memory Territory Rules store (no Alembic / FORCE RLS)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.modules.tenant_studio.territories import (
    TerritoryRule,
    TerritoryRuleError,
    build_territory_rule,
)
from app.modules.tenant_studio.territories_engine import (
    TerritoryAssignResult,
    assign_territory,
)


@dataclass
class MemTerritoriesStore:
    """Tenant-scoped territory rules for CAP-087 Studio."""

    _by_id: dict[str, TerritoryRule] = field(default_factory=dict)

    def upsert(
        self,
        *,
        tenant_id: str,
        name: str,
        territory_key: str,
        match_conditions: list[dict[str, Any]] | None = None,
        region: str = "",
        rep_id: str = "",
        priority: int = 100,
        active: bool = True,
        rule_id: str | None = None,
    ) -> TerritoryRule:
        tid = str(tenant_id)
        now = datetime.now(UTC).isoformat()
        rid = (rule_id or "").strip()
        existing = self._by_id.get(rid) if rid else None
        if existing and existing.tenant_id != tid:
            raise PermissionError("cross-tenant territory rule write blocked")
        schema_version = 1
        created_at = now
        if existing:
            schema_version = max(existing.schema_version + 1, 1)
            created_at = existing.created_at or now
        else:
            rid = rid or uuid.uuid4().hex[:12]

        rule = build_territory_rule(
            tenant_id=tid,
            name=name,
            territory_key=territory_key,
            match_conditions=match_conditions,
            region=region,
            rep_id=rep_id,
            priority=priority,
            active=active,
            rule_id=rid,
            schema_version=schema_version,
        )
        rule.created_at = created_at
        rule.updated_at = now
        self._by_id[rule.id] = rule
        return rule

    def get(self, rule_id: str, *, tenant_id: str) -> TerritoryRule | None:
        row = self._by_id.get(str(rule_id))
        if row is None or row.tenant_id != str(tenant_id):
            return None
        return row

    def list_for_tenant(self, *, tenant_id: str) -> list[TerritoryRule]:
        tid = str(tenant_id)
        return sorted(
            [r for r in self._by_id.values() if r.tenant_id == tid],
            key=lambda r: (r.priority, r.updated_at or ""),
        )

    def delete(self, rule_id: str, *, tenant_id: str) -> bool:
        row = self.get(rule_id, tenant_id=tenant_id)
        if row is None:
            return False
        del self._by_id[row.id]
        return True

    def assign(
        self,
        *,
        tenant_id: str,
        attributes: dict[str, Any] | None = None,
        rule_id: str | None = None,
    ) -> TerritoryAssignResult:
        if rule_id:
            rule = self.get(rule_id, tenant_id=tenant_id)
            if rule is None:
                raise TerritoryRuleError("territory rule not found")
            return assign_territory(rules=[rule], attributes=attributes)
        rules = self.list_for_tenant(tenant_id=tenant_id)
        return assign_territory(rules=rules, attributes=attributes)


DEFAULT_TERRITORIES_STORE = MemTerritoriesStore()
