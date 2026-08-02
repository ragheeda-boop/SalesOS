"""STORY-04-03 — block mutating requests for suspended tenants (app layer).

Owner/admin/auth/health paths are skipped. DEC-085 untouched. No Production GO.
"""

from __future__ import annotations

from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.database import get_current_tenant_id_context
from app.modules.identity.tenant_lifecycle_guard import (
    WRITE_METHODS,
    fetch_tenant_by_id,
    is_tenant_suspended,
    path_skips_suspension_guard,
    suspension_write_blocked_detail,
)


class SuspendedTenantWriteGuardMiddleware:
    """Reject POST/PUT/PATCH/DELETE when the caller's tenant is suspended."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        method = scope.get("method", "GET").upper()
        if method not in WRITE_METHODS:
            return await self.app(scope, receive, send)

        path = scope.get("path", "") or ""
        if path_skips_suspension_guard(path):
            return await self.app(scope, receive, send)

        request = Request(scope, receive)
        tenant_id = get_current_tenant_id_context()
        if not tenant_id:
            tenant_id = getattr(request.state, "api_key_tenant_id", None)
        if not tenant_id:
            headers = Headers(scope=scope)
            tenant_id = (headers.get("x-tenant-id") or "").strip() or None
        if not tenant_id:
            return await self.app(scope, receive, send)

        db_session = getattr(request.app.state, "db_session_factory", None)
        if not db_session:
            return await self.app(scope, receive, send)

        try:
            async with db_session() as db:
                tenant = await fetch_tenant_by_id(db, str(tenant_id))
                blocked = is_tenant_suspended(tenant)
        except Exception:
            resp = JSONResponse(
                {"detail": "Unable to verify tenant suspension status"},
                status_code=503,
            )
            await resp(scope, receive, send)
            return

        if blocked:
            resp = JSONResponse(
                {"detail": suspension_write_blocked_detail()},
                status_code=403,
            )
            await resp(scope, receive, send)
            return

        return await self.app(scope, receive, send)
