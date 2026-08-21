"""STORY-12-04 — Per-plan AI model tier HTTP (entitlement surface).

Read-only catalog + tenant resolve from Plan.entitlements.
Gated by settings.feature_ai_copilot. Phase 3 HITL gates closed 2026-08-19.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_tenant_id, verify_token
from app.modules.admin.ai_model_tiers import (
    catalog_list,
    clamp_requested_tier,
    resolve_model_for_entitlements,
)
from app.modules.admin.entitlement_resolver import resolve_entitlements_for_tenant
from app.modules.admin.entitlements import default_entitlements_for_tier

router = APIRouter(prefix="/studio/ai-model-tiers", tags=["AI Model Tiers"])
_AUTH = [Depends(verify_token)]


class ModelTierResolveResponse(BaseModel):
    feature_ai_copilot: bool = False  # overridden at runtime by settings
    plan_tier: str = ""
    source: str = ""
    default_tier: str
    allowed_tiers: list[str] = Field(default_factory=list)
    selected_tier: str
    provider: str
    model: str
    catalog: list[dict[str, str]] = Field(default_factory=list)
    honesty: str = (
        "Entitlement defaults only; product AI gated by settings.feature_ai_copilot. "
        "Phase 3 HITL/evaluation gates closed 2026-08-19."
    )


@router.get("/catalog", dependencies=_AUTH)
async def get_model_tier_catalog() -> dict[str, Any]:
    """Static commercial ladder (economy → full)."""
    return {
        "catalog": catalog_list(),
        "feature_ai_copilot": bool(settings.feature_ai_copilot),
        "honesty": "Catalog only — does not enable live LLM routing.",
    }


@router.get("/defaults", dependencies=_AUTH)
async def get_model_tier_defaults_by_plan(
    plan_tier: str = Query("starter", min_length=1, max_length=32),
) -> dict[str, Any]:
    """Commercial packaging defaults by plan tier (no DB)."""
    ents = default_entitlements_for_tier(plan_tier)
    resolved = resolve_model_for_entitlements(ents)
    return {
        "plan_tier": str(plan_tier).strip().lower(),
        "ai_model_tier": ents.ai_model_tier.model_dump(mode="json"),
        "resolved": resolved.as_dict(),
        "feature_ai_copilot": bool(settings.feature_ai_copilot),
    }


@router.get("", response_model=ModelTierResolveResponse, dependencies=_AUTH)
async def resolve_tenant_model_tiers(
    requested_tier: str | None = Query(None, max_length=32),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> ModelTierResolveResponse:
    """Resolve this tenant's Plan.entitlements AI model tier."""
    ents, meta = await resolve_entitlements_for_tenant(db, tenant_id)
    plan_tier = str(meta.get("tier") or "free")
    req = clamp_requested_tier(requested_tier)
    resolved = resolve_model_for_entitlements(ents, requested_tier=req)
    return ModelTierResolveResponse(
        feature_ai_copilot=bool(settings.feature_ai_copilot),
        plan_tier=plan_tier,
        source=str(meta.get("source") or ""),
        default_tier=resolved.default_tier,
        allowed_tiers=resolved.allowed_tiers,
        selected_tier=resolved.selected_tier,
        provider=resolved.provider,
        model=resolved.model,
        catalog=catalog_list(),
    )
