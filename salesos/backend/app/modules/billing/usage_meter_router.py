"""STORY-05-03 — Owner UsageMeter APIs (record / rollup / list).

No Stripe secrets. DEC-085 untouched. Not Production GO.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.modules.billing.usage_meter_service import UsageMeterService
from app.modules.billing.usage_metrics import METRIC_KEYS
from app.owner_auth import require_owner_role_dep

router = APIRouter(
    tags=["Admin - Usage Meter"],
    dependencies=[Depends(require_owner_role_dep("admin"))],
)


class UsageEventCreate(BaseModel):
    tenant_id: uuid.UUID
    metric_key: str = Field(..., description=f"One of {sorted(METRIC_KEYS)}")
    quantity: float = Field(..., ge=0)
    op: str | None = Field(None, description="add|set; default by metric")
    recorded_at: datetime | None = None
    source: str | None = Field(None, max_length=64)


class UsageRollupRequest(BaseModel):
    through: datetime | None = Field(
        None,
        description="Roll events with recorded_at < through (default: start of current UTC hour)",
    )
    limit: int = Field(5000, ge=1, le=50_000)


class UsageMeterResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    metric_key: str
    period_start: datetime
    period_end: datetime
    quantity: float


class UsageEventResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    metric_key: str
    quantity: float
    op: str
    recorded_at: datetime
    rolled_up_at: datetime | None = None
    source: str | None = None


@router.post("/billing/usage/events", response_model=UsageEventResponse, status_code=201)
async def record_usage_event(
    body: UsageEventCreate,
    db: AsyncSession = Depends(get_db_session),
) -> UsageEventResponse:
    svc = UsageMeterService(db)
    try:
        row = await svc.record_event(
            tenant_id=body.tenant_id,
            metric_key=body.metric_key,
            quantity=body.quantity,
            op=body.op,
            recorded_at=body.recorded_at,
            source=body.source,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    return UsageEventResponse(
        id=row.id,
        tenant_id=row.tenant_id,
        metric_key=row.metric_key,
        quantity=row.quantity,
        op=row.op,
        recorded_at=row.recorded_at,
        rolled_up_at=row.rolled_up_at,
        source=row.source,
    )


@router.post("/billing/usage/rollup")
async def rollup_usage(
    body: UsageRollupRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    svc = UsageMeterService(db)
    result = await svc.rollup_pending(through=body.through, limit=body.limit)
    await db.commit()
    return result


@router.get("/billing/usage", response_model=list[UsageMeterResponse])
async def list_usage_meters(
    db: AsyncSession = Depends(get_db_session),
    tenant_id: uuid.UUID | None = Query(None),
    metric_key: str | None = Query(None),
    period_from: datetime | None = Query(None),
    period_to: datetime | None = Query(None),
    limit: int = Query(200, ge=1, le=1000),
) -> list[UsageMeterResponse]:
    svc = UsageMeterService(db)
    try:
        rows = await svc.list_meters(
            tenant_id=tenant_id,
            metric_key=metric_key,
            period_from=period_from,
            period_to=period_to,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [
        UsageMeterResponse(
            id=r.id,
            tenant_id=r.tenant_id,
            metric_key=r.metric_key,
            period_start=r.period_start,
            period_end=r.period_end,
            quantity=r.quantity,
        )
        for r in rows
    ]
