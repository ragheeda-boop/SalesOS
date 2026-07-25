"""Rate limiting middleware for Employee 360 APIs.

Protects OAuth endpoints, webhooks, and AI endpoints from abuse.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, HTTPException


class RateLimiter:
    """Simple in-memory rate limiter. For production, use Redis-backed implementation."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self._max = max_requests
        self._window = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._cleanup_at = time.time() + 3600

    def _cleanup(self) -> None:
        now = time.time()
        if now < self._cleanup_at:
            return
        self._cleanup_at = now + 3600
        for key in list(self._buckets.keys()):
            self._buckets[key] = [t for t in self._buckets[key] if t > now - self._window]
            if not self._buckets[key]:
                del self._buckets[key]

    def check(self, key: str) -> bool:
        """Returns True if request is allowed, False if rate limited."""
        self._cleanup()
        now = time.time()
        bucket = self._buckets[key]
        bucket = [t for t in bucket if t > now - self._window]
        self._buckets[key] = bucket
        if len(bucket) >= self._max:
            return False
        bucket.append(now)
        return True

    def remaining(self, key: str) -> int:
        bucket = self._buckets.get(key, [])
        now = time.time()
        bucket = [t for t in bucket if t > now - self._window]
        return max(0, self._max - len(bucket))


# Pre-configured limiters
oauth_rate_limiter = RateLimiter(max_requests=20, window_seconds=60)    # OAuth endpoints
ai_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)       # AI completions
webhook_rate_limiter = RateLimiter(max_requests=60, window_seconds=60)  # Webhook handlers
sync_rate_limiter = RateLimiter(max_requests=5, window_seconds=300)     # Manual sync triggers


async def rate_limit_oauth(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    if not oauth_rate_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Too many OAuth requests. Try again later.")


async def rate_limit_ai(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    if not ai_rate_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="AI request limit reached. Try again in 60 seconds.")


async def rate_limit_webhook(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    if not webhook_rate_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Webhook rate limit reached.")


def get_rate_limit_headers(limiter: RateLimiter, key: str) -> dict[str, str]:
    return {
        "X-RateLimit-Limit": str(limiter._max),
        "X-RateLimit-Remaining": str(limiter.remaining(key)),
        "X-RateLimit-Reset": str(int(time.time() + limiter._window)),
    }
