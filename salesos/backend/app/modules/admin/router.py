from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session, require_role_dep

from .db_models import FeatureFlagModel, LicenseModel, PlanModel

from .pg_repositories import (
    PostgresAICostRepository,
    PostgresFeatureFlagRepository,
    PostgresHealthRepository,
    PostgresInvoiceRepository,
    PostgresJobRepository,
    PostgresLicenseRepository,
    PostgresPlanRepository,
)
from .schemas import (
    AICostResponse,
    AICostSummary,
    AIUsageResponse,
    DetailedHealthResponse,
    FeatureFlagCreate,
    FeatureFlagResponse,
    FeatureFlagTenantResponse,
    FeatureFlagUpdate,
    HealthComponentStatus,
    HealthHistoryEntry,
    InvoiceResponse,
    JobDetailResponse,
    JobResponse,
    LicenseCreate,
    LicenseResponse,
    PlanCreate,
    PlanResponse,
    PlanUpdate,
    TenantCreate,
    TenantDetail,
    TenantListItem,
    TenantUpdate,
    TenantUsage,
    TransactionResponse,
    UserAdminDetail,
    UserAdminListItem,
    UserAdminUpdate,
)

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"],
    dependencies=[Depends(require_role_dep("admin"))],
)


class AdminRepositories:
    def __init__(self, db: AsyncSession):
        self.plans = PostgresPlanRepository(db)
        self.licenses = PostgresLicenseRepository(db)
        self.invoices = PostgresInvoiceRepository(db)
        self.flags = PostgresFeatureFlagRepository(db)
        self.jobs = PostgresJobRepository(db)
        self.ai = PostgresAICostRepository(db)
        self.health = PostgresHealthRepository(db)


async def get_admin_repos(db: AsyncSession = Depends(get_db_session)) -> AdminRepositories:
    return AdminRepositories(db)


# ─── Internal state ──────────────────────────────────────────────

_tenants_store: dict[str, dict] = {}
_users_store: list[dict] = []
_seed_done = False
_users_seeded = False
_TENANT_UUIDS: dict[str, str] = {}


def _td(**kwargs):
    return timedelta(**kwargs)


def _seed_state():
    global _seed_done
    if _seed_done:
        return
    _seed_done = True
    now = datetime.now(timezone.utc)

    _TENANT_UUIDS.update({
        "techpro": str(uuid.uuid4()),
        "digitalinno": str(uuid.uuid4()),
        "modernbuild": str(uuid.uuid4()),
        "integrated": str(uuid.uuid4()),
        "futureskills": str(uuid.uuid4()),
    })

    tenants_data = {
        _TENANT_UUIDS["techpro"]: {
            "name": "شركة التقنية المتطورة", "slug": "tech-pro",
            "domain": "techpro.salesos.io", "plan": "growth",
            "is_active": True, "settings": {"timezone": "Asia/Riyadh", "lang": "ar"},
            "features": {"ai_copilot": True, "advanced_search": True},
            "user_count": 18, "subscription_ends_at": None,
            "created_at": now - _td(days=120), "updated_at": now - _td(days=2),
        },
        _TENANT_UUIDS["digitalinno"]: {
            "name": "مؤسسة الابتكار الرقمي", "slug": "digital-inno",
            "domain": "digitalinno.salesos.io", "plan": "starter",
            "is_active": True, "settings": {"timezone": "Asia/Riyadh", "lang": "ar"},
            "features": {"ai_copilot": False},
            "user_count": 4, "subscription_ends_at": None,
            "created_at": now - _td(days=200), "updated_at": now - _td(days=10),
        },
        _TENANT_UUIDS["modernbuild"]: {
            "name": "مجموعة البناء الحديث", "slug": "modern-build",
            "domain": "modernbuild.salesos.io", "plan": "enterprise",
            "is_active": True, "settings": {"timezone": "Asia/Riyadh", "lang": "ar"},
            "features": {"ai_copilot": True, "sso_enabled": True, "workflow_automation": True},
            "user_count": 42, "subscription_ends_at": now + _td(days=180),
            "created_at": now - _td(days=365), "updated_at": now - _td(days=1),
        },
        _TENANT_UUIDS["integrated"]: {
            "name": "شركة الحلول المتكاملة", "slug": "integrated-sol",
            "domain": "integrated.salesos.io", "plan": "free",
            "is_active": False, "settings": {"timezone": "Asia/Riyadh", "lang": "en"},
            "features": {},
            "user_count": 1, "subscription_ends_at": now - _td(days=30),
            "created_at": now - _td(days=400), "updated_at": now - _td(days=30),
        },
        _TENANT_UUIDS["futureskills"]: {
            "name": "أكاديمية المهارات المستقبلية", "slug": "future-skills",
            "domain": "futureskills.salesos.io", "plan": "growth",
            "is_active": True, "settings": {"timezone": "Asia/Riyadh", "lang": "ar"},
            "features": {"ai_copilot": True, "crm_kanban": True},
            "user_count": 22, "subscription_ends_at": None,
            "created_at": now - _td(days=60), "updated_at": now - _td(days=5),
        },
    }

    for tid, tdata in tenants_data.items():
        _tenants_store[tid] = {"id": tid, **tdata}

    _seed_users(now)


def _seed_users(now: datetime):
    global _users_seeded
    if _users_seeded:
        return
    _users_seeded = True
    tp = _TENANT_UUIDS["techpro"]
    di = _TENANT_UUIDS["digitalinno"]
    mb = _TENANT_UUIDS["modernbuild"]
    it = _TENANT_UUIDS["integrated"]
    fs = _TENANT_UUIDS["futureskills"]

    _users_store.extend([
        {"id": str(uuid.uuid4()), "email": "admin@techpro.sa", "full_name": "أحمد القحطاني", "full_name_ar": "أحمد القحطاني",
         "role": "admin", "is_active": True, "is_verified": True, "tenant_id": tp, "tenant_name": "شركة التقنية المتطورة",
         "permissions": ["admin", "manage_users", "manage_billing"], "created_at": now - _td(days=120), "updated_at": now - _td(days=2), "last_login_at": now - _td(hours=2)},
        {"id": str(uuid.uuid4()), "email": "manager@techpro.sa", "full_name": "سارة الدوسري", "full_name_ar": "سارة الدوسري",
         "role": "manager", "is_active": True, "is_verified": True, "tenant_id": tp, "tenant_name": "شركة التقنية المتطورة",
         "permissions": ["read_companies", "read_contacts", "manage_opportunities"], "created_at": now - _td(days=100), "updated_at": now - _td(days=5), "last_login_at": now - _td(days=1)},
        {"id": str(uuid.uuid4()), "email": "user@digitalinno.sa", "full_name": "Fahad Al-Otaibi", "full_name_ar": "فهد العتيبي",
         "role": "user", "is_active": True, "is_verified": True, "tenant_id": di, "tenant_name": "مؤسسة الابتكار الرقمي",
         "permissions": ["read_companies"], "created_at": now - _td(days=180), "updated_at": now - _td(days=10), "last_login_at": now - _td(days=7)},
        {"id": str(uuid.uuid4()), "email": "inactive@old.sa", "full_name": "قديم", "full_name_ar": "قديم",
         "role": "user", "is_active": False, "is_verified": False, "tenant_id": it, "tenant_name": "شركة الحلول المتكاملة",
         "permissions": [], "created_at": now - _td(days=400), "updated_at": now - _td(days=30), "last_login_at": None},
        {"id": str(uuid.uuid4()), "email": "ceo@modernbuild.sa", "full_name": "خالد الراجحي", "full_name_ar": "خالد الراجحي",
         "role": "admin", "is_active": True, "is_verified": True, "tenant_id": mb, "tenant_name": "مجموعة البناء الحديث",
         "permissions": ["admin", "manage_users", "manage_billing", "manage_plans"], "created_at": now - _td(days=365), "updated_at": now - _td(days=1), "last_login_at": now - _td(hours=6)},
        {"id": str(uuid.uuid4()), "email": "ops@futureskills.sa", "full_name": "نورة الشمري", "full_name_ar": "نورة الشمري",
         "role": "manager", "is_active": True, "is_verified": True, "tenant_id": fs, "tenant_name": "أكاديمية المهارات المستقبلية",
         "permissions": ["read_companies", "read_contacts", "manage_opportunities", "reports"], "created_at": now - _td(days=55), "updated_at": now - _td(days=5), "last_login_at": now - _td(days=2)},
    ])


_seed_state()


def _get_tenant(tenant_id: str) -> dict:
    tenant = _tenants_store.get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


def _resolve_tenant_name(tid_str: str) -> str:
    tenant = _tenants_store.get(tid_str)
    if tenant:
        return tenant["name"]
    return tid_str


# ─── Tenant Management ────────────────────────────────────────────


@router.get("/tenants", response_model=list[TenantListItem])
async def list_tenants(
    status: str | None = Query(None),
    plan: str | None = Query(None),
    search: str | None = Query(None),
):
    result = []
    for t in _tenants_store.values():
        if status and not (status == "active" and t["is_active"] or status == "suspended" and not t["is_active"]):
            continue
        if plan and t["plan"] != plan:
            continue
        if search and search.lower() not in t["name"].lower() and search.lower() not in t["slug"].lower():
            continue
        result.append(TenantListItem(**t))
    return sorted(result, key=lambda x: x.created_at, reverse=True)


@router.post("/tenants", response_model=TenantDetail, status_code=201)
async def create_tenant(body: TenantCreate):
    now = datetime.now(timezone.utc)
    tid = str(uuid.uuid4())
    tenant = {
        "id": tid, "name": body.name, "slug": body.slug,
        "domain": body.domain, "plan": "free",
        "is_active": True, "settings": {}, "features": {},
        "user_count": 0, "subscription_ends_at": None,
        "created_at": now, "updated_at": now,
    }
    _tenants_store[tid] = tenant
    return TenantDetail(**tenant)


@router.get("/tenants/{tenant_id}", response_model=TenantDetail)
async def get_tenant(tenant_id: str):
    return TenantDetail(**_get_tenant(tenant_id))


@router.put("/tenants/{tenant_id}", response_model=TenantDetail)
async def update_tenant(tenant_id: str, body: TenantUpdate):
    tenant = _get_tenant(tenant_id)
    if body.name is not None:
        tenant["name"] = body.name
    if body.is_active is not None:
        tenant["is_active"] = body.is_active
    if body.plan_id is not None:
        tenant["plan"] = str(body.plan_id)
    if body.settings is not None:
        tenant["settings"].update(body.settings)
    tenant["updated_at"] = datetime.now(timezone.utc)
    return TenantDetail(**tenant)


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str):
    tenant = _get_tenant(tenant_id)
    tenant["is_active"] = False
    tenant["updated_at"] = datetime.now(timezone.utc)
    return {"message": "Tenant soft-deleted", "tenant_id": tenant_id}


@router.get("/tenants/{tenant_id}/usage", response_model=TenantUsage)
async def get_tenant_usage(tenant_id: str):
    tenant = _get_tenant(tenant_id)
    now = datetime.now(timezone.utc)
    return TenantUsage(
        tenant_id=uuid.UUID(tenant_id),
        tenant_name=tenant["name"],
        api_calls=15420 + hash(tenant_id) % 10000,
        storage_mb=245.8 + hash(tenant_id) % 100,
        active_users=tenant["user_count"],
        total_users=tenant["user_count"],
        period_start=now - _td(days=30),
        period_end=now,
    )


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
async def list_licenses(repos: AdminRepositories = Depends(get_admin_repos)):
    licenses = await repos.licenses.list()
    result = []
    for lic in licenses:
        plan = await repos.plans.get(lic.plan_id)
        result.append(LicenseResponse(
            id=lic.id, tenant_id=lic.tenant_id,
            tenant_name=_resolve_tenant_name(str(lic.tenant_id)),
            plan_id=lic.plan_id, plan_name=plan.name if plan else "Unknown",
            tier=plan.tier if plan else "free",
            is_active=lic.is_active, starts_at=lic.starts_at, ends_at=lic.ends_at,
            created_at=lic.created_at, updated_at=lic.updated_at,
        ))
    return result


@router.post("/licenses", response_model=LicenseResponse, status_code=201)
async def create_license(body: LicenseCreate, repos: AdminRepositories = Depends(get_admin_repos)):
    now = datetime.now(timezone.utc)
    lic = LicenseModel(
        id=uuid.uuid4(), tenant_id=body.tenant_id, plan_id=body.plan_id,
        starts_at=body.starts_at or now,
        ends_at=body.ends_at,
    )
    created = await repos.licenses.create(lic)
    plan = await repos.plans.get(created.plan_id)
    return LicenseResponse(
        id=created.id, tenant_id=created.tenant_id,
        tenant_name=_resolve_tenant_name(str(created.tenant_id)),
        plan_id=created.plan_id, plan_name=plan.name if plan else "Unknown",
        tier=plan.tier if plan else "free",
        is_active=created.is_active, starts_at=created.starts_at, ends_at=created.ends_at,
        created_at=created.created_at, updated_at=created.updated_at,
    )


# ─── Users ────────────────────────────────────────────────────────


@router.get("/users", response_model=list[UserAdminListItem])
async def list_admin_users(
    tenant_id: str | None = Query(None),
    role: str | None = Query(None),
    is_active: bool | None = Query(None),
    search: str | None = Query(None),
):
    result = []
    for u in _users_store:
        if tenant_id and u["tenant_id"] != tenant_id:
            continue
        if role and u["role"] != role:
            continue
        if is_active is not None and u["is_active"] != is_active:
            continue
        if search and search.lower() not in u["full_name"].lower() and search.lower() not in u["email"].lower():
            continue
        result.append(UserAdminListItem(**u))
    return result


@router.get("/users/{user_id}", response_model=UserAdminDetail)
async def get_admin_user(user_id: str):
    for u in _users_store:
        if u["id"] == user_id:
            return UserAdminDetail(**u)
    raise HTTPException(status_code=404, detail="User not found")


@router.put("/users/{user_id}", response_model=UserAdminDetail)
async def update_admin_user(user_id: str, body: UserAdminUpdate):
    for u in _users_store:
        if u["id"] == user_id:
            if body.role is not None:
                u["role"] = body.role
            if body.is_active is not None:
                u["is_active"] = body.is_active
            u["updated_at"] = datetime.now(timezone.utc)
            return UserAdminDetail(**u)
    raise HTTPException(status_code=404, detail="User not found")


@router.delete("/users/{user_id}")
async def deactivate_admin_user(user_id: str):
    for u in _users_store:
        if u["id"] == user_id:
            u["is_active"] = False
            u["updated_at"] = datetime.now(timezone.utc)
            return {"message": "User deactivated", "user_id": user_id}
    raise HTTPException(status_code=404, detail="User not found")


# ─── Billing ──────────────────────────────────────────────────────


@router.get("/billing/invoices", response_model=list[InvoiceResponse])
async def list_invoices(tenant_id: str | None = Query(None), repos: AdminRepositories = Depends(get_admin_repos)):
    invoices = await repos.invoices.list_invoices(tenant_id)
    return [InvoiceResponse(
        id=inv.id, tenant_id=inv.tenant_id,
        tenant_name=_resolve_tenant_name(str(inv.tenant_id)),
        amount=inv.amount, currency=inv.currency,
        status=inv.status, description=inv.description,
        due_date=inv.due_date, paid_at=inv.paid_at,
        created_at=inv.created_at,
    ) for inv in invoices]


@router.get("/billing/transactions", response_model=list[TransactionResponse])
async def list_transactions(tenant_id: str | None = Query(None), repos: AdminRepositories = Depends(get_admin_repos)):
    txs = await repos.invoices.list_transactions(tenant_id)
    return [TransactionResponse(
        id=tx.id, tenant_id=tx.tenant_id,
        tenant_name=_resolve_tenant_name(str(tx.tenant_id)),
        amount=tx.amount, currency=tx.currency,
        status=tx.status, method=tx.method,
        description=tx.description, reference=tx.reference,
        created_at=tx.created_at,
    ) for tx in txs]


# ─── Feature Flags ────────────────────────────────────────────────


@router.get("/feature-flags", response_model=list[FeatureFlagResponse])
async def list_feature_flags(repos: AdminRepositories = Depends(get_admin_repos)):
    flags = await repos.flags.list()
    return [FeatureFlagResponse(
        id=f.id, key=f.key, name=f.name, description=f.description,
        enabled=f.enabled, is_global=f.is_global,
        created_at=f.created_at, updated_at=f.updated_at,
    ) for f in flags]


@router.post("/feature-flags", response_model=FeatureFlagResponse, status_code=201)
async def create_feature_flag(body: FeatureFlagCreate, repos: AdminRepositories = Depends(get_admin_repos)):
    existing = await repos.flags.get_by_key(body.key)
    if existing:
        raise HTTPException(status_code=409, detail=f"Flag with key '{body.key}' already exists")
    flag = FeatureFlagModel(id=uuid.uuid4(), key=body.key, name=body.name,
                       description=body.description, enabled=body.enabled)
    created = await repos.flags.create(flag)
    return FeatureFlagResponse(
        id=created.id, key=created.key, name=created.name,
        description=created.description, enabled=created.enabled,
        is_global=created.is_global,
        created_at=created.created_at, updated_at=created.updated_at,
    )


@router.put("/feature-flags/{flag_id}", response_model=FeatureFlagResponse)
async def update_feature_flag(flag_id: uuid.UUID, body: FeatureFlagUpdate, repos: AdminRepositories = Depends(get_admin_repos)):
    data = body.model_dump(exclude_none=True)
    flag = await repos.flags.update(flag_id, data)
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    return FeatureFlagResponse(
        id=flag.id, key=flag.key, name=flag.name, description=flag.description,
        enabled=flag.enabled, is_global=flag.is_global,
        created_at=flag.created_at, updated_at=flag.updated_at,
    )


@router.get("/feature-flags/{flag_id}/tenants", response_model=list[FeatureFlagTenantResponse])
async def get_feature_flag_tenants(flag_id: uuid.UUID, repos: AdminRepositories = Depends(get_admin_repos)):
    tenants = await repos.flags.get_tenants_for_flag(flag_id)
    result = []
    for t in tenants:
        tid_str = str(t["tenant_id"])
        result.append(FeatureFlagTenantResponse(
            flag_id=t["flag_id"], flag_key=t["flag_key"],
            tenant_id=uuid.UUID(tid_str) if isinstance(t["tenant_id"], str) else t["tenant_id"],
            tenant_name=_resolve_tenant_name(tid_str),
            enabled=t["enabled"],
        ))
    return result


@router.put("/feature-flags/{flag_id}/tenants/{tenant_id}")
async def toggle_flag_for_tenant(flag_id: uuid.UUID, tenant_id: str, body: FeatureFlagUpdate, repos: AdminRepositories = Depends(get_admin_repos)):
    if body.enabled is None:
        raise HTTPException(status_code=400, detail="enabled field required")
    flag = await repos.flags.set_tenant_override(flag_id, tenant_id, body.enabled)
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    return {"message": f"Flag {'enabled' if body.enabled else 'disabled'} for tenant {tenant_id}"}


# ─── Jobs ─────────────────────────────────────────────────────────


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(
    status: str | None = Query(None),
    job_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: AdminRepositories = Depends(get_admin_repos),
):
    jobs, total = await repos.jobs.list(status=status, job_type=job_type, page=page, page_size=page_size)
    return [JobResponse(
        id=j.id, type=j.type, status=j.status, progress=j.progress,
        tenant_id=j.tenant_id, created_by=j.created_by, payload=j.payload,
        result=j.result, error_message=j.error_message,
        retry_count=j.retry_count, max_retries=j.max_retries,
        scheduled_at=j.scheduled_at, started_at=j.started_at,
        completed_at=j.completed_at, created_at=j.created_at, updated_at=j.updated_at,
    ) for j in jobs]


@router.get("/jobs/{job_id}", response_model=JobDetailResponse)
async def get_job(job_id: str, repos: AdminRepositories = Depends(get_admin_repos)):
    job = await repos.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobDetailResponse(
        id=job.id, type=job.type, status=job.status, progress=job.progress,
        tenant_id=job.tenant_id, created_by=job.created_by, payload=job.payload,
        result=job.result, error_message=job.error_message,
        retry_count=job.retry_count, max_retries=job.max_retries,
        scheduled_at=job.scheduled_at, started_at=job.started_at,
        completed_at=job.completed_at, created_at=job.created_at, updated_at=job.updated_at,
        logs=job.logs,
    )


@router.post("/jobs/{job_id}/retry")
async def retry_job(job_id: str, repos: AdminRepositories = Depends(get_admin_repos)):
    job = await repos.jobs.retry(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or not in failed state")
    return {"message": "Job queued for retry", "job_id": job_id}


# ─── AI Costs ─────────────────────────────────────────────────────


@router.get("/ai/costs", response_model=list[AICostResponse])
async def list_ai_costs(
    model: str | None = Query(None),
    tenant_id: str | None = Query(None),
    days: int = Query(30, ge=1, le=365),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: AdminRepositories = Depends(get_admin_repos),
):
    records, total = await repos.ai.list(model=model, tenant_id=tenant_id, days=days, page=page, page_size=page_size)
    return [AICostResponse(
        id=r.id, model=r.model, tenant_id=r.tenant_id,
        tenant_name=_resolve_tenant_name(str(r.tenant_id)) if r.tenant_id else "System",
        prompt_tokens=r.prompt_tokens, completion_tokens=r.completion_tokens,
        total_tokens=r.total_tokens, cost=r.cost, operation=r.operation,
        created_at=r.created_at,
    ) for r in records]


@router.get("/ai/summary", response_model=AICostSummary)
async def get_ai_cost_summary(days: int = Query(30, ge=1, le=365), repos: AdminRepositories = Depends(get_admin_repos)):
    summary = await repos.ai.get_summary(days=days)
    return AICostSummary(**summary)


@router.get("/ai/usage", response_model=AIUsageResponse)
async def get_ai_usage(days: int = Query(30, ge=1, le=365), repos: AdminRepositories = Depends(get_admin_repos)):
    usage = await repos.ai.get_usage(days=days)
    return AIUsageResponse(**usage)


# ─── System Health ────────────────────────────────────────────────


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def get_detailed_health(repos: AdminRepositories = Depends(get_admin_repos)):
    health = await repos.health.get_detailed_health()
    return DetailedHealthResponse(
        overall_status=health["overall_status"],
        uptime_seconds=health["uptime_seconds"],
        components=[HealthComponentStatus(**c) for c in health["components"]],
    )


@router.get("/health/history", response_model=list[HealthHistoryEntry])
async def get_health_history(hours: int = Query(24, ge=1, le=168), repos: AdminRepositories = Depends(get_admin_repos)):
    history = await repos.health.get_history(hours=hours)
    return [HealthHistoryEntry(
        timestamp=h.timestamp,
        overall_status=h.overall_status,
        components=h.components,
    ) for h in history]
