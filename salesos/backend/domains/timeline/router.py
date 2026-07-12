"""Timeline Domain REST API — proper domain router using TimelineService.

Endpoints:
  GET    /api/v1/timeline/entity/{entityType}/{entityId} — Get timeline for entity
  GET    /api/v1/timeline/recent                         — Get recent timeline for tenant
  POST   /api/v1/timeline/events                         — Create timeline event
  GET    /api/v1/timeline/search                         — Search timeline events
  GET    /api/v1/timeline/entity/{entityType}/{entityId}/summary — Timeline summary
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.dependencies import get_current_tenant_id
from domains.timeline.schemas import (
    ActorSchema,
    TargetSchema,
    TimelineEventCreate,
    TimelineEventResponse,
    TimelineSearchParams,
    TimelineSearchResponse,
    TimelineSummaryResponse,
)
from domains.timeline.service import TimelineService
from domains.timeline.contracts.models import (
    ActivityOutcome,
    ActivityType,
    Actor,
    Target,
    TimelineEvent,
)
from domains.timeline.contracts.repository import TimelineQuery

router = APIRouter()


def _get_service(request: Request) -> TimelineService:
    svc = getattr(request.app.state, "timeline_service", None)
    if not svc:
        raise HTTPException(status_code=503, detail="Timeline Service not initialized")
    return svc


def _event_to_response(event: TimelineEvent) -> TimelineEventResponse:
    return TimelineEventResponse(
        event_id=event.event_id,
        actor=ActorSchema(id=event.actor.id, type=event.actor.type.value, name=event.actor.name),
        activity=event.activity.value,
        target=TargetSchema(id=event.target.id, type=event.target.type, label=event.target.label),
        outcome=event.outcome.value,
        metadata=event.metadata,
        timestamp=event.timestamp.isoformat(),
        tenant_id=event.tenant_id,
    )


@router.get("/timeline/entity/{entity_type}/{entity_id}")
async def get_entity_timeline(
    entity_type: str,
    entity_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    service = _get_service(request)
    events, total = await service.get_entity_timeline(
        entity_type=entity_type,
        entity_id=entity_id,
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
    )
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "total": total,
        "page": page,
        "page_size": page_size,
        "entries": [_event_to_response(e) for e in events],
    }


@router.get("/timeline/recent")
async def get_recent_timeline(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    limit: int = Query(20, ge=1, le=100),
):
    service = _get_service(request)
    events = await service.get_recent(tenant_id=tenant_id, limit=limit)
    return {"entries": [_event_to_response(e) for e in events]}


@router.post("/timeline/events")
async def create_timeline_event(
    body: TimelineEventCreate,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    service = _get_service(request)
    try:
        activity = ActivityType(body.activity)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid activity type: {body.activity}")
    try:
        outcome = ActivityOutcome(body.outcome)
    except ValueError:
        outcome = ActivityOutcome.SUCCESS

    actor = Actor(id=body.actor.id, type=body.actor.type, name=body.actor.name)
    target = Target(id=body.target.id, type=body.target.type, label=body.target.label)

    event = await service.create_event(
        actor=actor,
        activity=activity,
        target=target,
        outcome=outcome,
        metadata=body.metadata,
        tenant_id=tenant_id or body.tenant_id,
    )
    return _event_to_response(event)


@router.get("/timeline/search")
async def search_timeline(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    target_id: str | None = Query(None),
    target_type: str | None = Query(None),
    actor_id: str | None = Query(None),
    activity_types: str | None = Query(None, description="Comma-separated activity types"),
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_order: str = Query("desc"),
):
    service = _get_service(request)
    from datetime import datetime
    q = TimelineQuery(
        target_id=target_id or "",
        target_type=target_type or "",
        actor_id=actor_id or "",
        activity_types=[t.strip() for t in activity_types.split(",")] if activity_types else None,
        tenant_id=tenant_id,
        from_date=datetime.fromisoformat(from_date) if from_date else None,
        to_date=datetime.fromisoformat(to_date) if to_date else None,
        page=page,
        page_size=page_size,
        sort_order=sort_order,
    )
    events, total = await service.search(q)
    return TimelineSearchResponse(
        events=[_event_to_response(e) for e in events],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/timeline/entity/{entity_type}/{entity_id}/summary")
async def get_timeline_summary(
    entity_type: str,
    entity_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    service = _get_service(request)
    summary = await service.get_summary(
        entity_type=entity_type,
        entity_id=entity_id,
        tenant_id=tenant_id,
    )
    return summary
