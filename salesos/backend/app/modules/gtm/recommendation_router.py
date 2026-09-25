"""Tenant-scoped deterministic recommendations from current CRM opportunity data."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from intelligence.deal_intelligence import DealIntelligenceService
from intelligence.recommendation_engine import RecommendationEngine
from sdk.permissions import PermissionAction

router = APIRouter()

_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


@router.get("/recommendations")
async def list_recommendations(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.READ)),
    limit: int = Query(20, ge=1, le=50),
) -> dict:
    """Generate explainable recommendations without mutating CRM or sending messages."""
    result = await db.execute(
        text("""
            SELECT o.id, o.name, o.stage, o.value, o.probability,
                   COALESCE((
                       SELECT COUNT(*)
                       FROM activity_records ar
                       WHERE ar.tenant_id = o.tenant_id
                         AND ar.entity_id = o.id::text
                   ), 0) AS activity_count,
                   (
                       SELECT EXTRACT(EPOCH FROM (NOW() - se.entered_at)) / 86400
                       FROM commercial_stage_entries se
                       WHERE se.opportunity_id = o.id
                         AND se.to_stage = o.stage
                         AND se.exited_at IS NULL
                       ORDER BY se.entered_at DESC
                       LIMIT 1
                   ) AS days_in_stage
            FROM commercial_opportunities o
            WHERE o.tenant_id = :tenant_id AND o.status = 'open'
            ORDER BY o.updated_at DESC
            LIMIT 250
        """),
        {"tenant_id": tenant_id},
    )
    rows = result.mappings().all()
    deal_service = DealIntelligenceService(None, None)
    engine = RecommendationEngine()
    recommendations = []
    skipped_missing_probability = 0

    for row in rows:
        if row["probability"] is None:
            skipped_missing_probability += 1
            continue
        deal_health = await deal_service.analyze_deal(
            tenant_id=tenant_id,
            deal_id=str(row["id"]),
            deal_name=row["name"] or "",
            stage=row["stage"] or "",
            value=float(row["value"] or 0),
            probability=float(row["probability"]),
            days_in_stage=(
                float(row["days_in_stage"]) if row["days_in_stage"] is not None else None
            ),
            activity_count=int(row["activity_count"] or 0),
        )
        recommendation = engine.recommend_from_deal_health(
            tenant_id=tenant_id,
            deal_id=deal_health.deal_id,
            deal_name=deal_health.deal_name,
            health_level=deal_health.health_level,
            health_score=deal_health.health_score,
            risk_factors=deal_health.risk_factors,
            opportunity_factors=deal_health.opportunity_factors,
        )
        recommendations.append(
            {
                "id": recommendation.id,
                "title": recommendation.title,
                "description": recommendation.description,
                "reasoning": recommendation.reasoning,
                "priority": recommendation.priority.value,
                "confidence": recommendation.confidence,
                "target_id": recommendation.target_id,
                "target_type": recommendation.target_type,
                "evidence": [
                    {
                        "source_domain": item.source_domain,
                        "source_type": item.source_type,
                        "description": item.description,
                        "confidence": item.confidence,
                    }
                    for item in recommendation.evidence
                ],
            }
        )

    recommendations.sort(
        key=lambda item: (
            _PRIORITY_ORDER[item["priority"]],
            -item["confidence"],
            item["target_id"],
        )
    )
    return {
        "items": recommendations[:limit],
        "total": min(len(recommendations), limit),
        "source_opportunities": len(rows),
        "skipped_missing_probability": skipped_missing_probability,
        "generated_at": datetime.now(UTC).isoformat(),
        "method": "deterministic_crm_rules",
        "mutated_crm": False,
    }
