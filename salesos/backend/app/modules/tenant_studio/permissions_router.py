"""STORY-10-06 — Tenant Studio Permissions HTTP (CAP-003).

Custom roles capped at Plan.entitlements ceiling; privilege escalation blocked.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id, verify_token
from app.modules.tenant_studio.custom_roles import CustomRoleError
from app.modules.tenant_studio.custom_roles_store import (
    DEFAULT_CUSTOM_ROLES_STORE,
    MemCustomRolesStore,
)
from app.modules.tenant_studio.permission_ceiling import PermissionCeilingError

router = APIRouter(prefix="/studio/permissions", tags=["Tenant Studio"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_CUSTOM_ROLES_STORE


class CustomRoleUpsert(BaseModel):
    id: str | None = None
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    permissions: list[str] = Field(default_factory=list)
    plan_tier: str | None = Field(
        default=None,
        description="Optional tier default when tenant ceiling not yet set",
    )
    entitlements: dict[str, Any] | None = Field(
        default=None,
        description="Optional Plan.entitlements override (EPIC-06 document)",
    )


class CustomRoleResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str = ""
    permissions: list[str] = Field(default_factory=list)
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""


class CeilingCheckBody(BaseModel):
    permissions: list[str] = Field(default_factory=list)
    plan_tier: str | None = None
    entitlements: dict[str, Any] | None = None


class CeilingCheckResponse(BaseModel):
    allowed: bool
    rejected: list[str] = Field(default_factory=list)
    reasons: dict[str, str] = Field(default_factory=dict)
    grantable: list[str] = Field(default_factory=list)


class SetCeilingBody(BaseModel):
    plan_tier: str | None = None
    entitlements: dict[str, Any] | None = None


@router.get("/catalog", dependencies=_AUTH)
async def permissions_catalog(
    plan_tier: str | None = Query(None),
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[dict[str, Any]]:
    return _STORE.catalog(tenant_id=str(tenant_id), plan_tier=plan_tier)


@router.get("/ceiling", dependencies=_AUTH)
async def permissions_ceiling(
    plan_tier: str | None = Query(None),
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict[str, Any]:
    return _STORE.ceiling_summary(tenant_id=str(tenant_id), plan_tier=plan_tier)


@router.put("/ceiling", dependencies=_AUTH)
async def set_permissions_ceiling(
    body: SetCeilingBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict[str, Any]:
    try:
        doc = _STORE.set_ceiling(
            str(tenant_id),
            body.entitlements,
            plan_tier=body.plan_tier,
        )
    except (CustomRoleError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _STORE.ceiling_summary(tenant_id=str(tenant_id)) | {
        "version": doc.version,
    }


@router.post("/check", response_model=CeilingCheckResponse, dependencies=_AUTH)
async def check_permissions_ceiling(
    body: CeilingCheckBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> CeilingCheckResponse:
    result = _STORE.check(
        tenant_id=str(tenant_id),
        permissions=list(body.permissions),
        entitlements=body.entitlements,
        plan_tier=body.plan_tier,
    )
    return CeilingCheckResponse.model_validate(result.as_dict())


@router.post("/roles", response_model=CustomRoleResponse, dependencies=_AUTH)
async def upsert_custom_role(
    body: CustomRoleUpsert,
    tenant_id: str = Depends(get_current_tenant_id),
) -> CustomRoleResponse:
    try:
        row = _STORE.upsert(
            tenant_id=str(tenant_id),
            name=body.name,
            permissions=list(body.permissions),
            description=body.description,
            role_id=body.id,
            entitlements=body.entitlements,
            plan_tier=body.plan_tier,
        )
    except PermissionCeilingError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except CustomRoleError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return CustomRoleResponse.model_validate(row.as_dict())


@router.get("/roles", response_model=list[CustomRoleResponse], dependencies=_AUTH)
async def list_custom_roles(
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[CustomRoleResponse]:
    rows = _STORE.list_for_tenant(tenant_id=str(tenant_id))
    return [CustomRoleResponse.model_validate(r.as_dict()) for r in rows]


@router.get("/roles/{role_id}", response_model=CustomRoleResponse, dependencies=_AUTH)
async def get_custom_role(
    role_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> CustomRoleResponse:
    row = _STORE.get(role_id, tenant_id=str(tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="custom role not found")
    return CustomRoleResponse.model_validate(row.as_dict())


def bind_store(store: MemCustomRolesStore) -> None:
    """Test helper — swap process-local store."""
    global _STORE  # noqa: PLW0603
    _STORE = store
