from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session, require_role_dep

from ..db_models import FeatureFlagModel
from ..schemas import (
    FeatureFlagCreate,
    FeatureFlagEvaluateRequest,
    FeatureFlagEvaluateResponse,
    FeatureFlagResponse,
    FeatureFlagTenantResponse,
    FeatureFlagUpdate,
)
from ..services import FeatureFlagService
from ._dependencies import AdminRepositories, get_admin_repos

router = APIRouter(
    tags=["Admin - Feature Flags"],
    dependencies=[Depends(require_role_dep("admin"))],
)


@router.get("/feature-flags", response_model=list[FeatureFlagResponse])
async def list_feature_flags(repos: AdminRepositories = Depends(get_admin_repos)):
    flags = await repos.flags.list()
    return [FeatureFlagResponse(
        id=f.id, key=f.key, name=f.name, description=f.description,
        enabled=f.enabled, is_global=f.is_global,
        rollout_percentage=f.rollout_percentage,
        is_ci_test=f.is_ci_test,
        created_at=f.created_at, updated_at=f.updated_at,
    ) for f in flags]


@router.post("/feature-flags", response_model=FeatureFlagResponse, status_code=201)
async def create_feature_flag(body: FeatureFlagCreate, repos: AdminRepositories = Depends(get_admin_repos)):
    existing = await repos.flags.get_by_key(body.key)
    if existing:
        raise HTTPException(status_code=409, detail=f"Flag with key '{body.key}' already exists")
    flag = FeatureFlagModel(
        id=uuid.uuid4(), key=body.key, name=body.name,
        description=body.description, enabled=body.enabled,
        rollout_percentage=body.rollout_percentage if hasattr(body, 'rollout_percentage') else 100,
        is_ci_test=body.is_ci_test if hasattr(body, 'is_ci_test') else False,
    )
    created = await repos.flags.create(flag)
    return FeatureFlagResponse(
        id=created.id, key=created.key, name=created.name,
        description=created.description, enabled=created.enabled,
        is_global=created.is_global,
        rollout_percentage=created.rollout_percentage,
        is_ci_test=created.is_ci_test,
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
        rollout_percentage=flag.rollout_percentage,
        is_ci_test=flag.is_ci_test,
        created_at=flag.created_at, updated_at=flag.updated_at,
    )


@router.get("/feature-flags/{flag_id}/tenants", response_model=list[FeatureFlagTenantResponse])
async def get_feature_flag_tenants(flag_id: uuid.UUID, repos: AdminRepositories = Depends(get_admin_repos)):
    tenants = await repos.flags.get_tenants_for_flag(flag_id)
    return [FeatureFlagTenantResponse(
        flag_id=t["flag_id"], flag_key=t["flag_key"],
        tenant_id=uuid.UUID(t["tenant_id"]) if isinstance(t["tenant_id"], str) else t["tenant_id"],
        tenant_name=t["tenant_id"],
        enabled=t["enabled"],
    ) for t in tenants]


@router.put("/feature-flags/{flag_id}/tenants/{tenant_id}")
async def toggle_flag_for_tenant(flag_id: uuid.UUID, tenant_id: str, body: FeatureFlagUpdate, repos: AdminRepositories = Depends(get_admin_repos)):
    if body.enabled is None:
        raise HTTPException(status_code=400, detail="enabled field required")
    flag = await repos.flags.set_tenant_override(flag_id, tenant_id, body.enabled)
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    return {"message": f"Flag {'enabled' if body.enabled else 'disabled'} for tenant {tenant_id}"}


@router.post("/feature-flags/evaluate", response_model=FeatureFlagEvaluateResponse)
async def evaluate_feature_flag(
    body: FeatureFlagEvaluateRequest,
    repos: AdminRepositories = Depends(get_admin_repos),
    db: AsyncSession = Depends(get_db_session),
):
    flag_svc = FeatureFlagService(db)
    result = await flag_svc.is_enabled(body.flag_key, body.tenant_id)
    return FeatureFlagEvaluateResponse(
        flag_key=body.flag_key,
        tenant_id=body.tenant_id,
        enabled=result["enabled"],
        reason=result["reason"],
    )


@router.post("/feature-flags/ci-test", response_model=FeatureFlagResponse, status_code=201)
async def create_ci_test_flag(
    body: FeatureFlagCreate,
    db: AsyncSession = Depends(get_db_session),
):
    flag_svc = FeatureFlagService(db)
    result = await flag_svc.create_ci_test_flag(body.key, body.name, body.description or "")
    return FeatureFlagResponse(
        id=uuid.UUID(result["id"]), key=result["key"], name=result["name"],
        description=body.description, enabled=True, is_global=True,
        rollout_percentage=100, is_ci_test=True,
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
