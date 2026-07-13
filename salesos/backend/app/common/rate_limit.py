"""Per-user rate limiting for API endpoints — sliding window, Redis-backed with in-memory fallback."""
import threading
import time
from typing import Callable

from fastapi import Depends, HTTPException, Request

from app.config import settings
from app.dependencies import get_current_tenant_id


_store: dict[str, list[float]] = {}
_lock = threading.Lock()
_CLEANUP_INTERVAL = settings.rate_limit_cleanup_interval
_last_cleanup = time.time()

_redis: object | None = None
_redis_checked = False
_redis_lock = threading.Lock()


def _get_redis():
    global _redis, _redis_checked
    if _redis_checked:
        return _redis
    with _redis_lock:
        if _redis_checked:
            return _redis
        _redis_checked = True
        try:
            import redis.asyncio as aioredis
            _redis = aioredis.Redis.from_url(
                settings.redis_url,
                socket_connect_timeout=settings.redis_socket_connect_timeout,
                socket_timeout=settings.redis_socket_timeout,
            )
        except Exception:
            _redis = None
        return _redis


def _cleanup(now: float) -> None:
    """Remove entries older than 1 hour."""
    cutoff = now - 3600
    with _lock:
        empty_keys = [k for k, v in _store.items() if not v or v[-1] < cutoff]
        for k in empty_keys:
            del _store[k]


async def _check_rate_limit_redis(key: str, limit: int, window: int) -> float | None:
    r = _get_redis()
    if r is None:
        return None  # fall through to in-memory
    try:
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, window)
        if count > limit:
            ttl = await r.ttl(key)
            return max(float(ttl), 1.0) if ttl > 0 else float(window)
        return None
    except Exception:
        return None  # fall through to in-memory


def _check_rate_limit_in_memory(key: str, limit: int, window: int) -> float | None:
    """Check rate limit. Returns retry_after seconds if exceeded, None if ok."""
    now = time.time()

    global _last_cleanup
    if now - _last_cleanup > _CLEANUP_INTERVAL:
        _cleanup(now)
        _last_cleanup = now

    cutoff = now - window
    with _lock:
        if key not in _store:
            _store[key] = []
        timestamps = _store[key]
        _store[key] = [t for t in timestamps if t > cutoff]
        timestamps = _store[key]

        if len(timestamps) >= limit:
            oldest = timestamps[0]
            retry_after = window - (now - oldest)
            return max(retry_after, 1.0)

        timestamps.append(now)
        return None


def rate_limit_dep(resource: str, limit: int, window: int = 60) -> Callable:
    """Factory returning a FastAPI dependency that enforces per-user rate limiting.

    Uses Redis when available with graceful in-memory fallback.
    """

    async def _rate_limit(
        request: Request,
        tenant_id: str = Depends(get_current_tenant_id),
    ):
        user_id = getattr(request.state, "user_id", "anonymous")
        key = f"ratelimit:{tenant_id}:{user_id}:{resource}"

        retry_after = await _check_rate_limit_redis(key, limit, window)
        if retry_after is None:  # Redis unavailable — fall back
            retry_after = _check_rate_limit_in_memory(key, limit, window)

        if retry_after is not None:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded for {resource}",
                headers={"Retry-After": str(int(retry_after))},
            )

    return _rate_limit
