"""Revenue Workspace REST API — unified dashboard endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text as sa_text

from app.dependencies import get_current_tenant_id, get_db_session
from runtime.pipeline_analytics import PipelineAnalytics

router = APIRouter()


@router.get("/revenue/dashboard")
async def revenue_dashboard(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Unified revenue dashboard: pipeline summary, active opportunities, recent activity."""
    # Pipeline summary
    analytics = PipelineAnalytics(db, tenant_id)
    pipeline_summary = await analytics.summary()

    # Active opportunities (top 10)
    opps = await db.execute(
        sa_text("""
            SELECT id, name, stage, value, probability, health, company_id, owner_id
            FROM commercial_opportunities
            WHERE tenant_id = :tid AND status != 'closed'
            ORDER BY value DESC LIMIT 10
        """),
        {"tid": tenant_id},
    )
    active_opportunities = [dict(r) for r in opps.mappings().all()]

    # Total pipeline value
    total = await db.execute(
        sa_text("""
            SELECT COALESCE(SUM(value), 0) as total_value, COUNT(*) as count
            FROM commercial_opportunities
            WHERE tenant_id = :tid AND status != 'closed'
        """),
        {"tid": tenant_id},
    )
    totals = total.mappings().one()

    # Recent signals
    signals = await db.execute(
        sa_text("""
            SELECT cs.id, cs.title, cs.signal_type, cs.created_at,
                   c.name_ar as company_name
            FROM company_signals cs
            JOIN companies c ON cs.company_id = c.id
            WHERE c.tenant_id = :tid
            ORDER BY cs.created_at DESC LIMIT 10
        """),
        {"tid": tenant_id},
    )
    recent_signals = [dict(r) for r in signals.mappings().all()]

    return {
        "pipeline_summary": pipeline_summary,
        "active_opportunities": active_opportunities,
        "total_value": float(totals["total_value"]),
        "opportunity_count": totals["count"],
        "recent_signals": recent_signals,
    }
