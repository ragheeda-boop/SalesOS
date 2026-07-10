import logging
import time
import uuid

from fastapi import Request
from starlette.responses import JSONResponse

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

class RateLimitMiddleware:
    """Rate limiter — Redis-backed in production, in-memory fallback for dev."""

    def __init__(self, app, rate: int = 60, window: int = 60, redis_client=None):
        self.app = app
        self.rate = rate
        self.window = window
        self._redis = redis_client
        self._local: dict[str, list[float]] = {}

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope, receive)
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        if path == "/health" or path.startswith("/docs") or path.startswith("/redoc"):
            tier_rate = 120
        elif path.startswith("/api/v1/identity"):
            tier_rate = 10
        elif path.startswith("/api/v1/"):
            auth = request.headers.get("authorization", "")
            tier_rate = 60 if auth.startswith("Bearer ") else 20
        else:
            tier_rate = 60

        key = f"ratelimit:{client_ip}:{path}"
        now = time.time()

        if self._redis:
            try:
                count = await self._redis.incr(key)
                if count == 1:
                    await self._redis.expire(key, self.window)
                if count > tier_rate:
                    response = JSONResponse(
                        status_code=429,
                        content={"detail": "Too many requests", "retry_after": self.window},
                    )
                    await response(scope, receive, send)
                    return
                await self.app(scope, receive, send)
                return
            except Exception:
                pass

        window_start = now - self.window
        timestamps = self._local.get(key, [])
        timestamps = [t for t in timestamps if t > window_start]

        if len(timestamps) >= tier_rate:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Too many requests", "retry_after": self.window},
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
    """Log every request with method, path, status, duration, and client IP."""

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

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed = time.time() - start
            extra = {
                "http_method": method,
                "path": path,
                "status": status_code,
                "duration_ms": round(elapsed * 1000, 1),
                "client_ip": client_ip,
            }
            log_level = "warning" if elapsed > 1.0 else "info" if status_code < 500 else "error"
            getattr(logger, log_level)(
                "%s %s %d (%.1fms)" % (method, path, status_code, elapsed * 1000),
                extra={"request_id": request_id, **extra},
            )
