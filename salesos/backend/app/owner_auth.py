"""Owner Platform auth dependencies (``salesos-owner-platform`` audience).

Isolated from tenant ``app.dependencies.verify_token`` (``salesos-api``).
STORY-02-03 / DEC-093 consumption wiring.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import UnauthorizedError
from app.dependencies import get_db_session, require_role


async def verify_owner_token(
    authorization: str | None = Header(None, description="Bearer owner token"),
) -> dict:
    """Require a Bearer access token for Owner Platform (``salesos-owner-platform``).

    Tenant-audience tokens are rejected. Does not alter tenant ``verify_token``.
    """
    if not authorization:
        raise UnauthorizedError("Not authenticated")
    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("Invalid authorization scheme; expected Bearer")
    token = authorization[7:].strip()
    if not token:
        raise UnauthorizedError("Not authenticated")
    from app.modules.identity.service import decode_owner_access_token

    return decode_owner_access_token(token)


async def get_current_owner_user_id(
    token_payload: dict = Depends(verify_owner_token),
) -> str:
    return str(token_payload.get("sub", "") or "")


async def get_current_owner_user_role(
    token_payload: dict = Depends(verify_owner_token),
    db: AsyncSession = Depends(get_db_session),
) -> str:
    """Resolve role for an Owner Platform caller (owner audience only)."""
    from app.modules.identity.service import IdentityService

    service = IdentityService(db=db)
    user = await service.get_user(token_payload.get("sub", ""))
    return user.role


async def get_owner_scoped_tenant_id(
    x_tenant_id: str | None = Header(
        None, alias="X-Tenant-Id", description="Tenant ID for Owner Platform scoped queries"
    ),
    _token_payload: dict = Depends(verify_owner_token),
) -> str:
    """Tenant scope for Owner Platform routes (header required; owner JWT has no tenant_id)."""
    if not x_tenant_id:
        raise HTTPException(
            status_code=400,
            detail="Tenant ID required via X-Tenant-Id header for Owner Platform scoped queries",
        )
    return x_tenant_id


def require_owner_role_dep(required_role: str) -> Callable:
    """Factory for Owner Platform role check (``salesos-owner-platform`` audience)."""

    async def _require_owner_role(
        user_role: str = Depends(get_current_owner_user_role),
    ) -> bool:
        return await require_role(required_role, user_role=user_role)

    return _require_owner_role
