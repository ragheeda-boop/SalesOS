"""Per-user rate limiting for API endpoints — sliding window in-memory."""
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


def _cleanup(now: float) -> None:
    """Remove entries older than 1 hour."""
    cutoff = now - 3600
    with _lock:
        empty_keys = [k for k, v in _store.items() if not v or v[-1] < cutoff]
        for k in empty_keys:
            del _store[k]


def _check_rate_limit(key: str, limit: int, window: int) -> float | None:
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
        # Prune stale entries
        _store[key] = [t for t in timestamps if t > cutoff]
        timestamps = _store[key]

        if len(timestamps) >= limit:
            oldest = timestamps[0]
            retry_after = window - (now - oldest)
            return max(retry_after, 1.0)

        timestamps.append(now)
        return None


def rate_limit_dep(resource: str, limit: int, window: int = 60) -> Callable:
    """Factory returning a FastAPI dependency that enforces per-user rate limiting."""

    async def _rate_limit(
        request: Request,
        tenant_id: str = Depends(get_current_tenant_id),
    ):
        # Extract user_id from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", "anonymous")
        key = f"{tenant_id}:{user_id}:{resource}"

        retry_after = _check_rate_limit(key, limit, window)
        if retry_after is not None:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded for {resource}",
                headers={"Retry-After": str(int(retry_after))},
            )

    return _rate_limit
