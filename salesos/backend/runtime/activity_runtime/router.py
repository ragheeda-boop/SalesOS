"""Activity Runtime REST API.

Endpoints:
  POST /api/v1/activities/ingest        — Record one activity
  POST /api/v1/activities/ingest-batch  — Record multiple activities
  GET  /api/v1/activities               — Query activities with filters
  GET  /api/v1/activities/{entity_type}/{entity_id} — Activities for an entity
  GET  /api/v1/activities/by-actor/{actor}         — Activities by actor
  GET  /api/v1/activities/by-action/{action}       — Activities by action
  GET  /api/v1/activities/stats         — Aggregate activity stats
  GET  /api/v1/activities/metrics       — Runtime metrics
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.dependencies import get_current_tenant_id

router = APIRouter()


def _get_runtime(request: Request):
    rt = getattr(request.app.state, "activity_runtime", None)
    if not rt:
        raise HTTPException(status_code=503, detail="Activity Runtime not initialized")
    return rt


@router.post("/activities/ingest")
async def ingest_activity(
    request: Request,
    actor: str = Query(...),
    action: str = Query(...),
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    target_type: Optional[str] = Query(None),
    target_id: Optional[str] = Query(None),
    metadata: Optional[str] = Query(None, description="JSON string"),
    tenant_id: str = Depends(get_current_tenant_id),
):
    import json
    rt = _get_runtime(request)
    record = await rt.ingest(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        target_type=target_type,
        target_id=target_id,
        metadata=json.loads(metadata) if metadata else None,
        tenant_id=tenant_id,
    )
    return {"id": record.id, "timestamp": record.timestamp.isoformat()}


@router.post("/activities/ingest-batch")
async def ingest_batch(
    request: Request,
    records: list[dict],
    tenant_id: str = Depends(get_current_tenant_id),
):
    rt = _get_runtime(request)
    enriched = [{**r, "tenant_id": r.get("tenant_id", tenant_id)} for r in records]
    results = await rt.ingest_batch(enriched)
    return {
        "ingested": len(results),
        "ids": [r.id for r in results],
    }


@router.get("/activities")
async def query_activities(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    actor: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    target_type: Optional[str] = Query(None),
    target_id: Optional[str] = Query(None),
    since: Optional[datetime] = Query(None),
    until: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    rt = _get_runtime(request)
    items, total = await rt.query(
        tenant_id=tenant_id,
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        target_type=target_type,
        target_id=target_id,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/activities/{entity_type}/{entity_id}")
async def get_entity_activities(
    entity_type: str,
    entity_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    rt = _get_runtime(request)
    items, total = await rt.get_by_entity(
        entity_type=entity_type,
        entity_id=entity_id,
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )
    return {"entity_type": entity_type, "entity_id": entity_id, "items": items, "total": total}


@router.get("/activities/by-actor/{actor}")
async def get_actor_activities(
    actor: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    rt = _get_runtime(request)
    items, total = await rt.get_by_actor(
        actor=actor,
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )
    return {"actor": actor, "items": items, "total": total}


@router.get("/activities/by-action/{action}")
async def get_action_activities(
    action: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    rt = _get_runtime(request)
    items, total = await rt.get_by_action(
        action=action,
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )
    return {"action": action, "items": items, "total": total}


@router.get("/activities/stats")
async def activity_stats(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    since: Optional[datetime] = Query(None),
    until: Optional[datetime] = Query(None),
):
    rt = _get_runtime(request)
    return await rt.get_stats(tenant_id=tenant_id, since=since, until=until)


@router.get("/activities/metrics")
async def activity_metrics(request: Request):
    rt = getattr(request.app.state, "activity_runtime", None)
    if not rt:
        return {"status": "not_initialized"}
    return rt.metrics.snapshot()
