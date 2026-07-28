"""Employee Intelligence API — Calendar, Email, Productivity, Relationship, Executive.

All endpoints require employee.READ permission and tenant isolation.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    get_current_tenant_id,
    get_current_user_id,
    get_db_session,
    require_permission_dep,
)
from sdk.permissions import PermissionAction

from .calendar_service import CalendarIntelligenceService
from .email_service import EmailIntelligenceService
from .productivity_service import ProductivityService, RelationshipService
from .executive_service import ExecutiveDashboardService

router = APIRouter()


# ── Calendar Intelligence ──────────────────────────────────────────

@router.get(
    "/employees/{employee_id}/calendar-kpis",
    dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))],
)
async def employee_calendar_kpis(
    employee_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    svc = CalendarIntelligenceService(db)
    return await svc.get_kpis(employee_id, tenant_id)


@router.get(
    "/employees/{employee_id}/calendar-heatmap",
    dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))],
)
async def employee_calendar_heatmap(
    employee_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    days: int = Query(30, ge=7, le=90),
):
    svc = CalendarIntelligenceService(db)
    return await svc.get_heatmap(employee_id, tenant_id, days)


# ── Email Intelligence ─────────────────────────────────────────────

@router.get(
    "/employees/{employee_id}/email-kpis",
    dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))],
)
async def employee_email_kpis(
    employee_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    days: int = Query(30, ge=7, le=90),
):
    svc = EmailIntelligenceService(db)
    return await svc.get_kpis(employee_id, tenant_id, days)


@router.get(
    "/employees/{employee_id}/email-top-contacts",
    dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))],
)
async def employee_email_top_contacts(
    employee_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(10, ge=1, le=50),
):
    svc = EmailIntelligenceService(db)
    return await svc.get_top_contacts(employee_id, tenant_id, limit)


@router.get(
    "/employees/{employee_id}/email-daily-volume",
    dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))],
)
async def employee_email_daily_volume(
    employee_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    days: int = Query(30, ge=7, le=90),
):
    svc = EmailIntelligenceService(db)
    return await svc.get_daily_volume(employee_id, tenant_id, days)


# ── Productivity Intelligence ──────────────────────────────────────

@router.get(
    "/employees/{employee_id}/productivity",
    dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))],
)
async def employee_productivity(
    employee_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    period_days: int = Query(30, ge=7, le=90),
):
    svc = ProductivityService(db)
    return await svc.compute(employee_id, tenant_id, period_days)


@router.get(
    "/employees/{employee_id}/relationship/{target_type}/{target_id}",
    dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))],
)
async def employee_relationship_score(
    employee_id: str,
    target_type: str,
    target_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    svc = RelationshipService(db)
    return await svc.compute_relationship_score(employee_id, tenant_id, target_id, target_type)


# ── Executive Dashboard ────────────────────────────────────────────

@router.get(
    "/executive/summary",
    dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))],
)
async def executive_summary(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ExecutiveDashboardService(db)
    return await svc.get_summary(tenant_id)


# ── OAuth Integration ──────────────────────────────────────────────

@router.post(
    "/employees/{employee_id}/oauth/{provider}/callback",
    dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))],
)
async def oauth_callback(
    employee_id: str,
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    redirect_uri: str = Query(...),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Exchange OAuth authorization code for tokens (Google/Microsoft)."""
    from .oauth_service import OAuthTokenService
    import httpx

    if provider not in ("google", "microsoft"):
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    svc = OAuthTokenService(db)
    try:
        if provider == "google":
            resp = await _exchange_google_code(code, redirect_uri)
        else:
            resp = await _exchange_microsoft_code(code, redirect_uri)

        token = await svc.store_tokens(
            employee_id=employee_id,
            tenant_id=tenant_id,
            provider=provider,
            access_token=resp["access_token"],
            refresh_token=resp.get("refresh_token"),
            id_token=resp.get("id_token"),
            expires_in=resp.get("expires_in", 3600),
            scope=resp.get("scope", ""),
        )
        await db.commit()
        return {"status": "connected", "provider": provider, "expires_at": token.access_token_expires_at.isoformat()}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"OAuth exchange failed: {str(e)}")


@router.delete(
    "/employees/{employee_id}/oauth/{provider}",
    dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))],
)
async def oauth_disconnect(
    employee_id: str,
    provider: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Disconnect OAuth integration for a provider."""
    from .oauth_service import OAuthTokenService
    svc = OAuthTokenService(db)
    await svc.invalidate(employee_id, provider)
    await db.commit()
    return {"status": "disconnected", "provider": provider}


@router.post(
    "/employees/{employee_id}/oauth/{provider}/sync",
    dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))],
)
async def oauth_trigger_sync(
    employee_id: str,
    provider: str,
    sync_type: str = Query("calendar"),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Manually trigger calendar or email sync for an employee."""
    from .tasks import calendar_sync_employee, email_sync_employee
    try:
        if sync_type == "calendar":
            await calendar_sync_employee(employee_id, tenant_id, provider)
        elif sync_type == "email":
            await email_sync_employee(employee_id, tenant_id, provider)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown sync_type: {sync_type}")
        await db.commit()
        return {"status": "synced", "employee_id": employee_id, "provider": provider, "type": sync_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# ── AI Intelligence ────────────────────────────────────────────────

@router.get(
    "/employees/{employee_id}/ai/weekly-digest",
    dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))],
)
async def employee_ai_weekly_digest(
    employee_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Generate AI weekly performance digest."""
    from .ai_pipeline import EmployeeAIPipeline
    pipeline = EmployeeAIPipeline(db)
    return await pipeline.generate_weekly_digest(employee_id, tenant_id)


@router.get(
    "/employees/{employee_id}/ai/coaching",
    dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))],
)
async def employee_ai_coaching(
    employee_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Generate AI personalized coaching insight."""
    from .ai_pipeline import EmployeeAIPipeline
    pipeline = EmployeeAIPipeline(db)
    return await pipeline.generate_coaching_insight(employee_id, tenant_id)


@router.get(
    "/executive/ai-brief",
    dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))],
)
async def executive_ai_brief(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Generate AI executive brief for the organization."""
    from .ai_pipeline import EmployeeAIPipeline
    pipeline = EmployeeAIPipeline(db)
    return await pipeline.generate_executive_brief(tenant_id)


@router.post(
    "/calendar-events/{event_id}/ai-summary",
    dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))],
)
async def calendar_ai_summary(
    event_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Generate AI summary for a calendar event."""
    from .ai_pipeline import EmployeeAIPipeline
    pipeline = EmployeeAIPipeline(db)
    return await pipeline.generate_meeting_summary(event_id)


@router.post(
    "/email-events/{event_id}/ai-summary",
    dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))],
)
async def email_ai_summary(
    event_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Generate AI summary + sentiment for an email event."""
    from .ai_pipeline import EmployeeAIPipeline
    pipeline = EmployeeAIPipeline(db)
    return await pipeline.generate_email_summary(event_id)


# ── Health & Observability ─────────────────────────────────────────

@router.get("/health/employee-360")
async def employee_360_health(
    db: AsyncSession = Depends(get_db_session),
):
    """Full health check for Employee 360 sub-services."""
    from .health import EmployeeHealthChecker
    checker = EmployeeHealthChecker(db)
    return await checker.full_check()


@router.get("/health/employee-360/ready")
async def employee_360_readiness(
    db: AsyncSession = Depends(get_db_session),
):
    """Kubernetes readiness probe."""
    from .health import EmployeeHealthChecker
    checker = EmployeeHealthChecker(db)
    ok = await checker.readiness()
    if not ok:
        raise HTTPException(status_code=503, detail="Service not ready")
    return {"status": "ready"}


@router.get("/health/employee-360/live")
async def employee_360_liveness():
    """Kubernetes liveness probe."""
    return {"status": "alive"}


# ── Helpers ────────────────────────────────────────────────────────

async def _exchange_google_code(code: str, redirect_uri: str) -> dict:
    import httpx
    from app.config import settings
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": settings.sso_google_client_id,
            "client_secret": settings.sso_google_client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        })
        if resp.status_code != 200:
            raise Exception(f"Google OAuth error: {resp.text[:200]}")
        return resp.json()


async def _exchange_microsoft_code(code: str, redirect_uri: str) -> dict:
    import httpx
    from app.config import settings
    client_id = getattr(settings, "sso_microsoft_client_id", "") or getattr(settings, "MICROSOFT_CLIENT_ID", "")
    client_secret = getattr(settings, "sso_microsoft_client_secret", "") or getattr(settings, "MICROSOFT_CLIENT_SECRET", "")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post("https://login.microsoftonline.com/common/oauth2/v2.0/token", data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "scope": "https://graph.microsoft.com/.default",
        })
        if resp.status_code != 200:
            raise Exception(f"Microsoft OAuth error: {resp.text[:200]}")
        return resp.json()
