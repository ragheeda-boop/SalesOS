from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import require_role_dep

from ..schemas import (
    DetailedHealthResponse,
    HealthComponentStatus,
    HealthHistoryEntry,
)
from ._dependencies import AdminRepositories, get_admin_repos

router = APIRouter(
    tags=["Admin - Health"],
    dependencies=[Depends(require_role_dep("admin"))],
)


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def get_detailed_health(repos: AdminRepositories = Depends(get_admin_repos)):
    health = await repos.health.get_detailed_health()
    return DetailedHealthResponse(
        overall_status=health["overall_status"],
        uptime_seconds=health["uptime_seconds"],
        components=[HealthComponentStatus(**c) for c in health["components"]],
    )


@router.get("/health/history", response_model=list[HealthHistoryEntry])
async def get_health_history(hours: int = Query(24, ge=1, le=168), repos: AdminRepositories = Depends(get_admin_repos)):
    history = await repos.health.get_history(hours=hours)
    return [HealthHistoryEntry(
        timestamp=h.timestamp,
        overall_status=h.overall_status,
        components=h.components,
    ) for h in history]
