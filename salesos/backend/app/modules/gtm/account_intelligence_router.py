"""Tenant-scoped account context derived only from persisted CRM records."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from intelligence.account_evidence import persist_account_insight
from intelligence.account_signals import build_account_signals, build_engagement_trend
from sdk.permissions import PermissionAction

router = APIRouter()


@router.get("/companies/{company_id}/account-intelligence")
async def get_account_intelligence(
    company_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("company", PermissionAction.READ)),
) -> dict:
    """Return CRM facts for an account; this endpoint does not score or mutate it."""
    company_result = await db.execute(
        text("""
            SELECT id, name_ar, name_en, industry, city, status
            FROM companies
            WHERE id::text = :company_id AND tenant_id::text = :tenant_id
            LIMIT 1
        """),
        {"company_id": company_id, "tenant_id": tenant_id},
    )
    company = company_result.mappings().one_or_none()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    opportunities_result = await db.execute(
        text("""
            SELECT COUNT(*) AS total_opportunities,
                   COUNT(*) FILTER (WHERE LOWER(COALESCE(status, '')) = 'open') AS active_opportunities,
                   COUNT(*) FILTER (WHERE LOWER(COALESCE(status, '')) = 'won') AS won_deals,
                   COUNT(*) FILTER (WHERE LOWER(COALESCE(status, '')) = 'lost') AS lost_deals
            FROM commercial_opportunities
            WHERE tenant_id = :tenant_id AND company_id::text = :company_id
        """),
        {"company_id": company_id, "tenant_id": tenant_id},
    )
    opportunities = opportunities_result.mappings().one()

    activity_result = await db.execute(
        text("""
            SELECT COUNT(*) AS activity_count,
                   MAX(timestamp) AS last_activity_at,
                   COUNT(*) FILTER (WHERE timestamp >= NOW() - INTERVAL '90 days')
                       AS recent_activity_count,
                   COUNT(*) FILTER (
                       WHERE timestamp >= NOW() - INTERVAL '180 days'
                         AND timestamp < NOW() - INTERVAL '90 days'
                   ) AS previous_activity_count
            FROM activity_records
            WHERE tenant_id::text = :tenant_id
              AND entity_type = 'company'
              AND entity_id = :company_id
        """),
        {"company_id": company_id, "tenant_id": tenant_id},
    )
    activity = activity_result.mappings().one()

    total = int(opportunities["total_opportunities"] or 0)
    activity_count = int(activity["activity_count"] or 0)
    last_activity_at = activity["last_activity_at"]
    if last_activity_at is not None and last_activity_at.tzinfo is None:
        last_activity_at = last_activity_at.replace(tzinfo=UTC)
    days_since_activity = (
        max(0, (datetime.now(UTC) - last_activity_at).days)
        if last_activity_at is not None
        else None
    )

    account_signals = build_account_signals(
        total_opportunities=total,
        active_opportunities=int(opportunities["active_opportunities"] or 0),
        won_deals=int(opportunities["won_deals"] or 0),
        lost_deals=int(opportunities["lost_deals"] or 0),
        activity_count=int(activity["activity_count"] or 0),
        days_since_activity=days_since_activity,
    )
    engagement_trend = build_engagement_trend(
        recent_90_days=int(activity["recent_activity_count"] or 0),
        previous_90_days=int(activity["previous_activity_count"] or 0),
    )

    return {
        "company_id": str(company["id"]),
        "company_name": company["name_en"] or company["name_ar"] or "",
        "industry": company["industry"],
        "city": company["city"],
        "company_status": company["status"],
        "total_opportunities": total,
        "active_opportunities": int(opportunities["active_opportunities"] or 0),
        "won_deals": int(opportunities["won_deals"] or 0),
        "lost_deals": int(opportunities["lost_deals"] or 0),
        "activity_count": activity_count,
        "last_activity_at": last_activity_at.isoformat() if last_activity_at else None,
        "days_since_activity": days_since_activity,
        "missing_data": [
            name
            for name, missing in (
                ("opportunity_history", total == 0),
                ("activity_history", activity_count == 0),
            )
            if missing
        ],
        "account_signals": account_signals,
        "engagement_trend": engagement_trend,
        "generated_at": datetime.now(UTC).isoformat(),
        "method": "persisted_crm_records_with_explainable_rules",
        "mutated_crm": False,
    }


@router.post("/companies/{company_id}/account-intelligence/evidence")
async def record_account_intelligence_evidence(
    company_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("company", PermissionAction.CREATE)),
) -> dict:
    """Persist a tenant-scoped, idempotent evidence snapshot on explicit request."""
    facts = await get_account_intelligence(
        company_id=company_id,
        tenant_id=tenant_id,
        db=db,
        _rbac=None,
    )
    return await persist_account_insight(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        company_name=facts["company_name"],
        facts=facts,
    )
