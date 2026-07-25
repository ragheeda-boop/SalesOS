from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session, require_role_dep
from app.modules.identity.models import Tenant

from ..db_models import LicenseModel, PlanModel
from ..schemas import (
    LicenseCreate,
    LicenseResponse,
    PlanCreate,
    PlanResponse,
    PlanUpdate,
)
from ._dependencies import AdminRepositories, get_admin_repos

router = APIRouter(
    tags=["Admin - Plans & Licenses"],
    dependencies=[Depends(require_role_dep("admin"))],
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


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(repos: AdminRepositories = Depends(get_admin_repos)):
    plans = await repos.plans.list()
    return [PlanResponse(
        id=p.id, name=p.name, tier=p.tier,
        price_monthly=p.price_monthly, price_yearly=p.price_yearly,
        max_users=p.max_users, max_storage_mb=p.max_storage_mb,
        max_api_calls=p.max_api_calls, features=p.features,
        is_active=p.is_active, created_at=p.created_at, updated_at=p.updated_at,
    ) for p in plans]


@router.post("/plans", response_model=PlanResponse, status_code=201)
async def create_plan(body: PlanCreate, repos: AdminRepositories = Depends(get_admin_repos)):
    plan = PlanModel(id=uuid.uuid4(), name=body.name, tier=body.tier.value,
                     price_monthly=body.price_monthly, price_yearly=body.price_yearly,
                     max_users=body.max_users, max_storage_mb=body.max_storage_mb,
                     max_api_calls=body.max_api_calls, features=body.features)
    created = await repos.plans.create(plan)
    return PlanResponse(
        id=created.id, name=created.name, tier=created.tier,
        price_monthly=created.price_monthly, price_yearly=created.price_yearly,
        max_users=created.max_users, max_storage_mb=created.max_storage_mb,
        max_api_calls=created.max_api_calls, features=created.features,
        is_active=created.is_active, created_at=created.created_at, updated_at=created.updated_at,
    )


@router.put("/plans/{plan_id}", response_model=PlanResponse)
async def update_plan(plan_id: uuid.UUID, body: PlanUpdate, repos: AdminRepositories = Depends(get_admin_repos)):
    data = body.model_dump(exclude_none=True)
    plan = await repos.plans.update(plan_id, data)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return PlanResponse(
        id=plan.id, name=plan.name, tier=plan.tier,
        price_monthly=plan.price_monthly, price_yearly=plan.price_yearly,
        max_users=plan.max_users, max_storage_mb=plan.max_storage_mb,
        max_api_calls=plan.max_api_calls, features=plan.features,
        is_active=plan.is_active, created_at=plan.created_at, updated_at=plan.updated_at,
    )


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
        result.append(LicenseResponse(
            id=lic.id, tenant_id=lic.tenant_id,
            tenant_name=tenant_name,
            plan_id=lic.plan_id, plan_name=plan.name if plan else "Unknown",
            tier=plan.tier if plan else "free",
            is_active=lic.is_active, starts_at=lic.starts_at, ends_at=lic.ends_at,
            created_at=lic.created_at, updated_at=lic.updated_at,
        ))
    return result


@router.post("/licenses", response_model=LicenseResponse, status_code=201)
async def create_license(
    body: LicenseCreate,
    repos: AdminRepositories = Depends(get_admin_repos),
    db: AsyncSession = Depends(get_db_session),
):
    now = datetime.now(timezone.utc)
    lic = LicenseModel(
        id=uuid.uuid4(), tenant_id=body.tenant_id, plan_id=body.plan_id,
        starts_at=body.starts_at or now,
        ends_at=body.ends_at,
    )
    created = await repos.licenses.create(lic)
    plan = await repos.plans.get(created.plan_id)
    tenant_name = await _resolve_tenant_name(db, str(created.tenant_id))
    return LicenseResponse(
        id=created.id, tenant_id=created.tenant_id,
        tenant_name=tenant_name,
        plan_id=created.plan_id, plan_name=plan.name if plan else "Unknown",
        tier=plan.tier if plan else "free",
        is_active=created.is_active, starts_at=created.starts_at, ends_at=created.ends_at,
        created_at=created.created_at, updated_at=created.updated_at,
    )
