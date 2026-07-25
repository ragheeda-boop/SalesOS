"""Pipeline Analytics REST API — forecasting, analytics, deal scoring."""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from app.common.rate_limit import rate_limit_dep
from sdk.permissions import PermissionAction
from runtime.pipeline_analytics import PipelineAnalytics

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(rate_limit_dep("pipeline", 20, 60))]
)


@router.get("/pipeline/summary")
async def get_pipeline_summary(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.READ)),
):
    try:
        analytics = PipelineAnalytics(db, tenant_id)
        return await analytics.summary()
    except Exception as exc:
        logger.error("pipeline_summary failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pipeline/velocity")
async def get_pipeline_velocity(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.READ)),
):
    try:
        analytics = PipelineAnalytics(db, tenant_id)
        return await analytics.velocity()
    except Exception as exc:
        logger.error("pipeline_velocity failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pipeline/conversion")
async def get_pipeline_conversion(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.READ)),
):
    try:
        analytics = PipelineAnalytics(db, tenant_id)
        return await analytics.conversion_rates()
    except Exception as exc:
        logger.error("pipeline_conversion failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pipeline/health")
async def get_pipeline_health(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.READ)),
):
    try:
        analytics = PipelineAnalytics(db, tenant_id)
        return await analytics.health_map()
    except Exception as exc:
        logger.error("pipeline_health failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pipeline/forecast")
async def get_pipeline_forecast(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.READ)),
):
    try:
        analytics = PipelineAnalytics(db, tenant_id)
        return await analytics.forecast()
    except Exception as exc:
        logger.error("pipeline_forecast failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


# ─────────────────────────────────────────────
# Phase 7 — Advanced Pipeline Forecasting
# ─────────────────────────────────────────────

@router.get("/pipeline/forecast/advanced")
async def get_advanced_forecast(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.READ)),
    horizon_months: int = Query(3, ge=1, le=12),
):
    """Weighted pipeline + historical velocity forecast with confidence intervals."""
    from domains.commercial.pipeline.engine.forecast_engine import PipelineForecastEngine
    from domains.commercial.pipeline.engine.forecast_models import PipelineHistoricalPeriod

    try:
        engine = PipelineForecastEngine()

        opps_res = await db.execute(
            sa_text("""
                SELECT id, name, stage, value, probability, owner_id, status,
                       company_id, created_at, updated_at
                FROM commercial_opportunities
                WHERE tenant_id = :tid
                ORDER BY created_at DESC
            """),
            {"tid": tenant_id},
        )
        opps = [dict(r) for r in opps_res.mappings().all()]

        hist_res = await db.execute(
            sa_text("""
                SELECT
                    TO_CHAR(updated_at, 'YYYY-MM') as period,
                    COUNT(*) as total_deals,
                    SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as won,
                    SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) as lost,
                    SUM(CASE WHEN status = 'won' THEN value ELSE 0 END) as revenue,
                    AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 86400) as avg_cycle
                FROM commercial_opportunities
                WHERE tenant_id = :tid AND status IN ('won', 'lost')
                GROUP BY TO_CHAR(updated_at, 'YYYY-MM')
                ORDER BY period DESC
                LIMIT 12
            """),
            {"tid": tenant_id},
        )
        history = []
        for row in hist_res.mappings().all():
            history.append(PipelineHistoricalPeriod(
                period_label=row["period"],
                period_start=datetime.now(timezone.utc),
                period_end=datetime.now(timezone.utc),
                total_deals=row["total_deals"] or 0,
                closed_won=row["won"] or 0,
                closed_lost=row["lost"] or 0,
                total_revenue=float(row["revenue"] or 0),
                avg_cycle_days=float(row["avg_cycle"] or 0),
            ))
        engine.set_history(history)

        snapshot = engine.forecast(
            opportunities=opps,
            horizon_months=horizon_months,
            tenant_id=tenant_id,
        )
        return snapshot.to_dict()
    except Exception as exc:
        logger.error("advanced_forecast failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


# ─────────────────────────────────────────────
# Phase 7 — Pipeline Analytics (detailed)
# ─────────────────────────────────────────────

@router.get("/pipeline/analytics")
async def get_pipeline_analytics(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.READ)),
):
    """Comprehensive analytics: conversion rates, velocity, stage duration, win/loss rates."""
    from domains.commercial.pipeline.engine.analytics_engine import PipelineAnalyticsEngine
    from domains.commercial.pipeline.contracts.forecast_models import PipelineHistoricalPeriod

    try:
        engine = PipelineAnalyticsEngine()

        opps_res = await db.execute(
            sa_text("""
                SELECT id, name, stage, value, probability, owner_id, status,
                       company_id, created_at, updated_at
                FROM commercial_opportunities
                WHERE tenant_id = :tid
            """),
            {"tid": tenant_id},
        )
        opps = [dict(r) for r in opps_res.mappings().all()]

        entries_res = await db.execute(
            sa_text("""
                SELECT se.to_stage as stage, se.entered_at, se.exited_at,
                       EXTRACT(EPOCH FROM (COALESCE(se.exited_at, NOW()) - se.entered_at)) / 86400 as duration_days
                FROM commercial_stage_entries se
                JOIN commercial_opportunities co ON se.opportunity_id = co.id
                WHERE co.tenant_id = :tid
                ORDER BY se.opportunity_id, se.entered_at
            """),
            {"tid": tenant_id},
        )
        entries = [dict(r) for r in entries_res.mappings().all()]

        hist_res = await db.execute(
            sa_text("""
                SELECT
                    TO_CHAR(updated_at, 'YYYY-MM') as period,
                    COUNT(*) as total_deals,
                    SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as won,
                    SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) as lost,
                    SUM(CASE WHEN status = 'won' THEN value ELSE 0 END) as revenue,
                    AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 86400) as avg_cycle
                FROM commercial_opportunities
                WHERE tenant_id = :tid AND status IN ('won', 'lost')
                GROUP BY TO_CHAR(updated_at, 'YYYY-MM')
                ORDER BY period DESC
                LIMIT 12
            """),
            {"tid": tenant_id},
        )
        history = []
        for row in hist_res.mappings().all():
            history.append(PipelineHistoricalPeriod(
                period_label=row["period"],
                period_start=datetime.now(timezone.utc),
                period_end=datetime.now(timezone.utc),
                total_deals=row["total_deals"] or 0,
                closed_won=row["won"] or 0,
                closed_lost=row["lost"] or 0,
                total_revenue=float(row["revenue"] or 0),
                avg_cycle_days=float(row["avg_cycle"] or 0),
            ))
        engine.set_history(history)

        result = engine.compute(opportunities=opps, stage_entries=entries, tenant_id=tenant_id)
        return result.to_dict()
    except Exception as exc:
        logger.error("pipeline_analytics failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pipeline/value-over-time")
async def get_pipeline_value_over_time(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.READ)),
    months: int = Query(12, ge=1, le=24),
):
    """Monthly pipeline value snapshots."""
    try:
        from domains.commercial.pipeline.engine.analytics_engine import PipelineAnalyticsEngine

        opps_res = await db.execute(
            sa_text("""
                SELECT id, stage, value, probability, status, created_at, updated_at
                FROM commercial_opportunities
                WHERE tenant_id = :tid
                AND created_at >= NOW() - INTERVAL '1 month' * :months
                ORDER BY created_at
            """),
            {"tid": tenant_id, "months": months},
        )
        opps = [dict(r) for r in opps_res.mappings().all()]
        engine = PipelineAnalyticsEngine()
        value_over_time = engine._compute_value_over_time(opps)
        return {"months": len(value_over_time), "data": [v.__dict__ for v in value_over_time]}
    except Exception as exc:
        logger.error("value_over_time failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


# ─────────────────────────────────────────────
# Phase 7 — Deal Scoring
# ─────────────────────────────────────────────

@router.post("/pipeline/score-deal")
async def score_deal(
    deal_id: str = Query(...),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.READ)),
):
    """Score a single deal using Decision Platform factors."""
    from domains.commercial.pipeline.engine.deal_scoring import DealScorer

    try:
        opp_res = await db.execute(
            sa_text("""
                SELECT id, name, stage, value, probability, owner_id, status,
                       company_id, created_at, updated_at
                FROM commercial_opportunities
                WHERE id = :did AND tenant_id = :tid
            """),
            {"did": deal_id, "tid": tenant_id},
        )
        row = opp_res.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Deal not found")

        deal = dict(row)
        if deal.get("created_at"):
            try:
                created = deal["created_at"]
                if isinstance(created, str):
                    created = datetime.fromisoformat(created.replace("Z", "+00:00"))
                deal["age_days"] = (datetime.now(timezone.utc) - created).total_seconds() / 86400
            except (ValueError, TypeError):
                deal["age_days"] = 0
        else:
            deal["age_days"] = 0

        entries_res = await db.execute(
            sa_text("""
                SELECT EXTRACT(EPOCH FROM (COALESCE(exited_at, NOW()) - entered_at)) / 86400 as duration_days
                FROM pipeline_stage_entries
                WHERE opportunity_id = :did AND stage_name = :stage
            """),
            {"did": deal_id, "stage": deal.get("stage", "")},
        )
        entry_row = entries_res.mappings().first()
        if entry_row:
            deal["days_in_stage"] = float(entry_row["duration_days"] or 0)

        conv_res = await db.execute(
            sa_text("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN exit_reason LIKE 'advanced_to_%' THEN 1 ELSE 0 END) as converted
                FROM pipeline_stage_entries
                WHERE stage_name = :stage
            """),
            {"stage": deal.get("stage", "")},
        )
        conv_row = conv_res.mappings().first()
        stage_conversion = {}
        if conv_row and conv_row["total"] > 0:
            stage_conversion = {deal["stage"]: conv_row["converted"] / conv_row["total"]}

        scorer = DealScorer()
        scorer.configure(stage_conversion=stage_conversion)
        score = scorer.score_deal(deal)
        return score.to_dict()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("score_deal failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/pipeline/score-batch")
async def score_batch(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.READ)),
    limit: int = Query(50, ge=1, le=500),
):
    """Score all open deals in the pipeline."""
    from domains.commercial.pipeline.engine.deal_scoring import DealScorer

    try:
        opps_res = await db.execute(
            sa_text("""
                SELECT id, name, stage, value, probability, owner_id, status,
                       company_id, created_at, updated_at
                FROM commercial_opportunities
                WHERE tenant_id = :tid AND status NOT IN ('won', 'lost', 'abandoned')
                ORDER BY value DESC
                LIMIT :lim
            """),
            {"tid": tenant_id, "lim": limit},
        )
        opps = [dict(r) for r in opps_res.mappings().all()]

        for opp in opps:
            if opp.get("created_at"):
                try:
                    created = opp["created_at"]
                    if isinstance(created, str):
                        created = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    opp["age_days"] = (datetime.now(timezone.utc) - created).total_seconds() / 86400
                except (ValueError, TypeError):
                    opp["age_days"] = 0
            else:
                opp["age_days"] = 0

            entries_res = await db.execute(
                sa_text("""
                    SELECT EXTRACT(EPOCH FROM (COALESCE(exited_at, NOW()) - entered_at)) / 86400 as duration_days
                    FROM pipeline_stage_entries
                    WHERE opportunity_id = :oid AND stage_name = :stage
                    LIMIT 1
                """),
                {"oid": opp["id"], "stage": opp.get("stage", "")},
            )
            entry_row = entries_res.mappings().first()
            opp["days_in_stage"] = float(entry_row["duration_days"] or 0) if entry_row else 0

        scorer = DealScorer()
        scores = scorer.score_batch(opps)
        return {
            "total_scored": len(scores),
            "scores": [s.to_dict() for s in scores],
            "summary": {
                "avg_score": round(sum(s.overall_score for s in scores) / max(len(scores), 1), 2),
                "excellent": sum(1 for s in scores if s.health.value == "excellent"),
                "good": sum(1 for s in scores if s.health.value == "good"),
                "fair": sum(1 for s in scores if s.health.value == "fair"),
                "poor": sum(1 for s in scores if s.health.value == "poor"),
                "at_risk": sum(1 for s in scores if s.health.value == "at_risk"),
            },
        }
    except Exception as exc:
        logger.error("score_batch failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")
