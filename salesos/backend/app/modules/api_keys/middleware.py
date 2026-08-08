from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.common.api_key_manager import get_api_key_rate_limiter

from .service import ApiKeyService

# Per-key default when ApiKey model has no rate_limit_per_minute column.
_DEFAULT_API_KEY_RPM = 60


class ApiKeyMiddleware:
    """Validate API key from X-API-Key header.

    Uses ASGI __call__ pattern (not BaseHTTPMiddleware) to avoid
    body streaming deadlocks with nested middleware + exception handlers.

    Reads headers directly from ASGI scope (never consumes request body).
    Applies per-key rate limiting after successful validation.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        headers = Headers(scope=scope)
        api_key = headers.get("x-api-key", "")
        if api_key and not headers.get("authorization", "").startswith("Bearer "):
            request = Request(scope, receive)
            db_session = getattr(request.app.state, "db_session_factory", None)
            if not db_session:
                # EAB-001-P0-SEC-01: fail-closed when X-API-Key present but
                # factory unset — do not silently skip validation.
                resp = JSONResponse(
                    {"detail": "Unable to verify API key"},
                    status_code=503,
                )
                await resp(scope, receive, send)
                return
            async with db_session() as db:
                service = ApiKeyService(db=db)
                key_record = await service.validate(api_key)
                if key_record:
                    request.state.api_key_authenticated = True
                    request.state.api_key_user_id = str(key_record.user_id)
                    request.state.api_key_tenant_id = str(key_record.tenant_id)
                    request.state.api_key_scopes = (
                        key_record.scopes.split(",") if key_record.scopes else []
                    )
                    allowed, retry = get_api_key_rate_limiter().check_rate_limit(
                        str(key_record.id), _DEFAULT_API_KEY_RPM
                    )
                    if not allowed:
                        resp = JSONResponse(
                            {"detail": "Too many requests", "retry_after": retry},
                            status_code=429,
                            headers={"Retry-After": str(retry)},
                        )
                        await resp(scope, receive, send)
                        return
                    # STORY-04-03 gateway layer: suspended tenant API keys are
                    # write-blocked here (defense in depth vs app middleware).
                    method = scope.get("method", "GET").upper()
                    if method in {"POST", "PUT", "PATCH", "DELETE"}:
                        from app.modules.identity.tenant_lifecycle_guard import (
                            fetch_tenant_by_id,
                            is_tenant_suspended,
                            path_skips_suspension_guard,
                            suspension_write_blocked_detail,
                        )

                        path = scope.get("path", "") or ""
                        if not path_skips_suspension_guard(path):
                            tenant = await fetch_tenant_by_id(db, str(key_record.tenant_id))
                            if is_tenant_suspended(tenant):
                                resp = JSONResponse(
                                    {"detail": suspension_write_blocked_detail()},
                                    status_code=403,
                                )
                                await resp(scope, receive, send)
                                return
                else:
                    request.state.api_key_authenticated = False
        await self.app(scope, receive, send)
