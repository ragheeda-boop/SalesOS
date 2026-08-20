"""STORY-12-04 — Per-plan AI model tier entitlements."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import settings
from app.modules.admin.ai_model_tiers import (
    resolve_model_for_entitlements,
)
from app.modules.admin.entitlements import (
    AiModelTierEntitlement,
    PlanEntitlements,
    ai_model_tier_allowed,
    default_entitlements_for_tier,
    ensure_ai_model_tier_from_plan_tier,
    parse_entitlements,
    resolve_ai_model_tier,
)


def test_starter_economy_only() -> None:
    e = default_entitlements_for_tier("starter")
    assert e.ai_model_tier.default == "economy"
    assert e.ai_model_tier.allowed == ["economy"]
    assert ai_model_tier_allowed(e, "economy") is True
    assert ai_model_tier_allowed(e, "full") is False
    assert resolve_ai_model_tier(e, requested="full") == "economy"


def test_enterprise_full_access() -> None:
    e = default_entitlements_for_tier("enterprise")
    assert e.ai_model_tier.default == "full"
    assert set(e.ai_model_tier.allowed) == {"economy", "standard", "full"}
    assert resolve_ai_model_tier(e, requested="economy") == "economy"
    resolved = resolve_model_for_entitlements(e)
    assert resolved.selected_tier == "full"
    assert resolved.model == "gpt-4o"


def test_growth_standard_ceiling() -> None:
    e = default_entitlements_for_tier("growth")
    assert e.ai_model_tier.default == "standard"
    assert "full" not in e.ai_model_tier.allowed
    assert resolve_ai_model_tier(e, requested="full") == "standard"


def test_legacy_json_without_ai_model_tier_backfills_from_plan() -> None:
    raw = {
        "version": 1,
        "domains": {"DOM-001": {"enabled": True}},
        "quotas": {"seats": 5, "ai_tokens_monthly": 10000},
        "deployment_tier": "pooled",
        "support_sla": "community",
    }
    parsed = parse_entitlements(raw)
    # Pydantic factory → economy; ensure upgrades to starter packaging.
    filled = ensure_ai_model_tier_from_plan_tier(parsed, "starter", raw=raw)
    assert filled.ai_model_tier.default == "economy"
    assert filled.ai_model_tier.allowed == ["economy"]
    ent = ensure_ai_model_tier_from_plan_tier(parsed, "enterprise", raw=raw)
    assert ent.ai_model_tier.default == "full"
    assert "full" in ent.ai_model_tier.allowed


def test_explicit_ai_model_tier_preserved() -> None:
    raw = {
        "version": 1,
        "domains": {},
        "quotas": {},
        "ai_model_tier": {"default": "economy", "allowed": ["economy", "standard"]},
    }
    parsed = parse_entitlements(raw)
    kept = ensure_ai_model_tier_from_plan_tier(parsed, "enterprise", raw=raw)
    assert kept.ai_model_tier.default == "economy"
    assert kept.ai_model_tier.allowed == ["economy", "standard"]


def test_default_must_be_in_allowed() -> None:
    with pytest.raises(ValidationError):
        AiModelTierEntitlement(default="full", allowed=["economy"])


def test_copilot_flag_unchanged_false() -> None:
    assert settings.feature_ai_copilot is True


def test_round_trip_dump_includes_ai_model_tier() -> None:
    e = default_entitlements_for_tier("starter")
    dumped = e.model_dump(mode="json")
    assert "ai_model_tier" in dumped
    again = PlanEntitlements.model_validate(dumped)
    assert again.ai_model_tier.default == "economy"
