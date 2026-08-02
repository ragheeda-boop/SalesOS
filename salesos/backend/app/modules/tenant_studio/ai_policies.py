"""STORY-12-02 — CAP-091 AI Policies models (reuses AI-GR-* guardrails).

Tenant toggles + data-class → model-tier rules. Not Production GO.
DEC-085 untouched. No Alembic / FORCE RLS.
feature_ai_copilot remains False. No live LLM / RAG GO.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Existing guardrail ids (catalog) — reuse, do not reinvent.
AI_GUARDRAIL_CATALOG: dict[str, str] = {
    "AI-GR-001": "PII scrub / input sanitize (intelligence.guardrails)",
    "AI-GR-002": "Prompt-injection / harmful-input detection",
    "AI-GR-003": "LLM output schema validation",
    "AI-GR-004": "Data-class ceiling before model tier routing",
    "AI-GR-005": "Block live RAG path while feature_ai_copilot=False",
    "AI-GR-006": "Audit-log policy evaluation (honesty trail)",
}

VALID_DATA_CLASSES = ("public", "internal", "pii", "confidential")
VALID_MODEL_TIERS = ("economy", "standard", "full")

_TIER_RANK = {"economy": 0, "standard": 1, "full": 2}


class AiPolicyError(ValueError):
    """Invalid AI policy document or evaluation input."""


@dataclass(frozen=True)
class DataClassRule:
    data_class: str
    max_model_tier: str
    require_pii_scrub: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "data_class": self.data_class,
            "max_model_tier": self.max_model_tier,
            "require_pii_scrub": self.require_pii_scrub,
        }


@dataclass
class AiPolicySet:
    """Tenant AI Policies (Studio) — wraps existing AI-GR-* primitives."""

    id: str
    tenant_id: str
    name: str
    guardrails: dict[str, bool] = field(default_factory=dict)
    data_class_rules: list[DataClassRule] = field(default_factory=list)
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "guardrails": dict(self.guardrails),
            "data_class_rules": [r.as_dict() for r in self.data_class_rules],
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def default_guardrails() -> dict[str, bool]:
    return {gid: True for gid in AI_GUARDRAIL_CATALOG}


def default_data_class_rules() -> list[DataClassRule]:
    return [
        DataClassRule("public", "full", require_pii_scrub=False),
        DataClassRule("internal", "standard", require_pii_scrub=True),
        DataClassRule("pii", "economy", require_pii_scrub=True),
        DataClassRule("confidential", "economy", require_pii_scrub=True),
    ]


def normalize_data_class_rules(
    rows: list[dict[str, Any]] | None,
) -> list[DataClassRule]:
    if not rows:
        return default_data_class_rules()
    out: list[DataClassRule] = []
    seen: set[str] = set()
    for raw in rows:
        dc = str(raw.get("data_class") or "").strip().lower()
        tier = str(raw.get("max_model_tier") or "").strip().lower()
        if dc not in VALID_DATA_CLASSES:
            raise AiPolicyError(f"unknown data_class: {dc}")
        if tier not in VALID_MODEL_TIERS:
            raise AiPolicyError(f"unknown max_model_tier: {tier}")
        if dc in seen:
            raise AiPolicyError(f"duplicate data_class rule: {dc}")
        seen.add(dc)
        scrub = bool(raw.get("require_pii_scrub", True))
        out.append(DataClassRule(dc, tier, require_pii_scrub=scrub))
    return out


def normalize_guardrails(raw: dict[str, Any] | None) -> dict[str, bool]:
    base = default_guardrails()
    if not raw:
        return base
    for key, val in raw.items():
        gid = str(key).strip().upper()
        if gid not in AI_GUARDRAIL_CATALOG:
            raise AiPolicyError(f"unknown guardrail: {gid}")
        base[gid] = bool(val)
    return base


def tier_allowed(requested: str, ceiling: str) -> bool:
    req = (requested or "").strip().lower()
    ceil = (ceiling or "").strip().lower()
    if req not in _TIER_RANK or ceil not in _TIER_RANK:
        return False
    return _TIER_RANK[req] <= _TIER_RANK[ceil]
