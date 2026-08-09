"""ADR-031: Activity Attribution read-only API router.

Shadow mode: exposes attribution data for observation/validation.
Does NOT modify scoring or trigger business decisions.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session

router = APIRouter(prefix="/api/v1")


class AttributionItem(BaseModel):
    id: str
    activity_type: str
    activity_id: str
    activity_source_table: str
    resolution_method: str
    confidence: float
    resolution_state: str
    evidence: dict | None = None
    algorithm_version: str | None = None
    resolved_at: str | None = None

    model_config = {"from_attributes": True}


class AttributionListResponse(BaseModel):
    items: list[AttributionItem]
    total: int


@router.get("/attributions", response_model=AttributionListResponse)
async def list_attributions(
    opportunity_id: str | None = Query(None),
    resolution_state: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    conditions = ["aa.tenant_id = :tid"]
    params = {"tid": tenant_id}

    if opportunity_id:
        conditions.append("aa.opportunity_id = :oid")
        params["oid"] = opportunity_id
    if resolution_state:
        conditions.append("aa.resolution_state = :rs")
        params["rs"] = resolution_state

    where = " AND ".join(conditions)

    count_result = await db.execute(
        text(f"SELECT count(*) FROM activity_attributions aa WHERE {where}"),
        params,
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        text(f"""
            SELECT
                aa.id, aa.activity_type, aa.activity_id,
                aa.activity_source_table, aa.resolution_method,
                aa.confidence::float, aa.resolution_state,
                aa.evidence, aa.algorithm_version,
                aa.resolved_at::text
            FROM activity_attributions aa
            WHERE {where}
            ORDER BY aa.resolved_at DESC
            LIMIT :limit OFFSET :offset
        """),
        {**params, "limit": limit, "offset": offset},
    )

    items = [
        AttributionItem(
            id=str(r.id), activity_type=r.activity_type,
            activity_id=str(r.activity_id),
            activity_source_table=r.activity_source_table,
            resolution_method=r.resolution_method,
            confidence=float(r.confidence), resolution_state=r.resolution_state,
            evidence=r.evidence, algorithm_version=r.algorithm_version,
            resolved_at=r.resolved_at,
        )
        for r in result.fetchall()
    ]

    return AttributionListResponse(items=items, total=total)
