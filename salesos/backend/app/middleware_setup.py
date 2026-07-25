from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.common.middleware import BodyCacheMiddleware, CsrfEnforcementMiddleware, RequestIDMiddleware, RequestLoggingMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware
from app.config import settings
from app.metrics.collector import collector
from app.routers.metrics import MetricsMiddleware


def setup_middleware(app: FastAPI) -> None:
    # Starlette: last add_middleware = outermost. CORS must be outermost.
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(BodyCacheMiddleware, max_body_size=settings.max_body_size)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.allowed_hosts.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=[m.strip() for m in settings.cors_allow_methods.split(",") if m.strip()],
        allow_headers=[h.strip() for h in settings.cors_allow_headers.split(",") if h.strip()],
    )
