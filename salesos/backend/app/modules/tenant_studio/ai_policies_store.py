"""STORY-12-02 — In-memory AI Policies store (no Alembic / FORCE RLS)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.modules.tenant_studio.ai_policies import (
    AiPolicyError,
    AiPolicySet,
    default_data_class_rules,
    default_guardrails,
    normalize_data_class_rules,
    normalize_guardrails,
)
from app.modules.tenant_studio.ai_policies_engine import evaluate_policy


@dataclass
class MemAiPoliciesStore:
    """Tenant-scoped AI Policy sets for CAP-091 Studio."""

    _by_id: dict[str, AiPolicySet] = field(default_factory=dict)

    def upsert(
        self,
        *,
        tenant_id: str,
        name: str,
        guardrails: dict[str, Any] | None = None,
        data_class_rules: list[dict[str, Any]] | None = None,
        policy_id: str | None = None,
    ) -> AiPolicySet:
        tid = (tenant_id or "").strip()
        if not tid:
            raise AiPolicyError("tenant_id required")
        nm = (name or "").strip()
        if not nm:
            raise AiPolicyError("name required")

        rid = (policy_id or "").strip() or uuid.uuid4().hex[:12]
        existing = self._by_id.get(rid)
        if existing and existing.tenant_id != tid:
            raise PermissionError("cross-tenant ai policy write blocked")

        now = datetime.now(UTC).isoformat()
        row = AiPolicySet(
            id=rid,
            tenant_id=tid,
            name=nm,
            guardrails=normalize_guardrails(guardrails),
            data_class_rules=normalize_data_class_rules(data_class_rules),
            schema_version=(existing.schema_version + 1) if existing else 1,
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        self._by_id[row.id] = row
        return row

    def ensure_default(self, *, tenant_id: str) -> AiPolicySet:
        tid = str(tenant_id)
        for row in self._by_id.values():
            if row.tenant_id == tid:
                return row
        return self.upsert(
            tenant_id=tid,
            name="Default AI Policies",
            guardrails=default_guardrails(),
            data_class_rules=[r.as_dict() for r in default_data_class_rules()],
            policy_id=f"default-{tid[:8]}",
        )

    def get(self, policy_id: str, *, tenant_id: str) -> AiPolicySet | None:
        row = self._by_id.get(str(policy_id))
        if row is None or row.tenant_id != str(tenant_id):
            return None
        return row

    def list_for_tenant(self, *, tenant_id: str) -> list[AiPolicySet]:
        tid = str(tenant_id)
        return sorted(
            [r for r in self._by_id.values() if r.tenant_id == tid],
            key=lambda r: r.updated_at or "",
            reverse=True,
        )

    def delete(self, policy_id: str, *, tenant_id: str) -> bool:
        row = self.get(policy_id, tenant_id=tenant_id)
        if row is None:
            return False
        del self._by_id[row.id]
        return True

    def evaluate(
        self,
        *,
        tenant_id: str,
        data_class: str,
        requested_model_tier: str = "economy",
        sample_text: str = "",
        policy_id: str | None = None,
    ) -> dict[str, Any]:
        if policy_id:
            policy = self.get(policy_id, tenant_id=tenant_id)
            if policy is None:
                raise AiPolicyError("policy not found")
        else:
            policy = self.ensure_default(tenant_id=tenant_id)
        return evaluate_policy(
            policy,
            data_class=data_class,
            requested_model_tier=requested_model_tier,
            sample_text=sample_text,
        )


DEFAULT_AI_POLICIES_STORE = MemAiPoliciesStore()
