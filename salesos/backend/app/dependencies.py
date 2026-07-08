from collections.abc import Callable

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from sdk.permissions import PermissionAction, PermissionEnforcer
from sdk.exceptions import PermissionDeniedError


async def verify_token(
    authorization: str = Header(..., description="Bearer token"),
) -> dict:
    token = authorization.replace("Bearer ", "")
    from app.modules.identity.service import decode_access_token

    return decode_access_token(token)


async def get_optional_token(
    authorization: str | None = Header(None),
) -> dict | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return await verify_token(authorization=authorization)


async def get_current_user_id(
    token_payload: dict = Depends(verify_token),
) -> str:
    return token_payload.get("sub", "")


async def get_current_tenant_id(
    x_tenant_id: str = Header(..., description="Tenant ID for multi-tenancy"),
    token_payload: dict = Depends(verify_token),
) -> str:
    token_tenant = token_payload.get("tenant_id")
    if token_tenant and str(token_tenant) != x_tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Tenant ID in header does not match authenticated user's tenant",
        )
    return x_tenant_id


async def get_db_session(
    db: AsyncSession = Depends(get_db),
) -> AsyncSession:
    return db


async def get_current_user_role(
    token_payload: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db_session),
) -> str:
    from app.modules.identity.service import IdentityService
    service = IdentityService(db=db)
    user = await service.get_user(token_payload.get("sub", ""))
    return user.role


async def require_role(
    role: str,
    user_role: str = Depends(get_current_user_role),
) -> bool:
    role_hierarchy = {"admin": 3, "manager": 2, "user": 1, "api": 1, "auditor": 0}
    if role_hierarchy.get(user_role, 0) < role_hierarchy.get(role, 0):
        raise HTTPException(
            status_code=403,
            detail=f"Requires role '{role}' or higher, user has '{user_role}'",
        )
    return True


async def require_permission(
    resource: str,
    action: PermissionAction,
    token_payload: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db_session),
) -> bool:
    from app.modules.identity.service import IdentityService

    service = IdentityService(db=db)
    try:
        user = await service.get_user(token_payload.get("sub", ""))
        PermissionEnforcer.check(user.role, resource, action)
        return True
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


def require_role_dep(required_role: str) -> Callable:
    """Factory for role-checking dependency. Use: Depends(require_role_dep('admin'))."""
    async def _require_role(user_role: str = Depends(get_current_user_role)) -> bool:
        return await require_role(required_role, user_role=user_role)
    return _require_role


def require_permission_dep(resource: str, action: PermissionAction) -> Callable:
    """Factory for permission-checking dependency. Use: Depends(require_permission_dep('company', PermissionAction.CREATE))."""
    async def _require_permission(
        token_payload: dict = Depends(verify_token),
        db: AsyncSession = Depends(get_db_session),
    ) -> bool:
        return await require_permission(resource, action, token_payload=token_payload, db=db)
    return _require_permission
