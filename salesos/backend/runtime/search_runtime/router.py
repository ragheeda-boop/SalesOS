"""Search Runtime REST API.

Endpoints:
  GET /api/v1/search                     — Unified search (hybrid default)
  GET /api/v1/search/suggest             — Auto-complete suggestions
  GET /api/v1/search/similar/{company_id} — Semantic similarity
  GET /api/v1/search/metrics             — Search engine metrics
  POST /api/v1/search/ai                 — AI-powered semantic search
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from app.dependencies import get_current_tenant_id, verify_token
from runtime.search_runtime import SearchStrategy

router = APIRouter(dependencies=[Depends(verify_token)])


@router.get("/search")
async def search(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    q: str = Query(..., min_length=1, description="Search query"),
    strategy: str = Query("hybrid", pattern="^(fulltext|semantic|graph|hybrid)$"),
    limit: int = Query(20, ge=1, le=50),
    cursor: str | None = Query(None, description="Keyset cursor for pagination"),
    include_facets: bool = Query(False),
    city: Optional[str] = None,
    region: Optional[str] = None,
    industry: Optional[str] = None,
    status: Optional[str] = None,
):
    from sdk.pagination import decode_cursor, encode_cursor
    import hashlib, json as _json

    sr = getattr(request.app.state, "search_runtime", None)
    if not sr:
        raise HTTPException(status_code=503, detail="Search Runtime not initialized")

    filters = {}
    if city:
        filters["city"] = city
    if region:
        filters["region"] = region
    if industry:
        filters["industry"] = industry
    if status:
        filters["status"] = status

    cache = getattr(request.app.state, "cache", None)
    if cache:
        cache_payload = _json.dumps({"q": q, "strategy": strategy, "limit": limit, "cursor": cursor, "filters": filters, "facets": include_facets}, sort_keys=True)
        ck = f"search:{hashlib.md5(cache_payload.encode()).hexdigest()}"
        cached = await cache.get(ck)
        if cached:
            return cached

    result = await sr.search(
        query=q,
        tenant_id=tenant_id,
        strategy=SearchStrategy(strategy),
        filters=filters or None,
        limit=limit + 1,
        offset=0,
        include_facets=include_facets,
    )

    has_next = len(result.items) > limit
    if has_next:
        result.items = result.items[:limit]

    next_cursor = None
    if has_next and result.items:
        last = result.items[-1]
        created_at = getattr(last, "created_at", None) or datetime.utcnow().isoformat()
        next_cursor = encode_cursor(str(last.id), created_at)

    response = {
        "query": q,
        "strategy": strategy,
        "total": result.total,
        "took_ms": round(result.took_ms, 2),
        "items": [item.to_dict() for item in result.items],
        "facets": result.facets,
        "suggestions": result.suggestions,
        "next_cursor": next_cursor,
        "has_next": has_next,
    }

    if cache:
        await cache.set(ck, response, ttl_seconds=30)

    return response


@router.get("/search/suggest")
async def suggest(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    q: str = Query(..., min_length=1),
    field: str = Query("name_ar"),
    limit: int = Query(10, ge=1, le=50),
):
    sr = getattr(request.app.state, "search_runtime", None)
    if not sr:
        raise HTTPException(status_code=503, detail="Search Runtime not initialized")
    suggestions = await sr.suggest(q, tenant_id, field, limit)
    return {"query": q, "field": field, "suggestions": suggestions}


@router.get("/search/similar/{company_id}")
async def similar_to(
    company_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    limit: int = Query(10, ge=1, le=50),
):
    sr = getattr(request.app.state, "search_runtime", None)
    if not sr:
        raise HTTPException(status_code=503, detail="Search Runtime not initialized")
    result = await sr.similar_to(company_id, tenant_id, limit)
    return {
        "company_id": company_id,
        "items": [item.to_dict() for item in result.items],
        "total": result.total,
    }


@router.get("/search/metrics")
async def search_metrics(request: Request, tenant_id: str = Depends(get_current_tenant_id)):
    sr = getattr(request.app.state, "search_runtime", None)
    if not sr:
        return {"status": "not_initialized"}
    return sr.metrics.snapshot()


class AISearchRequest(BaseModel):
    text: str
    limit: int = 10


@router.post("/search/ai")
async def ai_search(
    body: AISearchRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    sr = getattr(request.app.state, "search_runtime", None)
    if not sr:
        raise HTTPException(status_code=503, detail="Search Runtime not initialized")

    try:
        result = await sr.search(
            query=body.text,
            tenant_id=tenant_id,
            strategy=SearchStrategy.SEMANTIC,
            limit=body.limit,
        )
        return {
            "query": body.text,
            "strategy": "semantic",
            "total": result.total,
            "took_ms": round(result.took_ms, 2),
            "items": [item.to_dict() for item in result.items],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI search failed: {exc}")
