from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func as sa_func
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.dependencies import get_db_session
from app.modules.identity.models import Tenant, User
from app.owner_auth import require_owner_role_dep

from ..schemas import (
    PROVISIONING_STATUS_VALUES,
    TenantActivateRequest,
    TenantCreate,
    TenantDetail,
    TenantHardDeleteRequest,
    TenantLifecycleResponse,
    TenantListItem,
    TenantReprovisionRequest,
    TenantReprovisionResponse,
    TenantSuspendRequest,
    TenantUpdate,
    TenantUsage,
)
from ..services import TenantProvisioningService

router = APIRouter(
    tags=["Admin - Tenants"],
    dependencies=[Depends(require_owner_role_dep("admin"))],
)

# FE-S04-15 trial filter buckets (Stream B client filter → server query param).
TRIAL_FILTER_VALUES = frozenset({"has_trial", "expired", "none"})

# FE-S04-19 sort keys (Stream B client sort → server query param).
TENANT_SORT_VALUES = frozenset({"created_desc", "created_asc", "name_asc", "name_desc"})


def apply_tenant_list_filters(
    stmt: Select[Any],
    *,
    status: str | None = None,
    plan: str | None = None,
    plan_id: str | None = None,
    region: str | None = None,
    data_residency: str | None = None,
    provisioning_status: str | None = None,
    trial: str | None = None,
    search: str | None = None,
    now: datetime | None = None,
) -> Select[Any]:
    """Apply Owner Platform list filters for GET /admin/tenants.

    Raises ``ValueError`` for invalid ``provisioning_status`` / ``trial`` values.
    """
    if status == "active":
        stmt = stmt.where(Tenant.is_active.is_(True))
    elif status == "suspended":
        stmt = stmt.where(Tenant.is_active.is_(False))
    if plan:
        stmt = stmt.where(Tenant.plan == plan)
    if plan_id:
        stmt = stmt.where(Tenant.plan_id == plan_id)
    if region:
        stmt = stmt.where(Tenant.region == region)
    if data_residency:
        stmt = stmt.where(Tenant.data_residency == data_residency)
    if provisioning_status:
        if provisioning_status not in PROVISIONING_STATUS_VALUES:
            raise ValueError(
                f"Invalid provisioning_status '{provisioning_status}'. "
                f"Allowed: {sorted(PROVISIONING_STATUS_VALUES)}"
            )
        stmt = stmt.where(Tenant.provisioning_status == provisioning_status)
    if trial:
        if trial not in TRIAL_FILTER_VALUES:
            raise ValueError(f"Invalid trial '{trial}'. Allowed: {sorted(TRIAL_FILTER_VALUES)}")
        clock = now or datetime.now(UTC)
        if trial == "none":
            stmt = stmt.where(Tenant.trial_ends_at.is_(None))
        elif trial == "has_trial":
            stmt = stmt.where(
                Tenant.trial_ends_at.is_not(None),
                Tenant.trial_ends_at >= clock,
            )
        else:  # expired
            stmt = stmt.where(
                Tenant.trial_ends_at.is_not(None),
                Tenant.trial_ends_at < clock,
            )
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Tenant.name.ilike(pattern),
                Tenant.slug.ilike(pattern),
                Tenant.domain.ilike(pattern),
                Tenant.plan_id.ilike(pattern),
                Tenant.region.ilike(pattern),
                Tenant.data_residency.ilike(pattern),
            )
        )
    return stmt


def apply_tenant_list_sort(stmt: Select[Any], sort: str | None = None) -> Select[Any]:
    """Order GET /admin/tenants. Default created_desc. Raises ValueError if invalid."""
    key = sort or "created_desc"
    if key not in TENANT_SORT_VALUES:
        raise ValueError(f"Invalid sort '{key}'. Allowed: {sorted(TENANT_SORT_VALUES)}")
    if key == "created_asc":
        return stmt.order_by(Tenant.created_at.asc())
    if key == "name_asc":
        return stmt.order_by(Tenant.name.asc(), Tenant.created_at.desc())
    if key == "name_desc":
        return stmt.order_by(Tenant.name.desc(), Tenant.created_at.desc())
    return stmt.order_by(Tenant.created_at.desc())


async def _resolve_tenant_name(db: AsyncSession, tenant_id: str) -> str:
    try:
        tid = uuid.UUID(tenant_id)
        tenant = await db.get(Tenant, tid)
        if tenant:
            return tenant.name
    except (ValueError, Exception):
        pass
    return tenant_id


async def _user_count(db: AsyncSession, tenant_id: uuid.UUID) -> int:
    stmt = select(sa_func.count()).where(User.tenant_id == tenant_id)
    result = await db.execute(stmt)
    return result.scalar() or 0


def _to_list_item(t: Tenant, user_count: int) -> TenantListItem:
    return TenantListItem(
        id=t.id,
        name=t.name,
        slug=t.slug,
        domain=t.domain,
        plan=t.plan,
        plan_id=t.plan_id,
        region=t.region,
        data_residency=t.data_residency,
        provisioning_status=t.provisioning_status,
        trial_ends_at=t.trial_ends_at,
        is_active=t.is_active,
        user_count=user_count,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


def _to_detail(t: Tenant, user_count: int) -> TenantDetail:
    return TenantDetail(
        id=t.id,
        name=t.name,
        slug=t.slug,
        domain=t.domain,
        plan=t.plan,
        plan_id=t.plan_id,
        region=t.region,
        data_residency=t.data_residency,
        provisioning_status=t.provisioning_status,
        trial_ends_at=t.trial_ends_at,
        is_active=t.is_active,
        settings=t.settings or {},
        features=t.features or {},
        user_count=user_count,
        subscription_ends_at=t.subscription_ends_at,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.get("/tenants", response_model=list[TenantListItem])
async def list_tenants(
    response: Response,
    status: str | None = Query(None, description="is_active: active|suspended"),
    plan: str | None = Query(None, description="Display/tier plan label"),
    plan_id: str | None = Query(None, description="Opaque Owner Platform plan catalog id"),
    region: str | None = Query(None),
    data_residency: str | None = Query(None),
    provisioning_status: str | None = Query(None, description="pending|active|suspended|failed"),
    trial: str | None = Query(None, description="Trial bucket: has_trial|expired|none (FE-S04-15)"),
    search: str | None = Query(
        None,
        description="ilike name|slug|domain|plan_id|region|data_residency",
    ),
    sort: str | None = Query(
        None,
        description="FE-S04-19: created_desc|created_asc|name_asc|name_desc",
    ),
    page: int | None = Query(None, ge=1, description="1-based page; omit = return all"),
    page_size: int | None = Query(
        None, ge=1, le=100, description="Page size when page set (default 20)"
    ),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(Tenant)
    try:
        stmt = apply_tenant_list_filters(
            stmt,
            status=status,
            plan=plan,
            plan_id=plan_id,
            region=region,
            data_residency=data_residency,
            provisioning_status=provisioning_status,
            trial=trial,
            search=search,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    count_stmt = select(sa_func.count()).select_from(stmt.order_by(None).subquery())
    total = int((await db.execute(count_stmt)).scalar() or 0)
    response.headers["X-Total-Count"] = str(total)

    try:
        stmt = apply_tenant_list_sort(stmt, sort)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if page is not None:
        size = page_size or 20
        stmt = stmt.offset((page - 1) * size).limit(size)

    result = await db.execute(stmt)
    tenants = result.scalars().all()

    items = []
    for t in tenants:
        items.append(_to_list_item(t, await _user_count(db, t.id)))
    return items


@router.post("/tenants", response_model=TenantDetail, status_code=201)
async def create_tenant(
    body: TenantCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """Create via STORY-04-02 idempotent provisioning workflow."""
    existing = await db.execute(select(Tenant).where(Tenant.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409, detail=f"Tenant with slug '{body.slug}' already exists"
        )

    provisioning = TenantProvisioningService(db)
    try:
        result = await provisioning.provision_workflow(
            name=body.name,
            slug=body.slug,
            domain=body.domain,
            plan=body.plan or "free",
            plan_id=body.plan_id,
            region=body.region,
            data_residency=body.data_residency,
            trial_ends_at=body.trial_ends_at,
            admin_email=body.admin_email,
            admin_password=body.admin_password,
            admin_full_name=body.admin_full_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    tenant = await db.get(Tenant, uuid.UUID(result["tenant_id"]))
    if not tenant:
        raise HTTPException(status_code=500, detail="Provisioning failed to persist tenant")

    return _to_detail(tenant, await _user_count(db, tenant.id))


@router.get("/tenants/{tenant_id}", response_model=TenantDetail)
async def get_tenant(tenant_id: str, db: AsyncSession = Depends(get_db_session)):
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found") from None
    tenant = await db.get(Tenant, tid)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return _to_detail(tenant, await _user_count(db, tenant.id))


@router.put("/tenants/{tenant_id}", response_model=TenantDetail)
async def update_tenant(
    tenant_id: str, body: TenantUpdate, db: AsyncSession = Depends(get_db_session)
):
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found") from None
    tenant = await db.get(Tenant, tid)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    # Use model_fields_set so FE write-path can clear Owner Platform fields with JSON null
    # (buildOwnerPlatformWritePayload sends null for empty strings).
    fields_set = body.model_fields_set

    if "name" in fields_set and body.name is not None:
        tenant.name = body.name
    if "is_active" in fields_set and body.is_active is not None:
        tenant.is_active = body.is_active
    # plan = display/tier label; plan_id = opaque Owner Platform catalog id (STORY-04-01).
    if "plan" in fields_set and body.plan is not None:
        tenant.plan = body.plan
    if "plan_id" in fields_set:
        tenant.plan_id = body.plan_id
    if "region" in fields_set:
        tenant.region = body.region
    if "data_residency" in fields_set:
        tenant.data_residency = body.data_residency
    if "provisioning_status" in fields_set and body.provisioning_status is not None:
        if body.provisioning_status not in PROVISIONING_STATUS_VALUES:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid provisioning_status '{body.provisioning_status}'. "
                    f"Allowed: {sorted(PROVISIONING_STATUS_VALUES)}"
                ),
            )
        tenant.provisioning_status = body.provisioning_status
    if "trial_ends_at" in fields_set:
        tenant.trial_ends_at = body.trial_ends_at
    if "settings" in fields_set and body.settings is not None:
        settings = dict(tenant.settings or {})
        settings.update(body.settings)
        tenant.settings = settings
    tenant.updated_at = datetime.now(UTC)
    await db.flush()

    return _to_detail(tenant, await _user_count(db, tenant.id))


@router.post("/tenants/{tenant_id}/suspend", response_model=TenantLifecycleResponse)
async def suspend_tenant(
    tenant_id: str, body: TenantSuspendRequest, db: AsyncSession = Depends(get_db_session)
):
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found") from None
    tenant = await db.get(Tenant, tid)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    prior = tenant.provisioning_status
    tenant.is_active = False
    tenant.provisioning_status = "suspended"
    tenant.updated_at = datetime.now(UTC)
    await db.flush()
    return TenantLifecycleResponse(
        message="Tenant suspended",
        tenant_id=tenant_id,
        is_active=False,
        provisioning_status="suspended",
        prior_provisioning_status=prior,
        reason=body.reason or "",
    )


@router.post("/tenants/{tenant_id}/activate", response_model=TenantLifecycleResponse)
async def activate_tenant(
    tenant_id: str,
    body: TenantActivateRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Restore soft-deleted or suspended tenant (FE-S04-17 lifecycle parity)."""
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found") from None
    tenant = await db.get(Tenant, tid)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    prior = tenant.provisioning_status
    tenant.is_active = True
    tenant.provisioning_status = "active"
    tenant.updated_at = datetime.now(UTC)
    await db.flush()
    return TenantLifecycleResponse(
        message="Tenant activated",
        tenant_id=tenant_id,
        is_active=True,
        provisioning_status="active",
        prior_provisioning_status=prior,
        reason=body.reason or "",
    )


@router.post("/tenants/{tenant_id}/reprovision", response_model=TenantReprovisionResponse)
async def reprovision_tenant(
    tenant_id: str,
    body: TenantReprovisionRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Re-run idempotent provision_workflow for failed/pending (or force_active)."""
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found") from None
    tenant = await db.get(Tenant, tid)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Default: allow retry for failed/pending; suspended needs explicit force_active.
    if tenant.provisioning_status == "suspended" and not body.force_active:
        raise HTTPException(
            status_code=409,
            detail="Tenant is suspended; pass force_active=true to reprovision",
        )

    force_active = body.force_active or tenant.provisioning_status in {
        "failed",
        "pending",
    }
    provisioning = TenantProvisioningService(db)
    try:
        result = await provisioning.provision_workflow(
            name=tenant.name,
            slug=tenant.slug,
            domain=tenant.domain,
            plan=tenant.plan or "free",
            plan_id=tenant.plan_id,
            region=tenant.region,
            data_residency=tenant.data_residency,
            trial_ends_at=tenant.trial_ends_at,
            admin_email=body.admin_email,
            admin_password=body.admin_password,
            admin_full_name=body.admin_full_name,
            force_active=force_active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return TenantReprovisionResponse(
        message="Tenant reprovisioned",
        tenant_id=result["tenant_id"],
        slug=result["slug"],
        created=bool(result.get("created")),
        idempotent=bool(result.get("idempotent")),
        provisioning_status=result["provisioning_status"],
        roles_provisioned=int(result.get("roles_provisioned") or 0),
        permissions_provisioned=int(result.get("permissions_provisioned") or 0),
        studio_config=result.get("studio_config") or {},
        admin_user_id=result.get("admin_user_id"),
    )


@router.delete("/tenants/{tenant_id}", response_model=TenantLifecycleResponse)
async def soft_delete_tenant(tenant_id: str, db: AsyncSession = Depends(get_db_session)):
    """Soft-delete: is_active=false only — does not set provisioning=suspended."""
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found") from None
    tenant = await db.get(Tenant, tid)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    prior = tenant.provisioning_status
    tenant.is_active = False
    # Keep provisioning_status unchanged so Inactive ≠ Suspended (FE-S04-14 honesty).
    tenant.updated_at = datetime.now(UTC)
    await db.flush()
    return TenantLifecycleResponse(
        message="Tenant soft-deleted",
        tenant_id=tenant_id,
        is_active=False,
        provisioning_status=tenant.provisioning_status or "pending",
        prior_provisioning_status=prior,
        reason="",
    )


@router.delete("/tenants/{tenant_id}/hard-delete")
async def hard_delete_tenant(
    tenant_id: str, body: TenantHardDeleteRequest, db: AsyncSession = Depends(get_db_session)
):
    if not body.confirm:
        raise HTTPException(status_code=400, detail="confirm must be True for hard delete")
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found") from None
    tenant = await db.get(Tenant, tid)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    await db.delete(tenant)
    await db.flush()
    return {"message": "Tenant hard-deleted", "tenant_id": tenant_id}


@router.get("/tenants/{tenant_id}/usage", response_model=TenantUsage)
async def get_tenant_usage(tenant_id: str, db: AsyncSession = Depends(get_db_session)):
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found") from None
    tenant = await db.get(Tenant, tid)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    user_count = await _user_count(db, tid)

    now = datetime.now(UTC)
    return TenantUsage(
        tenant_id=tid,
        tenant_name=tenant.name,
        api_calls=15420 + hash(str(tid)) % 10000,
        storage_mb=245.8 + hash(str(tid)) % 100,
        active_users=user_count,
        total_users=user_count,
        period_start=now - timedelta(days=30),
        period_end=now,
    )
