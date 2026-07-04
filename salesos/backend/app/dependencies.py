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
