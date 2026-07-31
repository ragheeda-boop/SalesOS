"""Shared OAuth CSRF state store — Redis-backed with in-memory fallback.

Used by SSO and Communication Hub Google OAuth so multi-instance deploys
do not break the authorize→callback round-trip.
"""

from __future__ import annotations

import contextlib
import json
import threading
import time
from typing import Any

from app.config import settings

_DEFAULT_TTL = 600
_KEY_PREFIX = "oauth_state:"

# In-memory fallback (tests + Redis unavailable)
_MEMORY: dict[str, tuple[Any, float]] = {}
_LOCK = threading.Lock()

_redis: Any | None = None
_redis_checked = False
_redis_lock = threading.Lock()


def _get_sync_redis():
    """Lazy sync Redis client (not asyncio) for sync OAuth helpers."""
    global _redis, _redis_checked
    if _redis_checked:
        return _redis
    with _redis_lock:
        if _redis_checked:
            return _redis
        _redis_checked = True
        try:
            import redis as redis_sync

            client = redis_sync.Redis.from_url(
                settings.redis_url,
                socket_connect_timeout=getattr(settings, "redis_socket_connect_timeout", 2),
                socket_timeout=getattr(settings, "redis_socket_timeout", 2),
                decode_responses=True,
            )
            client.ping()
            _redis = client
        except Exception:
            _redis = None
        return _redis


def _redis_key(key: str) -> str:
    return f"{_KEY_PREFIX}{key}"


def store_oauth_state(key: str, value: Any, ttl: int = _DEFAULT_TTL) -> None:
    """Store OAuth state. ``value`` may be str or JSON-serializable dict."""
    expiry = time.time() + ttl
    # Always mirror to memory so local cleanup/tests work even when Redis is up.
    with _LOCK:
        _MEMORY[key] = (value, expiry)
    payload = json.dumps({"v": value}, separators=(",", ":"), default=str)
    r = _get_sync_redis()
    if r is not None:
        with contextlib.suppress(Exception):
            r.setex(_redis_key(key), ttl, payload)


def get_oauth_state(key: str, *, consume: bool = False) -> Any | None:
    """Fetch OAuth state. If ``consume``, delete after read (one-time use)."""
    r = _get_sync_redis()
    if r is not None:
        try:
            rkey = _redis_key(key)
            raw = r.get(rkey)
            if raw is not None:
                if consume:
                    r.delete(rkey)
                    with _LOCK:
                        _MEMORY.pop(key, None)
                data = json.loads(raw)
                return data.get("v")
        except Exception:
            pass
    return _memory_get(key, consume=consume)


def _memory_get(key: str, *, consume: bool) -> Any | None:
    with _LOCK:
        entry = _MEMORY.get(key)
        if entry is None:
            return None
        value, expiry = entry
        if time.time() > expiry:
            _MEMORY.pop(key, None)
            return None
        if consume:
            _MEMORY.pop(key, None)
        return value


def clear_oauth_state_memory() -> None:
    """Test helper — clear in-memory fallback only."""
    with _LOCK:
        _MEMORY.clear()


def memory_store_snapshot() -> dict[str, Any]:
    """Test helper — shallow copy of live (non-expired) memory entries."""
    now = time.time()
    with _LOCK:
        return {k: v for k, (v, exp) in _MEMORY.items() if exp >= now}
