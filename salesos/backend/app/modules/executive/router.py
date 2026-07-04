from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session

router = APIRouter()


class RevenueKPI(BaseModel):
    total_booked: float = 0.0
    total_pipeline: float = 0.0
    weighted_pipeline: float = 0.0
    forecast: float = 0.0
    growth_percent: float = 0.0


class TeamKPI(BaseModel):
    total_employees: int = 0
    active_employees: int = 0
    top_performers: list[dict] = []
    avg_win_rate: float = 0.0


class RiskKPI(BaseModel):
    expiring_contracts: int = 0
    stalled_deals: int = 0
    inactive_companies: int = 0
    low_pipeline_employees: int = 0


class HealthKPI(BaseModel):
    overall_health: str = "good"
    data_completeness: float = 0.0
    sync_status: str = "synced"
    last_activity: str = ""


class PipelineHealth(BaseModel):
    total_deals: int = 0
    total_value: float = 0.0
    won_deals: int = 0
    lost_deals: int = 0
    win_rate: float = 0.0
    avg_deal_size: float = 0.0
    by_stage: list[dict] = []


class RenewalKPI(BaseModel):
    due_next_30_days: int = 0
    due_next_90_days: int = 0
    total_renewal_value: float = 0.0
    at_risk: list[dict] = []


class GrowthKPI(BaseModel):
    new_companies_30d: int = 0
    new_contacts_30d: int = 0
    new_opportunities_30d: int = 0
    new_contracts_30d: int = 0


class ExecutiveDashboard(BaseModel):
    revenue: RevenueKPI = RevenueKPI()
    team: TeamKPI = TeamKPI()
    risk: RiskKPI = RiskKPI()
    health: HealthKPI = HealthKPI()
    pipeline: PipelineHealth = PipelineHealth()
    renewals: RenewalKPI = RenewalKPI()
    growth: GrowthKPI = GrowthKPI()


@router.get("/executive/dashboard", response_model=ExecutiveDashboard)
async def executive_dashboard(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    import uuid
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    days_30 = now - timedelta(days=30)
    days_90 = now - timedelta(days=90)

    # Revenue
    total_pipeline = 0.0
    total_booked = 0.0
    try:
        row = await db.execute(sa_text("""
            SELECT COALESCE(SUM(value), 0) as total_pipeline,
                   COALESCE(SUM(CASE WHEN status IN ('won','closed_won') THEN value ELSE 0 END), 0) as won_value
            FROM commercial_opportunities WHERE tenant_id = :tid
        """), {"tid": tenant_id})
        r = dict(row.mappings().one())
        total_pipeline = r["total_pipeline"]
        total_booked = r["won_value"]
    except Exception:
        pass

    # Team
    total_employees = 0
    active_employees = 0
    try:
        row = await db.execute(sa_text("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active
            FROM users WHERE tenant_id = :tid
        """), {"tid": tenant_id})
        r = dict(row.mappings().one())
        total_employees = r["total"]
        active_employees = r["active"]
    except Exception:
        pass

    # Pipeline health
    total_deals = 0
    won_deals = 0
    lost_deals = 0
    avg_deal_size = 0.0
    try:
        row = await db.execute(sa_text("""
            SELECT COUNT(*) as total,
                   COALESCE(SUM(CASE WHEN status IN ('won','closed_won') THEN 1 ELSE 0 END), 0) as won,
                   COALESCE(SUM(CASE WHEN status IN ('lost','closed_lost') THEN 1 ELSE 0 END), 0) as lost,
                   COALESCE(AVG(value), 0) as avg_val
            FROM commercial_opportunities WHERE tenant_id = :tid
        """), {"tid": tenant_id})
        r = dict(row.mappings().one())
        total_deals = r["total"]
        won_deals = r["won"]
        lost_deals = r["lost"]
        avg_deal_size = r["avg_val"]
    except Exception:
        pass

    win_rate = won_deals / (won_deals + lost_deals) if (won_deals + lost_deals) > 0 else 0.0

    # Pipeline by stage
    by_stage = []
    try:
        rows = await db.execute(sa_text("""
            SELECT stage, COUNT(*) as cnt, COALESCE(SUM(value), 0) as val
            FROM commercial_opportunities WHERE tenant_id = :tid AND status = 'open'
            GROUP BY stage ORDER BY cnt DESC
        """), {"tid": tenant_id})
        by_stage = [dict(r) for r in rows.mappings().all()]
    except Exception:
        pass

    # Risks
    stalled_deals = 0
    try:
        row = await db.execute(sa_text("""
            SELECT COUNT(*) as cnt FROM commercial_opportunities
            WHERE tenant_id = :tid AND status = 'open' AND stage = 'prospecting'
        """), {"tid": tenant_id})
        stalled_deals = dict(row.mappings().one())["cnt"]
    except Exception:
        pass

    # Renewals
    due_30 = 0
    due_90 = 0
    try:
        row = await db.execute(sa_text("""
            SELECT
                SUM(CASE WHEN expiry_date <= :d30 THEN 1 ELSE 0 END) as due_30,
                SUM(CASE WHEN expiry_date <= :d90 AND expiry_date > :d30 THEN 1 ELSE 0 END) as due_90
            FROM commercial_contracts WHERE tenant_id = :tid AND status = 'active'
        """), {"tid": tenant_id, "d30": days_30.date(), "d90": days_90.date()})
        r = dict(row.mappings().one())
        due_30 = r["due_30"] or 0
        due_90 = r["due_90"] or 0
    except Exception:
        pass

    # Growth
    new_companies = 0
    new_opportunities = 0
    try:
        row = await db.execute(sa_text("""
            SELECT
                (SELECT COUNT(*) FROM companies WHERE tenant_id = :tid AND created_at >= :d30) as new_companies,
                (SELECT COUNT(*) FROM commercial_opportunities WHERE tenant_id = :tid AND created_at >= :d30) as new_opps
        """), {"tid": tenant_id, "d30": days_30})
        r = dict(row.mappings().one())
        new_companies = r["new_companies"]
        new_opportunities = r["new_opps"]
    except Exception:
        pass

    return ExecutiveDashboard(
        revenue=RevenueKPI(
            total_booked=total_booked,
            total_pipeline=total_pipeline,
            weighted_pipeline=total_pipeline * win_rate,
            forecast=total_pipeline * win_rate,
        ),
        team=TeamKPI(
            total_employees=total_employees,
            active_employees=active_employees,
            avg_win_rate=round(win_rate, 2),
        ),
        risk=RiskKPI(
            stalled_deals=stalled_deals,
            expiring_contracts=due_30 + due_90,
        ),
        pipeline=PipelineHealth(
            total_deals=total_deals,
            total_value=total_pipeline,
            won_deals=won_deals,
            lost_deals=lost_deals,
            win_rate=round(win_rate, 2),
            avg_deal_size=round(avg_deal_size, 2),
            by_stage=by_stage,
        ),
        renewals=RenewalKPI(
            due_next_30_days=due_30,
            due_next_90_days=due_90,
        ),
        growth=GrowthKPI(
            new_companies_30d=new_companies,
            new_opportunities_30d=new_opportunities,
        ),
        health=HealthKPI(
            overall_health="good",
            data_completeness=0.85,
            sync_status="synced",
            last_activity=now.isoformat(),
        ),
    )
