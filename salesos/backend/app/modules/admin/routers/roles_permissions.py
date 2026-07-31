from __future__ import annotations

import hashlib

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_role_dep

from ..db_models import RoleModel
from ..schemas import (
    PermissionResponse,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
)
from ._dependencies import AdminRepositories, get_admin_repos

router = APIRouter(
    tags=["Admin - Roles & Permissions"],
    dependencies=[Depends(require_role_dep("admin"))],
)


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    tenant_id: str | None = Query(None),
    repos: AdminRepositories = Depends(get_admin_repos),
):
    roles = await repos.roles.get_roles_with_permissions(tenant_id)
    return [RoleResponse(
        id=r["id"], name=r["name"], description=r["description"],
        is_system=r["is_system"], tenant_id=r["tenant_id"],
        permissions=r["permissions"],
        created_at=r["created_at"], updated_at=r["updated_at"],
    ) for r in roles]


@router.post("/roles", response_model=RoleResponse, status_code=201)
async def create_role(body: RoleCreate, repos: AdminRepositories = Depends(get_admin_repos)):
    role_id = f"role_{hashlib.md5(
        body.name.encode(), usedforsecurity=False
    ).hexdigest()[:8]}"
    existing = await repos.roles.get(role_id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Role '{body.name}' already exists")

    role = RoleModel(
        id=role_id,
        name=body.name,
        description=body.description,
        is_system=False,
    )
    created = await repos.roles.create(role)
    if body.permissions:
        await repos.roles.set_permissions(role_id, body.permissions)

    return RoleResponse(
        id=created.id, name=created.name, description=created.description,
        is_system=created.is_system, tenant_id=created.tenant_id,
        permissions=body.permissions,
        created_at=created.created_at, updated_at=created.updated_at,
    )


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(role_id: str, body: RoleUpdate, repos: AdminRepositories = Depends(get_admin_repos)):
    data = body.model_dump(exclude_none=True)
    perms = data.pop("permissions", None)
    updated = await repos.roles.update(role_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Role not found")
    if perms is not None:
        await repos.roles.set_permissions(role_id, perms)

    permissions = await repos.roles.get_permissions(role_id)
    return RoleResponse(
        id=updated.id, name=updated.name, description=updated.description,
        is_system=updated.is_system, tenant_id=updated.tenant_id,
        permissions=permissions,
        created_at=updated.created_at, updated_at=updated.updated_at,
    )


@router.delete("/roles/{role_id}")
async def delete_role(role_id: str, repos: AdminRepositories = Depends(get_admin_repos)):
    deleted = await repos.roles.delete(role_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Role not found or system role")
    return {"status": "deleted", "id": role_id}


@router.get("/permissions", response_model=list[PermissionResponse])
async def list_permissions(repos: AdminRepositories = Depends(get_admin_repos)):
    perms = await repos.permissions.list()
    return [PermissionResponse(
        id=p.id, key=p.key, name=p.name,
        description=p.description, group=p.group,
    ) for p in perms]
