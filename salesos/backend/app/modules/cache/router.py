from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.dependencies import verify_token

router = APIRouter(prefix="/api/v1/cache", tags=["Cache"], dependencies=[Depends(verify_token)])


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
    await cache.set(entry.key, entry.value, ttl=entry.ttl)
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
    await cache.flush(pattern=req.pattern)
    return {"flushed": True, "pattern": req.pattern}
