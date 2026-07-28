"""Activity Intelligence API — REST endpoints (ADR-012 §9).

All consumers (Dashboard, Company 360, Employee 360, Opportunity 360,
AI Copilot) use these endpoints.

Routes:
  GET /api/v1/activity/dashboard
  GET /api/v1/activity/company/{id}
  GET /api/v1/activity/email
  GET /api/v1/activity/calendar
  GET /api/v1/activity/followups
  GET /api/v1/activity/engagement
"""

from __future__ import annotations

from dataclasses import asdict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, verify_token
from intelligence.activity_intelligence.service import ActivityIntelligenceService

router = APIRouter(
    prefix="/api/v1/activity",
    tags=["Activity Intelligence"],
    dependencies=[Depends(verify_token)],
)


def _get_service(db: AsyncSession = Depends(get_db_session)) -> ActivityIntelligenceService:
    return ActivityIntelligenceService(db)


def _serialize(obj) -> dict:
    if hasattr(obj, "__dataclass_fields__"):
        data = asdict(obj)
        return data
    if isinstance(obj, dict):
        return obj
    return dict(obj)


@router.get("/dashboard", response_model=dict)
async def get_dashboard(
    tenant_id: str = Depends(get_current_tenant_id),
    svc: ActivityIntelligenceService = Depends(_get_service),
):
    """Get activity dashboard summary."""
    result = await svc.get_dashboard(tenant_id)
    return _serialize(result)


@router.get("/company/{company_id}", response_model=dict)
async def get_company_engagement(
    company_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    svc: ActivityIntelligenceService = Depends(_get_service),
):
    """Get per-company engagement summary."""
    result = await svc.get_company_engagement(company_id, tenant_id)
    return _serialize(result)


@router.get("/email", response_model=dict)
async def get_email_metrics(
    tenant_id: str = Depends(get_current_tenant_id),
    svc: ActivityIntelligenceService = Depends(_get_service),
):
    """Get email intelligence metrics."""
    return await svc.get_email_metrics(tenant_id)


@router.get("/calendar", response_model=dict)
async def get_calendar_metrics(
    tenant_id: str = Depends(get_current_tenant_id),
    svc: ActivityIntelligenceService = Depends(_get_service),
):
    """Get calendar intelligence metrics."""
    return await svc.get_calendar_metrics(tenant_id)


@router.get("/followups", response_model=dict)
async def get_followups(
    tenant_id: str = Depends(get_current_tenant_id),
    svc: ActivityIntelligenceService = Depends(_get_service),
):
    """Get follow-up dashboard."""
    return await svc.get_followups(tenant_id)


@router.get("/engagement", response_model=dict)
async def get_engagement_summary(
    tenant_id: str = Depends(get_current_tenant_id),
    svc: ActivityIntelligenceService = Depends(_get_service),
):
    """Get engagement summary across all companies."""
    return await svc.get_engagement_summary(tenant_id)
