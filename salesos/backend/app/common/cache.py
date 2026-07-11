"""Redis-backed caching decorator for FastAPI dependencies."""
import functools
import hashlib
import json
import logging
from typing import Any, Callable

from app.common.redis_client import AsyncRedisClient

logger = logging.getLogger(__name__)

_cache_client = AsyncRedisClient()

EXCLUDE_KEYS = {"db", "request", "_rbac"}


def make_cache_key(tenant_id: str, resource: str, kwargs: dict) -> str:
    """Build a deterministic Redis cache key from a tenant, resource name, and kwargs."""
    payload = {k: v for k, v in kwargs.items() if k not in EXCLUDE_KEYS and not k.startswith("_")}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]
    return f"{tenant_id}:{resource}:{digest}"


def cached(resource: str, ttl: int = 60) -> Callable:
    """Cache FastAPI dependency results in Redis.

    The decorated function must accept ``tenant_id`` as a keyword argument
    (typically injected via ``Depends(get_current_tenant_id)``).

    Falls back to executing the function normally when Redis is unavailable.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            tenant_id = kwargs.get("tenant_id")
            if not tenant_id:
                return await func(*args, **kwargs)

            cache_key = make_cache_key(tenant_id, resource, kwargs)

            cached_str = await _cache_client.get(cache_key)
            if cached_str is not None:
                try:
                    return json.loads(cached_str)
                except (json.JSONDecodeError, TypeError):
                    pass

            result = await func(*args, **kwargs)

            try:
                await _cache_client.set(cache_key, json.dumps(result, default=str), ttl=ttl)
            except Exception:
                pass

            return result
        return wrapper
    return decorator
