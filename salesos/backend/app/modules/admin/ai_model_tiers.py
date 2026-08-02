"""STORY-12-04 — AI model tier catalog + entitlement resolve helpers.

Maps Plan.entitlements.ai_model_tier → vendor-shaped model ids.
Does not enable feature_ai_copilot. Not Production GO.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.modules.admin.entitlements import (
    VALID_AI_MODEL_TIERS,
    PlanEntitlements,
    resolve_ai_model_tier,
)

# Catalog is declarative cost ladder — not a live provider call.
AI_MODEL_TIER_CATALOG: dict[str, dict[str, str]] = {
    "economy": {
        "tier": "economy",
        "label": "Economy",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "description": "Smaller/cheaper default for Starter and free plans",
    },
    "standard": {
        "tier": "standard",
        "label": "Standard",
        "provider": "anthropic",
        "model": "claude-3-5-haiku-20241022",
        "description": "Mid-tier default for Growth",
    },
    "full": {
        "tier": "full",
        "label": "Full",
        "provider": "openai",
        "model": "gpt-4o",
        "description": "Full-capability default for Enterprise",
    },
}


@dataclass(frozen=True)
class ResolvedModelTier:
    default_tier: str
    allowed_tiers: list[str]
    selected_tier: str
    provider: str
    model: str
    catalog_entry: dict[str, str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "default_tier": self.default_tier,
            "allowed_tiers": list(self.allowed_tiers),
            "selected_tier": self.selected_tier,
            "provider": self.provider,
            "model": self.model,
            "catalog_entry": dict(self.catalog_entry),
        }


def catalog_list() -> list[dict[str, str]]:
    return [dict(AI_MODEL_TIER_CATALOG[k]) for k in ("economy", "standard", "full")]


def resolve_model_for_entitlements(
    entitlements: PlanEntitlements,
    *,
    requested_tier: str | None = None,
) -> ResolvedModelTier:
    selected = resolve_ai_model_tier(entitlements, requested=requested_tier)
    if selected not in AI_MODEL_TIER_CATALOG:
        selected = "economy"
    entry = AI_MODEL_TIER_CATALOG[selected]
    return ResolvedModelTier(
        default_tier=str(entitlements.ai_model_tier.default),
        allowed_tiers=[str(t) for t in entitlements.ai_model_tier.allowed],
        selected_tier=selected,
        provider=entry["provider"],
        model=entry["model"],
        catalog_entry=entry,
    )


def clamp_requested_tier(tier: str | None) -> str | None:
    if tier is None:
        return None
    key = str(tier).strip().lower()
    if key not in VALID_AI_MODEL_TIERS:
        return None
    return key
