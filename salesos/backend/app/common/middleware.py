import logging
import os
import time
import uuid

from fastapi import Request
from starlette.responses import JSONResponse

from app.config import settings

logger = logging.getLogger(__name__)


class BodyCacheMiddleware:
    """Cache the request body and make it available via request.state.body.

    Reads the body from the ASGI receive stream once and stores it in
    scope['state']['body'].  Downstream middleware and route handlers can
    retrieve it via request.state.body without consuming the stream.

    Skips body caching for methods without request bodies (GET, HEAD, OPTIONS,
    DELETE) to reduce overhead under load.
    """

    _DEFAULT_MAX_BODY_SIZE = 10 * 1024 * 1024  # 10 MB
    _BODY_METHODS = frozenset({"POST", "PUT", "PATCH"})

    def __init__(self, app, max_body_size: int = _DEFAULT_MAX_BODY_SIZE):
        self.app = app
        self.max_body_size = max_body_size

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        if scope.get("method", "GET") not in self._BODY_METHODS:
            return await self.app(scope, receive, send)

        chunks = []
        total_size = 0
        more_body = True
        while more_body:
            message = await receive()
            chunk = message.get("body", b"")
            chunks.append(chunk)
            total_size += len(chunk)
            if total_size > self.max_body_size:
                response = JSONResponse(
                    status_code=413,
                    content={
                        "detail": "Request body too large",
                        "detail_ar": "حجم الطلب أكبر من الحد المسموح",
                    },
                )
                await response(scope, receive, send)
                return
            more_body = message.get("more_body", False)

        body = b"".join(chunks)

        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["body"] = body
        # Legacy key retained for callers/tests that read scope["body_cache"]
        scope["body_cache"] = body

        body_sent = False

        async def cached_receive():
            nonlocal body_sent
            if not body_sent:
                body_sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.disconnect"}

        await self.app(scope, cached_receive, send)


def _get_client_ip(scope: dict) -> str:
    """Extract client IP from request scope, handling proxies."""
    headers = dict(scope.get("headers", []))
    for _header_name, header_bytes in [
        (b"x-forwarded-for", b"x-forwarded-for"),
        (b"x-real-ip", b"x-real-ip"),
    ]:
        if header_bytes in headers:
            val = headers[header_bytes].decode().split(",")[0].strip()
            if val:
                return str(val)
    client = scope.get("client")
    if not client:
        return "unknown"
    host = client[0]
    return str(host) if host is not None else "unknown"


_SEARCH_ENRICH_PREFIXES = ("/api/v1/search", "/api/v1/entity-resolution", "/api/v1/data-fabric")
_GRAPHQL_PREFIX = "/graphql"


class RateLimitMiddleware:
    """Sliding-window rate limiter with identity-aware keys and tiered limits.

    Redis-backed when available, in-memory fallback for dev/staging.
    Anonymous traffic is keyed by IP + path bucket; authenticated JWT/API-key
    traffic compounds tenant/user (+ IP) so shared egress IPs do not collide.
    """

    _CLEANUP_INTERVAL = 300  # seconds between stale-entry sweeps

    def __init__(self, app, window: int = 60, redis_client=None):
        self.app = app
        self.window = window
        self._redis = redis_client
        self._local: dict[str, list[float]] = {}
        self._last_cleanup: float = time.time()

    def _cleanup_local(self, now: float) -> None:
        """Remove entries older than 1 hour to prevent memory leaks."""
        if now - self._last_cleanup < self._CLEANUP_INTERVAL:
            return
        cutoff = now - 3600
        stale_keys = [k for k, v in self._local.items() if not v or v[-1] < cutoff]
        for k in stale_keys:
            del self._local[k]
        self._last_cleanup = now

    @staticmethod
    def _is_authenticated(request: Request, auth_header: str) -> bool:
        """Authenticated tier only after verified API key or decodable JWT.

        Presence of a Bearer prefix alone must not raise the limit (PROD-W5-002).
        """
        if getattr(request.state, "api_key_authenticated", False):
            return True
        if not auth_header.startswith("Bearer "):
            return False
        token = auth_header[7:].strip()
        if not token:
            return False
        try:
            from app.modules.identity.service import decode_access_token

            decode_access_token(token)
            return True
        except Exception:
            return False

    @staticmethod
    def _identity_parts(request: Request, auth_header: str) -> tuple[str | None, str | None]:
        """Best-effort tenant/user for rate-limit keying (never required for anon)."""
        if getattr(request.state, "api_key_authenticated", False):
            tenant = getattr(request.state, "api_key_tenant_id", None)
            user = getattr(request.state, "api_key_user_id", None)
            return (str(tenant) if tenant else None, str(user) if user else None)
        if not auth_header.startswith("Bearer "):
            return (None, None)
        token = auth_header[7:].strip()
        if not token:
            return (None, None)
        try:
            from app.modules.identity.service import decode_access_token

            payload = decode_access_token(token)
            tenant = payload.get("tenant_id")
            user = payload.get("sub")
            return (str(tenant) if tenant else None, str(user) if user else None)
        except Exception:
            return (None, None)

    @staticmethod
    def _rate_limit_key(client_ip: str, path: str, tenant: str | None, user: str | None) -> str:
        """Compound key when identity is known; keep anon IP-scoped.

        Also buckets by coarse path tier so identity smoke traffic does not
        share the same counter as authenticated API probing from one IP.
        """
        if path.startswith("/api/v1/identity"):
            bucket = "identity"
        elif path in ("/health", "/health/live", "/health/ready", "/csrf-token") or path.startswith(
            ("/docs", "/redoc")
        ):
            bucket = "health"
        elif path.startswith(_GRAPHQL_PREFIX) or path.startswith("/api/v1/"):
            bucket = "api"
        else:
            bucket = "default"

        if tenant and user:
            return f"ratelimit:t:{tenant}:u:{user}:ip:{client_ip}:{bucket}"
        if tenant:
            return f"ratelimit:t:{tenant}:ip:{client_ip}:{bucket}"
        return f"ratelimit:anon:{client_ip}:{bucket}"

    def _select_tier(self, path: str, authenticated: bool) -> int:
        """Return the per-minute rate limit for the given request path."""
        health_paths = ("/health", "/health/live", "/health/ready", "/csrf-token")
        if path in health_paths or path.startswith(("/docs", "/redoc")):
            return settings.rate_limit_health
        # NOTE: RateLimitMiddleware runs before CsrfEnforcementMiddleware in the
        # stack (see app/boot/middleware.py). CSRF-failing POST/PUT/PATCH/DELETE
        # requests will therefore consume the caller's rate-limit budget before
        # the CSRF 403 is returned. This is a known P2 limitation; a full fix
        # requires middleware reordering or post-response rate-limit accounting.
        if path.startswith("/api/v1/identity"):
            return settings.rate_limit_identity
        if any(path.startswith(p) for p in _SEARCH_ENRICH_PREFIXES):
            return settings.rate_limit_search
        if path.startswith(_GRAPHQL_PREFIX) or path.startswith("/api/v1/"):
            if authenticated:
                return settings.rate_limit_authenticated
            return settings.rate_limit_anonymous
        return settings.rate_limit_default

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        if os.environ.get("SALESOS_TESTING") == "true":
            return await self.app(scope, receive, send)

        request = Request(scope, receive)
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        auth_header = request.headers.get("authorization", "")
        tier_rate = self._select_tier(path, self._is_authenticated(request, auth_header))
        now = time.time()

        tenant, user = self._identity_parts(request, auth_header)
        key = self._rate_limit_key(client_ip, path, tenant, user)

        # --- Redis path ---
        if self._redis:
            try:
                import asyncio

                # Bound Redis awaits — hung Redis would block ALL routes
                # (including register) before the handler; no register_enter log.
                count = await asyncio.wait_for(self._redis.incr(key), timeout=2.0)
                if count == 1:
                    await asyncio.wait_for(self._redis.expire(key, self.window), timeout=2.0)
                if count > tier_rate:
                    retry_after = self.window
                    response = JSONResponse(
                        status_code=429,
                        content={"detail": "Too many requests", "retry_after": retry_after},
                        headers={"Retry-After": str(retry_after)},
                    )
                    await response(scope, receive, send)
                    return
                await self.app(scope, receive, send)
                return
            except Exception:
                pass  # fall through to in-memory

        # --- In-memory sliding window path ---
        self._cleanup_local(now)
        window_start = now - self.window
        timestamps = self._local.get(key, [])
        timestamps = [t for t in timestamps if t > window_start]
        timestamps.append(now)
        self._local[key] = timestamps
        count = len(timestamps)

        if count > tier_rate:
            retry_after = self.window
            response = JSONResponse(
                status_code=429,
                content={"detail": "Too many requests", "retry_after": retry_after},
                headers={"Retry-After": str(retry_after)},
            )
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)


class TenantContextMiddleware:
    """Resolve tenant from X-Tenant-Id header (or JWT fallback) before any
    dependency runs, storing it in a ContextVar so get_db() can SET LOCAL
    app.tenant_id before yielding the session.

    Security (R-22): when both a header and a Bearer token are present, the
    header value MUST match the token's tenant_id claim — a mismatch is
    rejected with 403 (fail-closed) instead of trusting the client-controlled
    header. This blocks cross-tenant RLS impersonation.

    This MUST run early in the middleware stack — before any middleware or
    dependency that opens a DB session. Without this, RLS policies return
    zero rows (fail-closed) because the session variable is never set.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        headers = dict(scope.get("headers", []))
        header_tenant = self._header_tenant(headers)
        token_tenant = self._token_tenant(headers)

        if header_tenant and token_tenant and header_tenant != token_tenant:
            response = JSONResponse(
                status_code=403,
                content={"detail": "X-Tenant-Id does not match the authenticated user's tenant"},
            )
            return await response(scope, receive, send)

        tenant_id = header_tenant or token_tenant
        if tenant_id:
            from app.database import set_current_tenant_id

            set_current_tenant_id(tenant_id)

        return await self.app(scope, receive, send)

    @staticmethod
    def _header_tenant(headers: dict) -> str | None:
        raw = headers.get(b"x-tenant-id")
        if not raw:
            return None
        value = raw.decode().strip()
        return value or None

    @staticmethod
    def _token_tenant(headers: dict) -> str | None:
        auth = headers.get(b"authorization")
        if not auth or not auth.startswith(b"Bearer "):
            return None
        token = auth[7:].decode().strip()
        if not token:
            return None
        try:
            from app.modules.identity.service import decode_access_token

            payload = decode_access_token(token)
            tid = payload.get("tenant_id")
            return str(tid) if tid else None
        except Exception:
            return None


class SecurityHeadersMiddleware:
    """Add security headers to every response.
    Uses relaxed CSP for Swagger/ReDoc routes (debug only), strict CSP for everything else.
    """

    _STRICT_CSP = (
        b"default-src 'self'; "
        b"script-src 'self'; "
        b"style-src 'self' 'unsafe-inline'; "
        b"img-src 'self' data:; "
        b"font-src 'self'; "
        b"connect-src 'self'"
    )

    _DOCS_CSP = (
        b"default-src 'self'; "
        b"script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        b"style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        b"img-src 'self' data: https://cdn.jsdelivr.net https://fastapi.tiangolo.com; "
        b"font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
        b"connect-src 'self' https://cdn.jsdelivr.net"
    )

    _DOCS_PREFIXES = ("/docs", "/redoc", "/openapi.json")

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path = scope.get("path", "")
        csp = self._DOCS_CSP if path.startswith(self._DOCS_PREFIXES) else self._STRICT_CSP

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                extra = [
                    (b"content-security-policy", csp),
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"x-xss-protection", b"1; mode=block"),
                    (b"strict-transport-security", b"max-age=31536000; includeSubDomains"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
                ]
                message["headers"] = headers + extra
            await send(message)

        await self.app(scope, receive, send_wrapper)


class RequestIDMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request_id = None
        for name, value in scope.get("headers", []):
            if name == b"x-request-id":
                request_id = value.decode()
                break
        if request_id is None:
            request_id = str(uuid.uuid4())

        scope["request_id"] = request_id
        start = time.time()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                extra = [
                    (b"x-request-id", request_id.encode()),
                    (b"x-response-time", f"{time.time() - start:.3f}".encode()),
                ]
                message["headers"] = headers + extra
            await send(message)

        await self.app(scope, receive, send_wrapper)


class RequestLoggingMiddleware:
    """Log every request with method, path, status, duration, client IP, and structured fields."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path = scope.get("path", "/")
        method = scope.get("method", "GET")
        client_ip = _get_client_ip(scope)
        request_id = scope.get("request_id", "")
        start = time.time()
        status_code = 0

        # Extract user_id from Authorization header if available
        headers = dict(scope.get("headers", []))
        user_id = ""
        auth_header = headers.get(b"authorization", b"").decode()
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                import base64
                import json as _json

                payload_b64 = token.split(".")[1]
                payload_b64 += "=" * (4 - len(payload_b64) % 4)
                payload = _json.loads(base64.urlsafe_b64decode(payload_b64))
                user_id = payload.get("sub", "")
            except Exception:
                pass

        tenant_id = headers.get(b"x-tenant-id", b"").decode()

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed = time.time() - start
            latency_ms = round(elapsed * 1000, 1)
            extra = {
                "http_method": method,
                "path": path,
                "status": status_code,
                "duration_ms": latency_ms,
                "latency_ms": latency_ms,
                "client_ip": client_ip,
                "resource": path,
            }
            extra.update(
                {
                    "request_id": request_id,
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                }
            )
            log_level = "warning" if elapsed > 1.0 else "info" if status_code < 500 else "error"
            getattr(logger, log_level)(
                "%s %s %d (%.1fms)" % (method, path, status_code, elapsed * 1000),
                extra=extra,
            )


class CsrfEnforcementMiddleware:
    """Enforce CSRF token validation on state-changing requests.

    Requires X-CSRF-Token header matching the csrf_token cookie on
    POST/PUT/PATCH/DELETE. Does **not** skip for bare ``X-API-Key`` or for
    ``request.state.api_key_authenticated`` (PROD-W5-001 / STORY-01-03 /
    Phase 0 criterion 1.3). Skips only testing mode (``SALESOS_TESTING=true``),
    public identity paths, and read-only methods (GET/HEAD/OPTIONS).
    """

    _STATE_CHANGING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

    _PUBLIC_PATHS = frozenset(
        {
            "/api/v1/identity/register",
            "/api/v1/identity/login",
            "/api/v1/identity/forgot-password",
            "/api/v1/identity/reset-password",
            "/api/v1/identity/refresh",
            "/csrf-token",
            # STORY-05-02 — Stripe signs body; CSRF cookie not applicable.
            "/api/v1/billing/stripe/webhook",
        }
    )

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        if os.environ.get("SALESOS_TESTING") == "true":
            return await self.app(scope, receive, send)

        method = scope.get("method", "GET")
        if method not in self._STATE_CHANGING_METHODS:
            return await self.app(scope, receive, send)

        path = scope.get("path", "")
        if path in self._PUBLIC_PATHS:
            return await self.app(scope, receive, send)

        headers = dict(scope.get("headers", []))
        cookie_header = headers.get(b"cookie", b"").decode()
        csrf_header = headers.get(b"x-csrf-token", b"").decode()

        cookie_csrf = ""
        for part in cookie_header.split("; "):
            if part.startswith("csrf_token="):
                cookie_csrf = part[len("csrf_token=") :]
                break

        if not csrf_header:
            response = JSONResponse(
                status_code=403,
                content={
                    "detail": "CSRF token missing. Include X-CSRF-Token header.",
                    "detail_ar": "رمز CSRF مطلوب. يرجى تضمين X-CSRF-Token في الترويسة.",
                },
            )
            await response(scope, receive, send)
            return

        if not cookie_csrf or csrf_header != cookie_csrf:
            response = JSONResponse(
                status_code=403,
                content={
                    "detail": "CSRF token mismatch. Obtain a fresh token from GET /csrf-token.",
                    "detail_ar": "رمز CSRF غير متطابق. احصل على رمز جديد من GET /csrf-token.",
                },
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
