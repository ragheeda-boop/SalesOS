"""STORY-06-02/06-04 — Tenant entitlement cache (Redis + memory).

TTL target <=60s so plan downgrades take effect without manual flush.
Plan-change paths must invalidate (correctness over performance).
Does not call DEC-085 set_config. Not Production GO.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from app.modules.admin.entitlements import (
    PlanEntitlements,
    entitlements_to_dict,
    parse_entitlements,
)

logger = logging.getLogger(__name__)

ENTITLEMENT_CACHE_TTL_MAX_SECONDS = 60
ENTITLEMENT_CACHE_TTL_DEFAULT_SECONDS = 60
ENTITLEMENT_CACHE_KEY_PREFIX = "salesos:entitlements:v1:"


class _RedisLike(Protocol):
    async def get(self, key: str) -> str | None: ...

    async def set(self, key: str, value: str, ttl: int = 60) -> None: ...

    async def delete(self, key: str) -> None: ...


@dataclass
class _MemoryEntry:
    payload: str
    expires_at: float


def clamp_entitlement_cache_ttl(ttl_seconds: int) -> int:
    try:
        ttl = int(ttl_seconds)
    except (TypeError, ValueError):
        ttl = ENTITLEMENT_CACHE_TTL_DEFAULT_SECONDS
    if ttl < 1:
        return 1
    if ttl > ENTITLEMENT_CACHE_TTL_MAX_SECONDS:
        return ENTITLEMENT_CACHE_TTL_MAX_SECONDS
    return ttl


def entitlement_cache_key(tenant_id: str) -> str:
    return f"{ENTITLEMENT_CACHE_KEY_PREFIX}{str(tenant_id).strip()}"


def serialize_entitlement_cache(
    entitlements: PlanEntitlements | dict[str, Any],
    meta: dict[str, Any],
) -> str:
    doc = (
        entitlements
        if isinstance(entitlements, PlanEntitlements)
        else parse_entitlements(entitlements)
    )
    body = {
        "entitlements": entitlements_to_dict(doc),
        "meta": dict(meta or {}),
    }
    return json.dumps(body, separators=(",", ":"), sort_keys=True)


def deserialize_entitlement_cache(
    raw: str,
) -> tuple[PlanEntitlements, dict[str, Any]] | None:
    try:
        data = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    ents_raw = data.get("entitlements")
    meta_raw = data.get("meta")
    meta: dict[str, Any] = dict(meta_raw) if isinstance(meta_raw, dict) else {}
    try:
        ents = parse_entitlements(ents_raw)
    except (ValueError, TypeError):
        return None
    return ents, meta


class EntitlementCache:
    def __init__(
        self,
        *,
        ttl_seconds: int = ENTITLEMENT_CACHE_TTL_DEFAULT_SECONDS,
        redis_client: _RedisLike | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.ttl_seconds = clamp_entitlement_cache_ttl(ttl_seconds)
        self._redis = redis_client
        self._clock = clock or time.monotonic
        self._memory: dict[str, _MemoryEntry] = {}

    async def get(self, tenant_id: str) -> tuple[PlanEntitlements, dict[str, Any]] | None:
        key = entitlement_cache_key(tenant_id)
        now = float(self._clock())
        mem = self._memory.get(key)
        if mem is not None:
            if mem.expires_at > now:
                parsed = deserialize_entitlement_cache(mem.payload)
                if parsed is not None:
                    ents, meta = parsed
                    meta = {**meta, "cache": "memory_hit"}
                    return ents, meta
            self._memory.pop(key, None)

        if self._redis is not None:
            try:
                raw = await self._redis.get(key)
            except Exception as exc:  # noqa: BLE001
                logger.warning("entitlement cache redis GET failed: %s", exc)
                raw = None
            if raw:
                parsed = deserialize_entitlement_cache(raw)
                if parsed is not None:
                    ents, meta = parsed
                    self._memory[key] = _MemoryEntry(
                        payload=raw, expires_at=now + float(self.ttl_seconds)
                    )
                    meta = {**meta, "cache": "redis_hit"}
                    return ents, meta
        return None

    async def set(
        self,
        tenant_id: str,
        entitlements: PlanEntitlements | dict[str, Any],
        meta: dict[str, Any],
    ) -> None:
        key = entitlement_cache_key(tenant_id)
        payload = serialize_entitlement_cache(entitlements, meta)
        now = float(self._clock())
        self._memory[key] = _MemoryEntry(payload=payload, expires_at=now + float(self.ttl_seconds))
        if self._redis is not None:
            try:
                await self._redis.set(key, payload, ttl=self.ttl_seconds)
            except Exception as exc:  # noqa: BLE001
                logger.warning("entitlement cache redis SET failed: %s", exc)

    async def invalidate(self, tenant_id: str) -> None:
        key = entitlement_cache_key(tenant_id)
        self._memory.pop(key, None)
        if self._redis is not None:
            try:
                await self._redis.delete(key)
            except Exception as exc:  # noqa: BLE001
                logger.warning("entitlement cache redis DEL failed: %s", exc)

    async def invalidate_all(self) -> None:
        self._memory.clear()


_cache: EntitlementCache | None = None


def get_entitlement_cache() -> EntitlementCache:
    global _cache
    if _cache is None:
        from app.config import settings

        redis_client: _RedisLike | None = None
        try:
            from app.common.redis_client import AsyncRedisClient

            redis_client = AsyncRedisClient()
        except Exception as exc:  # noqa: BLE001
            logger.warning("entitlement cache: redis client unavailable: %s", exc)
            redis_client = None
        ttl = int(getattr(settings, "entitlement_cache_ttl_seconds", 60) or 60)
        _cache = EntitlementCache(ttl_seconds=ttl, redis_client=redis_client)
    return _cache


def reset_entitlement_cache_for_tests(
    cache: EntitlementCache | None = None,
) -> None:
    global _cache
    _cache = cache


async def invalidate_entitlement_cache_for_tenant(tenant_id: str) -> None:
    await get_entitlement_cache().invalidate(str(tenant_id))


async def invalidate_all_entitlement_caches() -> None:
    await get_entitlement_cache().invalidate_all()
