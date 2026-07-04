import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from sdk.telemetry import trace_span


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter (per IP, per path).

    For production, replace with Redis-based rate limiting.
    """

    def __init__(self, app, rate: int = 60, window: int = 60):
        super().__init__(app)
        self.rate = rate
        self.window = window
        self._requests: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.url.path}"

        now = time.time()
        window_start = now - self.window
        timestamps = self._requests.get(key, [])
        timestamps = [t for t in timestamps if t > window_start]

        if len(timestamps) >= self.rate:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests", "retry_after": self.window},
            )

        timestamps.append(now)
        self._requests[key] = timestamps
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        start = time.time()
        response = await call_next(request)
        elapsed = time.time() - start

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{elapsed:.3f}s"

        return response


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        async with trace_span(
            "http.request",
            attributes={"http.method": method, "http.path": path},
        ):
            start = time.time()
            response = await call_next(request)
            elapsed = time.time() - start

        if elapsed > 1.0:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning("Slow request: %s %s took %.2fs", method, path, elapsed)

        return response
