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

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_tenant_id, verify_token
from intelligence.activity_intelligence.contracts.models import (
    ActivityDashboardDTO,
    CompanyEngagementDTO,
)
from intelligence.activity_intelligence.mappers.company_mapper import CompanyEngagementMapper
from intelligence.activity_intelligence.mappers.dashboard_mapper import DashboardMapper

router = APIRouter(
    prefix="/api/v1/activity",
    tags=["Activity Intelligence"],
    dependencies=[Depends(verify_token)],
)


def _get_service():
    """Get ActivityIntelligenceService from app state."""
    # In production, injected via FastAPI dependency
    # For now, returns None — wired during app startup
    return None


@router.get("/dashboard", response_model=dict)
async def get_dashboard(tenant_id: str = Depends(get_current_tenant_id)):
    """Get activity dashboard summary."""
    svc = _get_service()
    if svc is None:
        return ActivityDashboardDTO().__dict__
    result = await svc.get_dashboard(tenant_id)
    return DashboardMapper.to_activity_dashboard(result).__dict__


@router.get("/company/{company_id}", response_model=dict)
async def get_company_engagement(
    company_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Get per-company engagement summary."""
    svc = _get_service()
    if svc is None:
        return CompanyEngagementDTO(company_id=company_id).__dict__
    result = await svc.get_company_engagement(company_id, tenant_id)
    return CompanyEngagementMapper.to_company_engagement(company_id, result).__dict__


@router.get("/email", response_model=dict)
async def get_email_metrics(tenant_id: str = Depends(get_current_tenant_id)):
    """Get email intelligence metrics."""
    return {"status": "ok", "message": "Email metrics endpoint"}


@router.get("/calendar", response_model=dict)
async def get_calendar_metrics(tenant_id: str = Depends(get_current_tenant_id)):
    """Get calendar intelligence metrics."""
    return {"status": "ok", "message": "Calendar metrics endpoint"}


@router.get("/followups", response_model=dict)
async def get_followups(tenant_id: str = Depends(get_current_tenant_id)):
    """Get follow-up dashboard."""
    return {"status": "ok", "message": "Followups endpoint"}


@router.get("/engagement", response_model=dict)
async def get_engagement_summary(tenant_id: str = Depends(get_current_tenant_id)):
    """Get engagement summary across all companies."""
    return {"status": "ok", "message": "Engagement endpoint"}
