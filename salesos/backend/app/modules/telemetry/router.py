from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_current_user_id, get_db_session, verify_token

from .service import TelemetryService, InMemoryTelemetryRepository

router = APIRouter()


def get_service(request: Request) -> TelemetryService:
    repo = InMemoryTelemetryRepository()
    return TelemetryService(repository=repo)


@router.post("/api/v1/telemetry/event")
async def track_event(
    event_type: str = Query(..., description="Type of event to track"),
    properties: str | None = Query(None, description="JSON string of event properties"),
    token: dict = Depends(verify_token),
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
    service: TelemetryService = Depends(get_service),
):
    import json
    parsed_props = None
    if properties:
        try:
            parsed_props = json.loads(properties)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in properties")
    event = await service.track(event_type, tenant_id, user_id, parsed_props)
    return {
        "id": event.id,
        "event_type": event.event_type,
        "tenant_id": event.tenant_id,
        "user_id": event.user_id,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
    }


@router.get("/api/v1/admin/telemetry/feature-adoption")
async def get_feature_adoption(
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    token: dict = Depends(verify_token),
    tenant_id: str = Depends(get_current_tenant_id),
    service: TelemetryService = Depends(get_service),
):
    frm = datetime.fromisoformat(from_date.replace("Z", "+00:00")) if from_date else None
    to = datetime.fromisoformat(to_date.replace("Z", "+00:00")) if to_date else None
    return await service.feature_adoption(tenant_id, frm, to)


@router.get("/api/v1/admin/telemetry/search-success")
async def get_search_success(
    token: dict = Depends(verify_token),
    tenant_id: str = Depends(get_current_tenant_id),
    service: TelemetryService = Depends(get_service),
):
    return await service.search_success_rate(tenant_id)


@router.get("/api/v1/admin/telemetry/nba-acceptance")
async def get_nba_acceptance(
    token: dict = Depends(verify_token),
    tenant_id: str = Depends(get_current_tenant_id),
    service: TelemetryService = Depends(get_service),
):
    return await service.nba_acceptance_rate(tenant_id)


@router.get("/api/v1/admin/telemetry/active-users")
async def get_active_users(
    days: int = Query(7, ge=1, le=365),
    token: dict = Depends(verify_token),
    service: TelemetryService = Depends(get_service),
):
    return await service.active_users(days)


@router.get("/api/v1/admin/telemetry/overview")
async def get_telemetry_overview(
    token: dict = Depends(verify_token),
    tenant_id: str = Depends(get_current_tenant_id),
    service: TelemetryService = Depends(get_service),
):
    adoption = await service.feature_adoption(tenant_id)
    search = await service.search_success_rate(tenant_id)
    nba = await service.nba_acceptance_rate(tenant_id)
    time_insight = await service.time_to_insight(tenant_id)
    time_action = await service.time_to_action(tenant_id)
    users = await service.active_users()

    total_features = len(adoption)
    avg_adoption = round(sum(a["adoption_pct"] for a in adoption) / total_features, 1) if total_features > 0 else 0.0

    return {
        "feature_adoption": adoption,
        "search_success": search,
        "nba_acceptance": nba,
        "time_to_insight": time_insight,
        "time_to_action": time_action,
        "active_users": users,
        "avg_adoption_pct": avg_adoption,
    }
