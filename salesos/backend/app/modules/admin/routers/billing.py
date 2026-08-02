from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.modules.billing.service import SubscriptionService
from app.modules.billing.state_machine import SubscriptionTransitionError
from app.modules.identity.models import Tenant
from app.owner_auth import require_owner_role_dep

from ..schemas import (
    InvoiceResponse,
    SubscriptionResponse,
    SubscriptionTransitionRequest,
    TransactionResponse,
)
from ._dependencies import AdminRepositories, get_admin_repos

router = APIRouter(
    tags=["Admin - Billing"],
    dependencies=[Depends(require_owner_role_dep("admin"))],
)


def _subscription_response(row) -> SubscriptionResponse:
    return SubscriptionResponse(
        id=row.id,
        tenant_id=row.tenant_id,
        plan_id=row.plan_id,
        status=row.status,
        billing_cycle=row.billing_cycle,
        seats=row.seats,
        trial_ends_at=row.trial_ends_at,
        current_period_start=row.current_period_start,
        current_period_end=row.current_period_end,
        canceled_at=row.canceled_at,
        pending_plan_id=getattr(row, "pending_plan_id", None),
        pending_effective_at=getattr(row, "pending_effective_at", None),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def _resolve_tenant_name(db: AsyncSession, tenant_id: str) -> str:
    try:
        tid = uuid.UUID(tenant_id)
        tenant = await db.get(Tenant, tid)
        if tenant:
            return tenant.name
    except (ValueError, Exception):
        pass
    return tenant_id


@router.get("/billing/subscriptions/{tenant_id}", response_model=SubscriptionResponse)
async def get_tenant_subscription(
    tenant_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """STORY-05-01: Owner read of a tenant's subscription."""
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid tenant_id") from exc
    svc = SubscriptionService(db)
    row = await svc.get_by_tenant(tid)
    if row is None:
        raise HTTPException(status_code=404, detail="subscription not found")
    return _subscription_response(row)


@router.post(
    "/billing/subscriptions/{tenant_id}/transition",
    response_model=SubscriptionResponse,
)
async def transition_tenant_subscription(
    tenant_id: str,
    body: SubscriptionTransitionRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """STORY-05-01: apply a named subscription state-machine event."""
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid tenant_id") from exc
    svc = SubscriptionService(db)
    try:
        row = await svc.apply_event(tenant_id=tid, event=body.event)
    except SubscriptionTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    return _subscription_response(row)


@router.get("/billing/invoices", response_model=list[InvoiceResponse])
async def list_invoices(
    tenant_id: str | None = Query(None),
    repos: AdminRepositories = Depends(get_admin_repos),
    db: AsyncSession = Depends(get_db_session),
):
    invoices = await repos.invoices.list_invoices(tenant_id)
    return [
        InvoiceResponse(
            id=inv.id,
            tenant_id=inv.tenant_id,
            tenant_name=await _resolve_tenant_name(db, str(inv.tenant_id)),
            amount=inv.amount,
            currency=inv.currency,
            status=inv.status,
            description=inv.description,
            due_date=inv.due_date,
            paid_at=inv.paid_at,
            created_at=inv.created_at,
        )
        for inv in invoices
    ]


@router.get("/billing/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    tenant_id: str | None = Query(None),
    repos: AdminRepositories = Depends(get_admin_repos),
    db: AsyncSession = Depends(get_db_session),
):
    txs = await repos.invoices.list_transactions(tenant_id)
    return [
        TransactionResponse(
            id=tx.id,
            tenant_id=tx.tenant_id,
            tenant_name=await _resolve_tenant_name(db, str(tx.tenant_id)),
            amount=tx.amount,
            currency=tx.currency,
            status=tx.status,
            method=tx.method,
            description=tx.description,
            reference=tx.reference,
            created_at=tx.created_at,
        )
        for tx in txs
    ]
