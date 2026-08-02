from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.common.middleware import (
    BodyCacheMiddleware,
    CsrfEnforcementMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    TenantContextMiddleware,
)
from app.config import settings
from app.routers.metrics import MetricsMiddleware


def setup_middleware(app: FastAPI) -> None:
    # Starlette: last add_middleware = outermost. Add security/app middleware
    # first, then CORS last so preflight and error responses always get ACAO.
    from app.modules.identity.suspended_tenant_middleware import (
        SuspendedTenantWriteGuardMiddleware,
    )
    from app.modules.admin.entitlement_middleware import (
        EntitlementEnforcementMiddleware,
    )

    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(BodyCacheMiddleware, max_body_size=settings.max_body_size)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    # Inner of TenantContext so ContextVar tenant_id is already set (STORY-04-03 / 06-02).
    app.add_middleware(EntitlementEnforcementMiddleware)
    app.add_middleware(SuspendedTenantWriteGuardMiddleware)
    app.add_middleware(TenantContextMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CsrfEnforcementMiddleware)
    app.add_middleware(MetricsMiddleware)

    _redis = None
    try:
        import redis.asyncio as aioredis

        _redis = aioredis.Redis.from_url(settings.redis_url)
    except Exception:
        pass
    app.add_middleware(RateLimitMiddleware, window=settings.rate_limit_window, redis_client=_redis)

    from app.modules.audit.middleware import AuditMiddleware

    app.add_middleware(AuditMiddleware)

    from app.modules.api_keys.middleware import ApiKeyMiddleware

    app.add_middleware(ApiKeyMiddleware)

    # Outermost — must wrap all other middleware for CORS on errors/OPTIONS.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.allowed_hosts.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=[m.strip() for m in settings.cors_allow_methods.split(",") if m.strip()],
        allow_headers=[h.strip() for h in settings.cors_allow_headers.split(",") if h.strip()],
        # Admin tenant list pagination (Stream A) — FE may read total without body wrap.
        expose_headers=["X-Total-Count"],
    )
