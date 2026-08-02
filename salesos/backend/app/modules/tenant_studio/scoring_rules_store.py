"""STORY-10-04 — In-memory Scoring Rules store (no Alembic / FORCE RLS)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.modules.tenant_studio.scoring_rules import (
    ScoringRule,
    ScoringRuleError,
    build_scoring_rule,
)
from app.modules.tenant_studio.scoring_rules_engine import (
    ScoringEvalResult,
    evaluate_score,
)


@dataclass
class MemScoringRulesStore:
    """Tenant-scoped scoring rules for CAP-085 Studio."""

    _by_id: dict[str, ScoringRule] = field(default_factory=dict)

    def upsert(
        self,
        *,
        tenant_id: str,
        name: str,
        target_type: str,
        dimension_weights: dict[str, float],
        boosts: list[dict[str, Any]] | None = None,
        active: bool = True,
        rule_id: str | None = None,
    ) -> ScoringRule:
        tid = str(tenant_id)
        now = datetime.now(UTC).isoformat()
        rid = (rule_id or "").strip()
        existing = self._by_id.get(rid) if rid else None
        if existing and existing.tenant_id != tid:
            raise PermissionError("cross-tenant scoring rule write blocked")
        schema_version = 1
        created_at = now
        if existing:
            schema_version = max(existing.schema_version + 1, 1)
            created_at = existing.created_at or now
        else:
            rid = rid or uuid.uuid4().hex[:12]

        rule = build_scoring_rule(
            tenant_id=tid,
            name=name,
            target_type=target_type,
            dimension_weights=dimension_weights,
            boosts=boosts,
            active=active,
            rule_id=rid,
            schema_version=schema_version,
        )
        rule.created_at = created_at
        rule.updated_at = now
        self._by_id[rule.id] = rule
        return rule

    def get(self, rule_id: str, *, tenant_id: str) -> ScoringRule | None:
        row = self._by_id.get(str(rule_id))
        if row is None or row.tenant_id != str(tenant_id):
            return None
        return row

    def list_for_tenant(self, *, tenant_id: str) -> list[ScoringRule]:
        tid = str(tenant_id)
        return sorted(
            [r for r in self._by_id.values() if r.tenant_id == tid],
            key=lambda r: r.updated_at or "",
            reverse=True,
        )

    def get_active_for_target(self, *, tenant_id: str, target_type: str) -> ScoringRule | None:
        tid = str(tenant_id)
        tt = (target_type or "").strip().lower()
        matches = [
            r
            for r in self._by_id.values()
            if r.tenant_id == tid and r.target_type == tt and r.active
        ]
        if not matches:
            return None
        return sorted(matches, key=lambda r: r.updated_at or "", reverse=True)[0]

    def evaluate(
        self,
        *,
        tenant_id: str,
        target_type: str,
        dimension_scores: dict[str, float],
        attributes: dict[str, Any] | None = None,
        rule_id: str | None = None,
    ) -> ScoringEvalResult:
        rule: ScoringRule | None
        if rule_id:
            rule = self.get(rule_id, tenant_id=tenant_id)
            if rule is None:
                raise ScoringRuleError("scoring rule not found")
        else:
            rule = self.get_active_for_target(tenant_id=tenant_id, target_type=target_type)
        return evaluate_score(
            dimension_scores=dimension_scores,
            rule=rule,
            attributes=attributes,
        )


DEFAULT_SCORING_RULES_STORE = MemScoringRulesStore()
