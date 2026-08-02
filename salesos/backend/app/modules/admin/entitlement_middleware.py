"""STORY-06-02 — Enforce Plan.entitlements on gated tenant API paths.

Skips Owner/admin/auth. Does not weaken auth/CSRF/RBAC. DEC-085 untouched.
Not Production GO.
"""

from __future__ import annotations

from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings
from app.database import get_current_tenant_id_context
from app.modules.admin.entitlement_gates import (
    path_skips_entitlement_guard,
    required_domain_for_path,
)
from app.modules.admin.entitlement_resolver import resolve_entitlements_for_tenant
from app.modules.admin.entitlements import domain_enabled


class EntitlementEnforcementMiddleware:
    """Reject requests to gated DOM surfaces when the tenant plan lacks entitlement."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        if not bool(getattr(settings, "entitlement_enforcement_enabled", True)):
            return await self.app(scope, receive, send)

        path = scope.get("path", "") or ""
        if path_skips_entitlement_guard(path):
            return await self.app(scope, receive, send)

        gate = required_domain_for_path(path)
        if gate is None:
            return await self.app(scope, receive, send)

        request = Request(scope, receive)
        tenant_id = get_current_tenant_id_context()
        if not tenant_id:
            tenant_id = getattr(request.state, "api_key_tenant_id", None)
        if not tenant_id:
            headers = Headers(scope=scope)
            tenant_id = (headers.get("x-tenant-id") or "").strip() or None
        if not tenant_id:
            # No tenant context yet — leave to auth; do not invent access.
            return await self.app(scope, receive, send)

        db_session = getattr(request.app.state, "db_session_factory", None)
        if not db_session:
            return await self.app(scope, receive, send)

        try:
            async with db_session() as db:
                ents, meta = await resolve_entitlements_for_tenant(db, str(tenant_id))
                allowed = domain_enabled(ents, gate.domain)
        except Exception:
            resp = JSONResponse(
                {"detail": "Unable to verify plan entitlements"},
                status_code=503,
            )
            await resp(scope, receive, send)
            return

        if not allowed:
            resp = JSONResponse(
                {
                    "detail": (
                        f"Plan entitlement required: {gate.domain} "
                        f"(path {gate.path_prefix}). Upgrade plan to access this capability."
                    ),
                    "domain": gate.domain,
                    "path_prefix": gate.path_prefix,
                    "plan_id": meta.get("plan_id"),
                    "tier": meta.get("tier"),
                },
                status_code=403,
            )
            await resp(scope, receive, send)
            return

        return await self.app(scope, receive, send)
