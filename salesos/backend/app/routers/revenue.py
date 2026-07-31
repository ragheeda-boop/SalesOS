"""Revenue Workspace REST API — unified dashboard endpoint."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache import cached
from app.common.rate_limit import rate_limit_dep
from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from runtime.pipeline_analytics import PipelineAnalytics
from sdk.permissions import PermissionAction

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(rate_limit_dep("revenue", 15, 60))])


@router.get("/revenue/dashboard")
@cached("revenue:dashboard", ttl=60)
async def revenue_dashboard(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("revenue", PermissionAction.READ)),
):
    """Unified revenue dashboard: pipeline summary, active opportunities, recent activity."""
    try:
        analytics = PipelineAnalytics(db, tenant_id)

        # Sequential awaits — asyncpg forbids concurrent ops on one connection.
        pipeline_summary = await analytics.summary()
        opps_res = await db.execute(
            sa_text("""
                SELECT id, name, stage, value, probability, company_id, owner_id, status
                FROM commercial_opportunities
                WHERE tenant_id = :tid AND status != 'closed'
                ORDER BY value DESC LIMIT 10
            """),
            {"tid": tenant_id},
        )
        active_opportunities = [dict(r) for r in opps_res.mappings().all()]
        total_res = await db.execute(
            sa_text("""
                SELECT COALESCE(SUM(value), 0) as total_value, COUNT(*) as count
                FROM commercial_opportunities
                WHERE tenant_id = :tid AND status != 'closed'
            """),
            {"tid": tenant_id},
        )
        total_row = total_res.mappings().one()
        total_value = float(total_row["total_value"])
        opportunity_count = total_row["count"]

        recent_signals: list[dict] = []
        try:
            signals_res = await db.execute(
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
            recent_signals = [dict(r) for r in signals_res.mappings().all()]
        except Exception as sig_exc:
            # Demo/local DBs may lack company_signals — do not fail the dashboard.
            logger.warning("revenue_dashboard signals skipped: %s", sig_exc)
            await db.rollback()

        return {
            "pipeline_summary": pipeline_summary,
            "active_opportunities": active_opportunities,
            "total_value": total_value,
            "opportunity_count": opportunity_count,
            "recent_signals": recent_signals,
        }
    except Exception as exc:
        logger.error("revenue_dashboard failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
