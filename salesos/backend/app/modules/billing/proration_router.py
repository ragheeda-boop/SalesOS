"""STORY-05-05 — Owner plan-change / proration APIs."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.modules.billing.proration_service import ProrationError, ProrationService
from app.owner_auth import require_owner_role_dep

router = APIRouter(
    tags=["Admin - Proration"],
    dependencies=[Depends(require_owner_role_dep("admin"))],
)


class PlanChangeRequest(BaseModel):
    tenant_id: uuid.UUID
    target_plan_id: uuid.UUID
    downgrade_immediate: bool = Field(
        False,
        description="If true, downgrade applies now with prorated credit; else period-end.",
    )
    now: datetime | None = None


class PlanChangeEvaluateRequest(BaseModel):
    now: datetime | None = None


@router.post("/billing/plan-change/quote")
async def quote_plan_change(
    body: PlanChangeRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        return await ProrationService(db).quote(
            tenant_id=body.tenant_id,
            target_plan_id=body.target_plan_id,
            downgrade_immediate=body.downgrade_immediate,
            now=body.now,
        )
    except ProrationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/billing/plan-change/apply")
async def apply_plan_change(
    body: PlanChangeRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        result = await ProrationService(db).apply(
            tenant_id=body.tenant_id,
            target_plan_id=body.target_plan_id,
            downgrade_immediate=body.downgrade_immediate,
            now=body.now,
        )
    except ProrationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    return result


@router.post("/billing/plan-change/apply-pending")
async def apply_pending_plan_changes(
    body: PlanChangeEvaluateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    result = await ProrationService(db).apply_pending_due(now=body.now)
    await db.commit()
    return result
