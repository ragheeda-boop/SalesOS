"""Tenant-scoped, read-only opportunity health insights for the V3 deal page."""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from intelligence.deal_intelligence import DealIntelligenceService
from sdk.permissions import PermissionAction

router = APIRouter()


@router.get("/opportunities/{opportunity_id}/intelligence")
async def get_deal_intelligence(
    opportunity_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.READ)),
) -> dict:
    """Calculate a rule-based deal summary from current tenant CRM data.

    This endpoint is read-only. It never records an insight or updates the deal.
    A missing probability is reported as insufficient data instead of being
    converted into a guessed score.
    """
    result = await db.execute(
        text("""
            SELECT o.id, o.name, o.stage, o.value, o.probability, o.status,
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
            WHERE o.id::text = :opportunity_id AND o.tenant_id = :tenant_id
            LIMIT 1
        """),
        {"opportunity_id": opportunity_id, "tenant_id": tenant_id},
    )
    opportunity = result.mappings().one_or_none()
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    probability = opportunity["probability"]
    activity_count = int(opportunity["activity_count"] or 0)
    days_in_stage = opportunity["days_in_stage"]
    if probability is None:
        missing_fields = ["probability"]
        if days_in_stage is None:
            missing_fields.append("days_in_stage")
        return {
            "opportunity_id": str(opportunity["id"]),
            "deal_name": opportunity["name"],
            "health_score": None,
            "health_level": "unknown",
            "risk_factors": ["Probability is missing; health score was not calculated."],
            "opportunity_factors": [],
            "stage": opportunity["stage"] or "",
            "value": float(opportunity["value"] or 0),
            "probability": None,
            "days_in_stage": float(days_in_stage) if days_in_stage is not None else None,
            "activity_count": activity_count,
            "missing_fields": missing_fields,
            "generated_at": datetime.now(UTC).isoformat(),
            "method": "deterministic_crm_rules",
        }

    health = await DealIntelligenceService(None, None).analyze_deal(
        tenant_id=tenant_id,
        deal_id=str(opportunity["id"]),
        deal_name=opportunity["name"] or "",
        stage=opportunity["stage"] or "",
        value=float(opportunity["value"] or 0),
        probability=float(probability),
        days_in_stage=float(days_in_stage) if days_in_stage is not None else None,
        activity_count=activity_count,
    )
    output = asdict(health)
    output["missing_fields"] = [] if days_in_stage is not None else ["days_in_stage"]
    output["generated_at"] = datetime.now(UTC).isoformat()
    output["method"] = "deterministic_crm_rules"
    return output
