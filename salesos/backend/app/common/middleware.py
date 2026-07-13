import logging
import time
import uuid

from fastapi import Request
from starlette.responses import JSONResponse

from app.config import settings

logger = logging.getLogger(__name__)


def _get_client_ip(scope: dict) -> str:
    """Extract client IP from request scope, handling proxies."""
    headers = dict(scope.get("headers", []))
    for header_name, header_bytes in [(b"x-forwarded-for", b"x-forwarded-for"), (b"x-real-ip", b"x-real-ip")]:
        if header_bytes in headers:
            val = headers[header_bytes].decode().split(",")[0].strip()
            if val:
                return val
    client = scope.get("client")
    return client[0] if client else "unknown"


_SEARCH_ENRICH_PREFIXES = ("/api/v1/search", "/api/v1/entity-resolution", "/api/v1/data-fabric")


class RateLimitMiddleware:
    """Per-IP sliding-window rate limiter with tiered limits.

    Redis-backed when available, in-memory fallback for dev/staging.
    Enforces global per-IP limits with different tiers for path categories.
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

    def _select_tier(self, path: str, auth_header: str) -> int:
        """Return the per-minute rate limit for the given request path."""
        health_paths = ("/health", "/health/live", "/health/ready")
        if path in health_paths or path.startswith(("/docs", "/redoc")):
            return settings.rate_limit_health
        if path.startswith("/api/v1/identity"):
            return settings.rate_limit_identity
        if any(path.startswith(p) for p in _SEARCH_ENRICH_PREFIXES):
            return settings.rate_limit_search
        if path.startswith("/api/v1/"):
            if auth_header.startswith("Bearer "):
                return settings.rate_limit_authenticated
            return settings.rate_limit_anonymous
        return settings.rate_limit_default

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope, receive)
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        auth_header = request.headers.get("authorization", "")
        tier_rate = self._select_tier(path, auth_header)
        now = time.time()

        # Key by IP only — prevents bypass via path variation
        key = f"ratelimit:{client_ip}"

        # --- Redis path ---
        if self._redis:
            try:
                count = await self._redis.incr(key)
                if count == 1:
                    await self._redis.expire(key, self.window)
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

        if len(timestamps) >= tier_rate:
            retry_after = max(int(self.window - (now - timestamps[0])), 1)
            response = JSONResponse(
                status_code=429,
                content={"detail": "Too many requests", "retry_after": retry_after},
                headers={"Retry-After": str(retry_after)},
            )
            await response(scope, receive, send)
            return

        timestamps.append(now)
        self._local[key] = timestamps
        await self.app(scope, receive, send)


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
                import json as _json
                import base64
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
            extra.update({
                "request_id": request_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
            })
            log_level = "warning" if elapsed > 1.0 else "info" if status_code < 500 else "error"
            getattr(logger, log_level)(
                "%s %s %d (%.1fms)" % (method, path, status_code, elapsed * 1000),
                extra=extra,
            )


class CsrfEnforcementMiddleware:
    """Enforce CSRF token validation on state-changing requests.

    Requires X-CSRF-Token header matching the csrf_token cookie on
    POST/PUT/PATCH/DELETE. Skips for API key authenticated requests
    and read-only methods (GET/HEAD/OPTIONS).
    """

    _STATE_CHANGING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        method = scope.get("method", "GET")
        if method not in self._STATE_CHANGING_METHODS:
            return await self.app(scope, receive, send)

        headers = dict(scope.get("headers", []))
        cookie_header = headers.get(b"cookie", b"").decode()
        csrf_header = headers.get(b"x-csrf-token", b"").decode()
        api_key_header = headers.get(b"x-api-key", b"").decode()

        if api_key_header:
            return await self.app(scope, receive, send)

        cookie_csrf = ""
        for part in cookie_header.split("; "):
            if part.startswith("csrf_token="):
                cookie_csrf = part[len("csrf_token="):]
                break

        if not csrf_header:
            response = JSONResponse(
                status_code=403,
                content={
                    "detail": "CSRF token missing. Include X-CSRF-Token header.",
                    "detail_ar": "رمز CSRF مطلوب. يرجى تضمين X-CSRF-Token في الترويسة."
                },
            )
            await response(scope, receive, send)
            return

        if not cookie_csrf or csrf_header != cookie_csrf:
            response = JSONResponse(
                status_code=403,
                content={
                    "detail": "CSRF token mismatch. Obtain a fresh token from GET /csrf-token.",
                    "detail_ar": "رمز CSRF غير متطابق. احصل على رمز جديد من GET /csrf-token."
                },
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
