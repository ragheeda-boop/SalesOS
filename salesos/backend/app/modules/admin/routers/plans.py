from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.modules.admin.entitlement_cache import invalidate_all_entitlement_caches
from app.modules.admin.entitlements import (
    default_entitlements_for_tier,
    entitlements_to_dict,
    parse_entitlements,
)
from app.modules.identity.models import Tenant
from app.owner_auth import require_owner_role_dep

from ..db_models import LicenseModel, PlanModel
from ..schemas import (
    LicenseCreate,
    LicenseResponse,
    PlanCreate,
    PlanResponse,
    PlanTier,
    PlanUpdate,
)
from ._dependencies import AdminRepositories, get_admin_repos

router = APIRouter(
    tags=["Admin - Plans & Licenses"],
    dependencies=[Depends(require_owner_role_dep("admin"))],
)


async def _resolve_tenant_name(db: AsyncSession, tenant_id: str) -> str:
    try:
        tid = uuid.UUID(tenant_id)
        tenant = await db.get(Tenant, tid)
        if tenant:
            return tenant.name
    except (ValueError, Exception):
        pass
    return tenant_id


# ─── Plans ────────────────────────────────────────────────────────


def _plan_response(p: PlanModel) -> PlanResponse:
    raw_ents = getattr(p, "entitlements", None) or {}
    try:
        ents = parse_entitlements(raw_ents)
    except (ValueError, TypeError, ValidationError):
        ents = default_entitlements_for_tier(getattr(p, "tier", "free"))
    return PlanResponse(
        id=p.id,
        name=p.name,
        tier=PlanTier(p.tier),
        price_monthly=p.price_monthly,
        price_yearly=p.price_yearly,
        max_users=p.max_users,
        max_storage_mb=p.max_storage_mb,
        max_api_calls=p.max_api_calls,
        features=p.features or [],
        is_active=p.is_active,
        stripe_price_id_monthly=getattr(p, "stripe_price_id_monthly", None),
        stripe_price_id_yearly=getattr(p, "stripe_price_id_yearly", None),
        entitlements=ents,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(repos: AdminRepositories = Depends(get_admin_repos)):
    plans = await repos.plans.list()
    return [_plan_response(p) for p in plans]


@router.post("/plans", response_model=PlanResponse, status_code=201)
async def create_plan(body: PlanCreate, repos: AdminRepositories = Depends(get_admin_repos)):
    if body.entitlements is None:
        ents_doc = default_entitlements_for_tier(body.tier.value)
    else:
        ents_doc = parse_entitlements(body.entitlements)
    plan = PlanModel(
        id=uuid.uuid4(),
        name=body.name,
        tier=body.tier.value,
        price_monthly=body.price_monthly,
        price_yearly=body.price_yearly,
        max_users=body.max_users,
        max_storage_mb=body.max_storage_mb,
        max_api_calls=body.max_api_calls,
        features=body.features,
        stripe_price_id_monthly=body.stripe_price_id_monthly,
        stripe_price_id_yearly=body.stripe_price_id_yearly,
        entitlements=entitlements_to_dict(ents_doc),
    )
    created = await repos.plans.create(plan)
    return _plan_response(created)


@router.put("/plans/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: uuid.UUID, body: PlanUpdate, repos: AdminRepositories = Depends(get_admin_repos)
):
    data = body.model_dump(exclude_none=True)
    ents_changed = "entitlements" in data and data["entitlements"] is not None
    if ents_changed:
        data["entitlements"] = entitlements_to_dict(parse_entitlements(data["entitlements"]))
    plan = await repos.plans.update(plan_id, data)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if ents_changed or "tier" in data:
        await invalidate_all_entitlement_caches()
    return _plan_response(plan)


# ─── Licenses ─────────────────────────────────────────────────────


@router.get("/licenses", response_model=list[LicenseResponse])
async def list_licenses(
    repos: AdminRepositories = Depends(get_admin_repos),
    db: AsyncSession = Depends(get_db_session),
):
    licenses = await repos.licenses.list()
    result = []
    for lic in licenses:
        plan = await repos.plans.get(lic.plan_id)
        tenant_name = await _resolve_tenant_name(db, str(lic.tenant_id))
        result.append(
            LicenseResponse(
                id=lic.id,
                tenant_id=lic.tenant_id,
                tenant_name=tenant_name,
                plan_id=lic.plan_id,
                plan_name=plan.name if plan else "Unknown",
                tier=PlanTier(plan.tier) if plan else PlanTier.FREE,
                is_active=lic.is_active,
                starts_at=lic.starts_at,
                ends_at=lic.ends_at,
                created_at=lic.created_at,
                updated_at=lic.updated_at,
            )
        )
    return result


@router.post("/licenses", response_model=LicenseResponse, status_code=201)
async def create_license(
    body: LicenseCreate,
    repos: AdminRepositories = Depends(get_admin_repos),
    db: AsyncSession = Depends(get_db_session),
):
    now = datetime.now(UTC)
    lic = LicenseModel(
        id=uuid.uuid4(),
        tenant_id=body.tenant_id,
        plan_id=body.plan_id,
        starts_at=body.starts_at or now,
        ends_at=body.ends_at,
    )
    created = await repos.licenses.create(lic)
    plan = await repos.plans.get(created.plan_id)
    tenant_name = await _resolve_tenant_name(db, str(created.tenant_id))
    return LicenseResponse(
        id=created.id,
        tenant_id=created.tenant_id,
        tenant_name=tenant_name,
        plan_id=created.plan_id,
        plan_name=plan.name if plan else "Unknown",
        tier=PlanTier(plan.tier) if plan else PlanTier.FREE,
        is_active=created.is_active,
        starts_at=created.starts_at,
        ends_at=created.ends_at,
        created_at=created.created_at,
        updated_at=created.updated_at,
    )
