from __future__ import annotations

import contextlib
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session, require_role_dep
from app.modules.identity.models import Tenant, User

from ..pg_repositories import PostgresRoleRepository
from ..schemas import (
    UserAdminDetail,
    UserAdminListItem,
    UserAdminUpdate,
)

router = APIRouter(
    tags=["Admin - Users"],
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


@router.get("/users", response_model=list[UserAdminListItem])
async def list_admin_users(
    tenant_id: str | None = Query(None),
    role: str | None = Query(None),
    is_active: bool | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(User)
    if tenant_id:
        with contextlib.suppress(ValueError):
            stmt = stmt.where(User.tenant_id == uuid.UUID(tenant_id))
    if role:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(User.full_name.ilike(pattern) | User.email.ilike(pattern))
    result = await db.execute(stmt)
    users = result.scalars().all()

    response = []
    for u in users:
        tenant_name = await _resolve_tenant_name(db, str(u.tenant_id))
        response.append(
            UserAdminListItem(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                full_name_ar=u.full_name_ar,
                role=u.role,
                is_active=u.is_active,
                is_verified=u.is_verified,
                tenant_id=u.tenant_id,
                tenant_name=tenant_name,
                created_at=u.created_at,
                last_login_at=u.last_login_at,
            )
        )
    return response


@router.get("/users/{user_id}", response_model=UserAdminDetail)
async def get_admin_user(user_id: str, db: AsyncSession = Depends(get_db_session)):
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found") from None
    user = await db.get(User, uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    tenant_name = await _resolve_tenant_name(db, str(user.tenant_id))
    role_repo = PostgresRoleRepository(db)
    roles_with_perms = await role_repo.get_roles_with_permissions()
    permissions = []
    for rp in roles_with_perms:
        if rp["name"].lower() == user.role.lower() or rp["id"] == user.role:
            permissions = rp["permissions"]
            break

    return UserAdminDetail(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        full_name_ar=user.full_name_ar,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        tenant_id=user.tenant_id,
        tenant_name=tenant_name,
        permissions=permissions,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )


@router.put("/users/{user_id}", response_model=UserAdminDetail)
async def update_admin_user(
    user_id: str, body: UserAdminUpdate, db: AsyncSession = Depends(get_db_session)
):
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found") from None
    user = await db.get(User, uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    user.updated_at = datetime.now(UTC)
    await db.flush()

    tenant_name = await _resolve_tenant_name(db, str(user.tenant_id))
    return UserAdminDetail(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        full_name_ar=user.full_name_ar,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        tenant_id=user.tenant_id,
        tenant_name=tenant_name,
        permissions=[],
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )


@router.delete("/users/{user_id}")
async def deactivate_admin_user(user_id: str, db: AsyncSession = Depends(get_db_session)):
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found") from None
    user = await db.get(User, uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    user.updated_at = datetime.now(UTC)
    await db.flush()
    return {"message": "User deactivated", "user_id": user_id}
