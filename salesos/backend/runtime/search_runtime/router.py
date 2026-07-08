"""Search Runtime REST API.

Endpoints:
  GET /api/v1/search                     — Unified search (hybrid default)
  GET /api/v1/search/suggest             — Auto-complete suggestions
  GET /api/v1/search/similar/{company_id} — Semantic similarity
  GET /api/v1/search/metrics             — Search engine metrics
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.dependencies import get_current_tenant_id
from runtime.search_runtime import SearchStrategy

router = APIRouter()


@router.get("/search")
async def search(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    q: str = Query(..., min_length=1, description="Search query"),
    strategy: str = Query("hybrid", pattern="^(fulltext|semantic|graph|hybrid)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_facets: bool = Query(False),
    city: Optional[str] = None,
    region: Optional[str] = None,
    industry: Optional[str] = None,
    status: Optional[str] = None,
):
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

    result = await sr.search(
        query=q,
        tenant_id=tenant_id,
        strategy=SearchStrategy(strategy),
        filters=filters or None,
        limit=limit,
        offset=offset,
        include_facets=include_facets,
    )
    return {
        "query": q,
        "strategy": strategy,
        "total": result.total,
        "took_ms": round(result.took_ms, 2),
        "items": [item.to_dict() for item in result.items],
        "facets": result.facets,
        "suggestions": result.suggestions,
    }


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
