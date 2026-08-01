from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import PaginatedResponse
from app.dependencies import get_db_session
from app.modules.identity.models import Tenant
from app.owner_auth import require_owner_role_dep

from ..schemas import AICostResponse, AICostSummary, AIUsageResponse
from ._dependencies import AdminRepositories, get_admin_repos

router = APIRouter(
    tags=["Admin - AI Costs"],
    dependencies=[Depends(require_owner_role_dep("admin"))],
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


@router.get("/ai/costs", response_model=PaginatedResponse)
async def list_ai_costs(
    model: str | None = Query(None),
    tenant_id: str | None = Query(None),
    days: int = Query(30, ge=1, le=365),
    page_size: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, description="Keyset cursor for pagination"),
    repos: AdminRepositories = Depends(get_admin_repos),
    db: AsyncSession = Depends(get_db_session),
):
    from sdk.pagination import encode_cursor

    records, total = await repos.ai.list(
        model=model, tenant_id=tenant_id, days=days, page=1, page_size=page_size + 1
    )
    has_next = len(records) > page_size
    if has_next:
        records = records[:page_size]
    next_cursor = None
    if has_next and records:
        last = records[-1]
        next_cursor = encode_cursor(str(last.id), last.created_at)
    items = [
        AICostResponse(
            id=r.id,
            model=r.model,
            tenant_id=r.tenant_id,
            tenant_name=await _resolve_tenant_name(db, str(r.tenant_id))
            if r.tenant_id
            else "System",
            prompt_tokens=r.prompt_tokens,
            completion_tokens=r.completion_tokens,
            total_tokens=r.total_tokens,
            cost=r.cost,
            operation=r.operation,
            created_at=r.created_at,
        )
        for r in records
    ]
    return PaginatedResponse(
        total=total,
        page=1,
        page_size=page_size,
        items=items,
        next_cursor=next_cursor,
        has_next=has_next,
    )


@router.get("/ai/summary", response_model=AICostSummary)
async def get_ai_cost_summary(
    days: int = Query(30, ge=1, le=365), repos: AdminRepositories = Depends(get_admin_repos)
):
    summary = await repos.ai.get_summary(days=days)
    return AICostSummary(**summary)


@router.get("/ai/usage", response_model=AIUsageResponse)
async def get_ai_usage(
    days: int = Query(30, ge=1, le=365), repos: AdminRepositories = Depends(get_admin_repos)
):
    usage = await repos.ai.get_usage(days=days)
    return AIUsageResponse(**usage)
