"""STORY-06-02 — Resolve Plan.entitlements for a tenant (read-only).

Uses short-TTL entitlement cache (<=60s). Does not call DEC-085 set_config.
Does not invent Stripe secrets.
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.db_models import PlanModel
from app.modules.admin.entitlement_cache import get_entitlement_cache
from app.modules.admin.entitlements import (
    PlanEntitlements,
    default_entitlements_for_tier,
    ensure_ai_model_tier_from_plan_tier,
    parse_entitlements,
)
from app.modules.billing.models import SubscriptionModel
from app.modules.identity.tenant_lifecycle_guard import fetch_tenant_by_id


async def _plan_by_id_or_tier(db: AsyncSession, plan_ref: str | None) -> PlanModel | None:
    if not plan_ref:
        return None
    try:
        pid = uuid.UUID(str(plan_ref))
    except ValueError:
        pid = None
    if pid is not None:
        plan = await db.get(PlanModel, pid)
        if plan is not None:
            return plan
    result = await db.execute(select(PlanModel).where(PlanModel.tier == str(plan_ref)).limit(1))
    return result.scalar_one_or_none()


async def _resolve_entitlements_from_db(
    db: AsyncSession,
    tenant_id: str | uuid.UUID,
) -> tuple[PlanEntitlements, dict[str, Any]]:
    tenant = await fetch_tenant_by_id(db, str(tenant_id))
    plan_ref: str | None = None
    tier_hint = "free"
    if tenant is not None:
        plan_ref = tenant.plan_id or None
        if getattr(tenant, "plan", None):
            tier_hint = str(tenant.plan).strip().lower() or tier_hint

    if plan_ref is None:
        try:
            tid = uuid.UUID(str(tenant_id))
        except ValueError:
            tid = None
        if tid is not None:
            sub = (
                await db.execute(
                    select(SubscriptionModel).where(SubscriptionModel.tenant_id == tid)
                )
            ).scalar_one_or_none()
            if sub is not None and sub.plan_id:
                plan_ref = sub.plan_id

    plan = await _plan_by_id_or_tier(db, plan_ref)
    if plan is not None:
        tier_hint = str(plan.tier or tier_hint).lower()
        raw = plan.entitlements if isinstance(plan.entitlements, dict) else {}
        try:
            ents = parse_entitlements(raw or {})
        except (ValueError, TypeError, ValidationError):
            ents = default_entitlements_for_tier(tier_hint)
        else:
            ents = ensure_ai_model_tier_from_plan_tier(ents, tier_hint, raw=raw or {})
        return ents, {
            "plan_id": str(plan.id),
            "tier": plan.tier,
            "source": "admin_plans",
        }

    return default_entitlements_for_tier(tier_hint), {
        "plan_id": plan_ref,
        "tier": tier_hint,
        "source": "tier_default",
    }


async def resolve_entitlements_for_tenant(
    db: AsyncSession,
    tenant_id: str | uuid.UUID,
    *,
    skip_cache: bool = False,
) -> tuple[PlanEntitlements, dict[str, Any]]:
    """Return (entitlements, meta) for enforcement decisions."""
    tid = str(tenant_id)
    cache = get_entitlement_cache()
    if not skip_cache:
        hit = await cache.get(tid)
        if hit is not None:
            return hit

    ents, meta = await _resolve_entitlements_from_db(db, tid)
    meta = {**meta, "cache": "miss"}
    await cache.set(tid, ents, meta)
    return ents, meta
