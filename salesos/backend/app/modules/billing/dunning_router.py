"""STORY-05-04 — Owner dunning APIs."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.modules.billing.dunning_service import DunningService
from app.owner_auth import require_owner_role_dep

router = APIRouter(
    tags=["Admin - Dunning"],
    dependencies=[Depends(require_owner_role_dep("admin"))],
)


class DunningOpenRequest(BaseModel):
    tenant_id: uuid.UUID
    stripe_invoice_id: str | None = Field(None, max_length=128)
    failed_at: datetime | None = None


class DunningEvaluateRequest(BaseModel):
    now: datetime | None = None


class DunningCaseResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    subscription_id: uuid.UUID | None = None
    status: str
    failed_at: datetime
    grace_ends_at: datetime
    suspended_at: datetime | None = None
    cleared_at: datetime | None = None
    failure_count: int
    last_stripe_invoice_id: str | None = None


def _case_response(c: Any) -> DunningCaseResponse:
    return DunningCaseResponse(
        id=c.id,
        tenant_id=c.tenant_id,
        subscription_id=c.subscription_id,
        status=c.status,
        failed_at=c.failed_at,
        grace_ends_at=c.grace_ends_at,
        suspended_at=c.suspended_at,
        cleared_at=c.cleared_at,
        failure_count=c.failure_count,
        last_stripe_invoice_id=c.last_stripe_invoice_id,
    )


@router.get("/billing/dunning", response_model=list[DunningCaseResponse])
async def list_dunning_cases(
    db: AsyncSession = Depends(get_db_session),
    status: str | None = Query(None),
    tenant_id: uuid.UUID | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
) -> list[DunningCaseResponse]:
    rows = await DunningService(db).list_cases(
        status=status, tenant_id=tenant_id, limit=limit
    )
    return [_case_response(r) for r in rows]


@router.post("/billing/dunning/open", response_model=DunningCaseResponse, status_code=201)
async def open_dunning_case(
    body: DunningOpenRequest,
    db: AsyncSession = Depends(get_db_session),
) -> DunningCaseResponse:
    case = await DunningService(db).open_or_bump(
        tenant_id=body.tenant_id,
        stripe_invoice_id=body.stripe_invoice_id,
        failed_at=body.failed_at,
    )
    await db.commit()
    return _case_response(case)


@router.post("/billing/dunning/evaluate")
async def evaluate_dunning(
    body: DunningEvaluateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    result = await DunningService(db).evaluate_due(now=body.now)
    await db.commit()
    return result


@router.post("/billing/dunning/{tenant_id}/clear")
async def clear_dunning(
    tenant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    cleared = await DunningService(db).clear_for_tenant(tenant_id)
    if cleared == 0:
        raise HTTPException(status_code=404, detail="no open dunning case")
    await db.commit()
    return {"tenant_id": str(tenant_id), "cleared": cleared}
