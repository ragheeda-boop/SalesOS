from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.dependencies import require_role_dep

# DEC-159: raw key-based get/set/delete plus a wildcard flush() is a wider
# blast radius than most per-tenant endpoints (any caller-supplied key,
# cache-wide flush by pattern) — gated at "admin" role, not just any
# authenticated user. require_role_dep("admin") already depends on
# verify_token transitively (via get_current_user_role), so no separate
# verify_token dependency is needed here.
router = APIRouter(
    prefix="/api/v1/cache", tags=["Cache"], dependencies=[Depends(require_role_dep("admin"))]
)


class CacheEntry(BaseModel):
    key: str
    value: str
    ttl: int = 300


class CacheDeleteRequest(BaseModel):
    keys: list[str]


class CacheFlushRequest(BaseModel):
    pattern: str = "*"


@router.get("/health")
async def cache_health(request: Request):
    cache = getattr(request.app.state, "cache", None)
    if cache is None:
        raise HTTPException(status_code=503, detail="Cache service not available")
    ok = await cache.health()
    return {"status": "connected" if ok else "unavailable"}


@router.get("/{key}")
async def get_cache(key: str, request: Request):
    cache = getattr(request.app.state, "cache", None)
    if cache is None:
        raise HTTPException(status_code=503, detail="Cache service not available")
    value = await cache.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"key": key, "value": value}


@router.post("/set")
async def set_cache(entry: CacheEntry, request: Request):
    cache = getattr(request.app.state, "cache", None)
    if cache is None:
        raise HTTPException(status_code=503, detail="Cache service not available")
    await cache.set(entry.key, entry.value, ttl_seconds=entry.ttl)
    return {"key": entry.key, "ttl": entry.ttl}


@router.delete("/{key}")
async def delete_cache(key: str, request: Request):
    cache = getattr(request.app.state, "cache", None)
    if cache is None:
        raise HTTPException(status_code=503, detail="Cache service not available")
    await cache.delete(key)
    return {"deleted": key}


@router.post("/flush")
async def flush_cache(req: CacheFlushRequest, request: Request):
    cache = getattr(request.app.state, "cache", None)
    if cache is None:
        raise HTTPException(status_code=503, detail="Cache service not available")
    await cache.delete_pattern(req.pattern)
    return {"flushed": True, "pattern": req.pattern}
