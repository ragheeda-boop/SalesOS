"""STORY-06-02/06-03 — Enforce Plan.entitlements + UsageMeter quotas.

Skips Owner/admin/auth for domain gates. Seat quota still applies on invite.
Does not weaken auth/CSRF/RBAC. DEC-085 untouched. Not Production GO.
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
from app.modules.admin.quota_enforcement import (
    evaluate_quota_violations,
    limits_from_entitlements,
    over_quota_payload,
)
from app.modules.admin.quota_gates import quota_metrics_for_path
from app.modules.billing.usage_meter_service import UsageMeterService


class EntitlementEnforcementMiddleware:
    """Reject gated DOM surfaces without entitlement; enforce UsageMeter quotas."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        domain_on = bool(getattr(settings, "entitlement_enforcement_enabled", True))
        quota_on = bool(getattr(settings, "quota_enforcement_enabled", True))
        if not domain_on and not quota_on:
            return await self.app(scope, receive, send)

        path = scope.get("path", "") or ""
        method = (scope.get("method") or "GET").upper()
        skip_domain = path_skips_entitlement_guard(path)
        gate = None if (skip_domain or not domain_on) else required_domain_for_path(path)
        metrics = quota_metrics_for_path(path, method) if quota_on else None
        if gate is None and not metrics:
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
                if gate is not None and not domain_enabled(ents, gate.domain):
                    resp = JSONResponse(
                        {
                            "detail": (
                                f"Plan entitlement required: {gate.domain} "
                                f"(path {gate.path_prefix}). "
                                "Upgrade plan to access this capability."
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

                if metrics:
                    snap = await UsageMeterService(db).quota_usage_snapshot(
                        tenant_id=str(tenant_id)
                    )
                    violations = evaluate_quota_violations(
                        limits=limits_from_entitlements(ents),
                        usage=snap["usage"],
                        metrics=metrics,
                    )
                    if violations:
                        v = violations[0]
                        resp = JSONResponse(
                            over_quota_payload(
                                v,
                                period=snap.get("period"),
                                plan_id=meta.get("plan_id"),
                                tier=meta.get("tier"),
                            ),
                            status_code=v.status_code,
                        )
                        await resp(scope, receive, send)
                        return
        except Exception:
            resp = JSONResponse(
                {"detail": "Unable to verify plan entitlements"},
                status_code=503,
            )
            await resp(scope, receive, send)
            return

        return await self.app(scope, receive, send)
