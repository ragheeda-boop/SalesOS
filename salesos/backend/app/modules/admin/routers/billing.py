from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session, require_role_dep
from app.modules.identity.models import Tenant

from ..schemas import InvoiceResponse, TransactionResponse
from ._dependencies import AdminRepositories, get_admin_repos

router = APIRouter(
    tags=["Admin - Billing"],
    dependencies=[Depends(require_role_dep("admin"))],
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


@router.get("/billing/invoices", response_model=list[InvoiceResponse])
async def list_invoices(
    tenant_id: str | None = Query(None),
    repos: AdminRepositories = Depends(get_admin_repos),
    db: AsyncSession = Depends(get_db_session),
):
    invoices = await repos.invoices.list_invoices(tenant_id)
    return [InvoiceResponse(
        id=inv.id, tenant_id=inv.tenant_id,
        tenant_name=await _resolve_tenant_name(db, str(inv.tenant_id)),
        amount=inv.amount, currency=inv.currency,
        status=inv.status, description=inv.description,
        due_date=inv.due_date, paid_at=inv.paid_at,
        created_at=inv.created_at,
    ) for inv in invoices]


@router.get("/billing/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    tenant_id: str | None = Query(None),
    repos: AdminRepositories = Depends(get_admin_repos),
    db: AsyncSession = Depends(get_db_session),
):
    txs = await repos.invoices.list_transactions(tenant_id)
    return [TransactionResponse(
        id=tx.id, tenant_id=tx.tenant_id,
        tenant_name=await _resolve_tenant_name(db, str(tx.tenant_id)),
        amount=tx.amount, currency=tx.currency,
        status=tx.status, method=tx.method,
        description=tx.description, reference=tx.reference,
        created_at=tx.created_at,
    ) for tx in txs]
