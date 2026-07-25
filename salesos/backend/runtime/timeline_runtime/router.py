"""Universal Timeline Runtime REST API.

Endpoints:
  GET  /api/v1/timeline/{entity_type}/{entity_id}      — Get timeline for entity
  GET  /api/v1/timeline/{entity_type}/{entity_id}/summary — Timeline stats
  GET  /api/v1/timeline/{entity_type}                  — Recent timelines across entities
  GET  /api/v1/timeline/metrics                        — Timeline engine metrics
"""

from datetime import datetime
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.dependencies import get_current_tenant_id, verify_token

router = APIRouter(dependencies=[Depends(verify_token)])


def _get_runtime(request: Request):
    tl = getattr(request.app.state, "timeline_runtime", None)
    if not tl:
        raise HTTPException(status_code=503, detail="Timeline Runtime not initialized")
    return tl


@router.get("/timeline/{entity_type}/{entity_id}")
async def get_timeline(
    entity_type: str,
    entity_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    event_types: Optional[str] = Query(None, description="Comma-separated event types to filter (e.g. email,call,meeting)"),
    date_from: Optional[datetime] = Query(None, alias="date_from", description="Start date for filtering"),
    date_to: Optional[datetime] = Query(None, alias="date_to", description="End date for filtering"),
    domain: Optional[str] = Query(None, description="Source domain filter (e.g. crm, enrichment)"),
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = Query(50, ge=1, le=200),
    cursor: Optional[str] = Query(None, description="Keyset cursor for pagination"),
):
    tl = getattr(request.app.state, "timeline_runtime", None)
    if not tl:
        raise HTTPException(status_code=503, detail="Timeline Runtime not initialized")

    from sdk.pagination import encode_cursor

    types_list: list[str] = [t.strip() for t in event_types.split(",") if t.strip()] if event_types else []
    effective_since = date_from or since
    effective_until = date_to or until
    entries, total = await tl.get_timeline(
        entity_type=entity_type,
        entity_id=entity_id,
        event_types=types_list,
        since=effective_since,
        until=effective_until,
        domain=domain,
        limit=limit + 1,
        offset=0,
        cursor=cursor,
    )

    has_next = len(entries) > limit
    if has_next:
        entries = entries[:limit]

    next_cursor = None
    if has_next and entries:
        last = entries[-1]
        next_cursor = encode_cursor(str(last.get("id", "")), last.get("created_at"))

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "total": total,
        "entries": entries,
        "next_cursor": next_cursor,
        "has_next": has_next,
    }


@router.get("/timeline/{entity_type}/{entity_id}/summary")
async def timeline_summary(
    entity_type: str,
    entity_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    domain: Optional[str] = Query(None, description="Source domain filter (e.g. crm, enrichment)"),
):
    tl = _get_runtime(request)
    return await tl.get_timeline_summary(entity_type, entity_id, domain=domain)


@router.get("/timeline/{entity_type}")
async def get_entity_timelines(
    entity_type: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    domain: Optional[str] = Query(None, description="Source domain filter (e.g. crm, enrichment)"),
    date_from: Optional[datetime] = Query(None, alias="date_from"),
    date_to: Optional[datetime] = Query(None, alias="date_to"),
    limit: int = Query(20, ge=1, le=100),
):
    tl = _get_runtime(request)
    entries = await tl.get_entity_timelines(
        tenant_id, entity_type, limit, domain=domain,
        since=date_from, until=date_to,
    )
    return {"entity_type": entity_type, "entries": entries}


@router.get("/timeline/metrics")
async def timeline_metrics(request: Request, tenant_id: str = Depends(get_current_tenant_id)):
    tl = getattr(request.app.state, "timeline_runtime", None)
    if not tl:
        return {"status": "not_initialized"}
    return tl.metrics.snapshot()
