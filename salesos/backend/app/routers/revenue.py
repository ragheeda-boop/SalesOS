"""Revenue Workspace REST API — unified dashboard endpoint."""
import logging
from asyncio import gather

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from app.common.cache import cached
from app.common.rate_limit import rate_limit_dep
from sdk.permissions import PermissionAction
from runtime.pipeline_analytics import PipelineAnalytics

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(rate_limit_dep("revenue", 15, 60))]
)


@router.get("/revenue/dashboard")
@cached("revenue:dashboard", ttl=60)
async def revenue_dashboard(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep(PermissionAction.READ, "revenue")),
):
    """Unified revenue dashboard: pipeline summary, active opportunities, recent activity."""
    try:
        analytics = PipelineAnalytics(db, tenant_id)

        pipeline_task = analytics.summary()
        opps_task = db.execute(
            sa_text("""
                SELECT id, name, stage, value, probability, health, company_id, owner_id
                FROM commercial_opportunities
                WHERE tenant_id = :tid AND status != 'closed'
                ORDER BY value DESC LIMIT 10
            """),
            {"tid": tenant_id},
        )
        total_task = db.execute(
            sa_text("""
                SELECT COALESCE(SUM(value), 0) as total_value, COUNT(*) as count
                FROM commercial_opportunities
                WHERE tenant_id = :tid AND status != 'closed'
            """),
            {"tid": tenant_id},
        )
        signals_task = db.execute(
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

        pipeline_summary, opps_res, total_res, signals_res = await gather(
            pipeline_task, opps_task, total_task, signals_task
        )

        return {
            "pipeline_summary": pipeline_summary,
            "active_opportunities": [dict(r) for r in opps_res.mappings().all()],
            "total_value": float(total_res.mappings().one()["total_value"]),
            "opportunity_count": total_res.mappings().one()["count"],
            "recent_signals": [dict(r) for r in signals_res.mappings().all()],
        }
    except Exception as exc:
        logger.error("revenue_dashboard failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")
