"""Owner Platform auth dependencies (``salesos-owner-platform`` audience).

Isolated from tenant ``app.dependencies.verify_token`` (``salesos-api``).
STORY-02-03 / DEC-093 consumption wiring.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Header, HTTPException

from app.common.exceptions import UnauthorizedError
from app.dependencies import require_role


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
) -> str:
    """Resolve role for an Owner Platform caller (owner audience only).

    Tenant role alone never grants Owner Platform access: the caller must be a
    designated platform owner (``User.is_platform_owner``).
    """
    # Owner JWTs intentionally carry no tenant_id. A normal request session
    # therefore cannot read FORCE-RLS protected users; use the same BYPASSRLS
    # owner probe as refresh-token validation instead of turning a valid owner
    # token into a misleading 404.
    from app.database import probe_platform_owner_status

    status = await probe_platform_owner_status(str(token_payload.get("sub", "")))
    if status is None:
        raise HTTPException(status_code=401, detail="Owner account not found")
    is_active, role, is_platform_owner = status
    if not is_active or not is_platform_owner:
        raise HTTPException(
            status_code=403,
            detail="Owner Platform requires a designated platform owner",
        )
    return role


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
