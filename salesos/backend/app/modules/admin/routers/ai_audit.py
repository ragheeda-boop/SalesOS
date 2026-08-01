from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.owner_auth import get_current_tenant_id, require_owner_role_dep

router = APIRouter(
    tags=["Admin - AI Audit Log"],
    dependencies=[Depends(require_owner_role_dep("admin"))],
)


@router.get("/ai/audit/logs")
async def query_ai_audit_logs(
    action: str | None = Query(None),
    model: str | None = Query(None),
    user_id: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    min_tokens: int | None = Query(None, ge=0),
    max_tokens: int | None = Query(None, ge=0),
    min_cost: float | None = Query(None, ge=0),
    max_cost: float | None = Query(None, ge=0),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
    tenant_id: str = Depends(get_owner_scoped_tenant_id),
):
    from app.modules.audit.service import AuditService, PostgresAuditRepository

    repo = PostgresAuditRepository(db)
    service = AuditService(repository=repo)

    filters: dict[str, Any] = {
        "action": action,
        "user_id": user_id,
    }
    if date_from:
        filters["date_from"] = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
    if date_to:
        filters["date_to"] = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
    if date_from is None and date_to is None:
        filters["action__prefix"] = "ai:"

    entries, total = await service.query(tenant_id, filters, page, size)

    results = []
    for e in entries:
        details = e.details or {}
        results.append(
            {
                "id": e.id,
                "user_id": e.user_id,
                "action": e.action,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "model": details.get("ai_model"),
                "prompt_tokens": details.get("prompt_tokens"),
                "completion_tokens": details.get("completion_tokens"),
                "total_tokens": details.get("total_tokens"),
                "cost": details.get("cost"),
                "operation": details.get("operation"),
                "details": details,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
        )

    return {
        "total": total,
        "page": page,
        "size": size,
        "results": results,
    }


@router.get("/ai/audit/summary")
async def ai_audit_summary(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db_session),
    tenant_id: str = Depends(get_owner_scoped_tenant_id),
):
    from app.modules.audit.service import AuditService, PostgresAuditRepository

    repo = PostgresAuditRepository(db)
    service = AuditService(repository=repo)

    filters: dict[str, Any] = {
        "action__prefix": "ai:",
    }
    entries, total = await service.query(tenant_id, filters, page=1, size=10000)

    model_counts: dict[str, int] = {}
    action_counts: dict[str, int] = {}
    total_cost = 0.0
    total_tokens = 0

    for e in entries:
        details = e.details or {}
        model = details.get("ai_model", "unknown")
        model_counts[model] = model_counts.get(model, 0) + 1
        action_counts[e.action] = action_counts.get(e.action, 0) + 1
        total_cost += details.get("cost", 0.0) or 0.0
        total_tokens += details.get("total_tokens", 0) or 0

    return {
        "total_calls": total,
        "total_cost": round(total_cost, 6),
        "total_tokens": total_tokens,
        "by_model": [
            {"model": m, "count": c}
            for m, c in sorted(model_counts.items(), key=lambda x: x[1], reverse=True)
        ],
        "by_action": [
            {"action": a, "count": c}
            for a, c in sorted(action_counts.items(), key=lambda x: x[1], reverse=True)
        ],
    }
