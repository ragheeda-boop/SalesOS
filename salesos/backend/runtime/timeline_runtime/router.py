"""Universal Timeline Runtime REST API.

Endpoints:
  GET  /api/v1/timeline/{entity_type}/{entity_id}      — Get timeline for entity
  GET  /api/v1/timeline/{entity_type}/{entity_id}/summary — Timeline stats
  GET  /api/v1/timeline/{entity_type}                  — Recent timelines across entities
  GET  /api/v1/timeline/metrics                        — Timeline engine metrics
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.dependencies import get_current_tenant_id

router = APIRouter()


@router.get("/timeline/{entity_type}/{entity_id}")
async def get_timeline(
    entity_type: str,
    entity_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    event_types: Optional[str] = Query(None, description="Comma-separated event types to filter"),
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    tl = getattr(request.app.state, "timeline_runtime", None)
    if not tl:
        raise HTTPException(status_code=503, detail="Timeline Runtime not initialized")

    types_list = [t.strip() for t in event_types.split(",")] if event_types else None
    entries = await tl.get_timeline(
        entity_type=entity_type,
        entity_id=entity_id,
        event_types=types_list,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "total": len(entries),
        "entries": entries,
    }


@router.get("/timeline/{entity_type}/{entity_id}/summary")
async def timeline_summary(
    entity_type: str,
    entity_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    tl = getattr(request.app.state, "timeline_runtime", None)
    if not tl:
        raise HTTPException(status_code=503, detail="Timeline Runtime not initialized")
    return await tl.get_timeline_summary(entity_type, entity_id)


@router.get("/timeline/{entity_type}")
async def get_entity_timelines(
    entity_type: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    limit: int = Query(20, ge=1, le=100),
):
    tl = getattr(request.app.state, "timeline_runtime", None)
    if not tl:
        raise HTTPException(status_code=503, detail="Timeline Runtime not initialized")
    entries = await tl.get_entity_timelines(tenant_id, entity_type, limit)
    return {"entity_type": entity_type, "entries": entries}


@router.get("/timeline/metrics")
async def timeline_metrics(request: Request):
    tl = getattr(request.app.state, "timeline_runtime", None)
    if not tl:
        return {"status": "not_initialized"}
    return tl.metrics.snapshot()
