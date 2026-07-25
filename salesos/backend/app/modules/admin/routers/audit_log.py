from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_role_dep, verify_token

from ..services import AuditCSVExportService

router = APIRouter(
    tags=["Admin - Audit Log"],
    dependencies=[Depends(require_role_dep("admin"))],
)


@router.get("/audit/logs")
async def query_audit_logs(
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    user_id: str | None = Query(None),
    resource_id: str | None = Query(None),
    outcome: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
    token: dict = Depends(verify_token),
    tenant_id: str = Depends(get_current_tenant_id),
):
    from app.modules.audit.service import AuditService, PostgresAuditRepository

    repo = PostgresAuditRepository(db)
    service = AuditService(repository=repo)

    filters: dict[str, Any] = {}
    if action:
        filters["action"] = action
    if resource_type:
        filters["resource_type"] = resource_type
    if user_id:
        filters["user_id"] = user_id
    if resource_id:
        filters["resource_id"] = resource_id
    if outcome:
        filters["outcome"] = outcome
    if date_from:
        filters["date_from"] = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
    if date_to:
        filters["date_to"] = datetime.fromisoformat(date_to.replace("Z", "+00:00"))

    entries, total = await service.query(tenant_id, filters, page, size)
    return {
        "total": total,
        "page": page,
        "size": size,
        "results": [
            {
                "id": e.id,
                "tenant_id": e.tenant_id,
                "user_id": e.user_id,
                "action": e.action,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "outcome": e.outcome,
                "details": e.details,
                "ip_address": e.ip_address,
                "user_agent": e.user_agent,
                "request_id": e.request_id,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ],
    }


@router.get("/audit/stats")
async def audit_stats(
    days: int = Query(30, ge=1, le=365),
    token: dict = Depends(verify_token),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    from app.modules.audit.service import AuditService, PostgresAuditRepository

    repo = PostgresAuditRepository(db)
    service = AuditService(repository=repo)
    return await service.stats(tenant_id, days)


@router.get("/audit/export")
async def export_audit_csv(
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    user_id: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    db: AsyncSession = Depends(get_db_session),
    token: dict = Depends(verify_token),
    tenant_id: str = Depends(get_current_tenant_id),
):
    from app.modules.audit.service import AuditService, PostgresAuditRepository

    repo = PostgresAuditRepository(db)
    service = AuditService(repository=repo)

    filters: dict[str, Any] = {}
    if action:
        filters["action"] = action
    if resource_type:
        filters["resource_type"] = resource_type
    if user_id:
        filters["user_id"] = user_id
    if date_from:
        filters["date_from"] = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
    if date_to:
        filters["date_to"] = datetime.fromisoformat(date_to.replace("Z", "+00:00"))

    entries, total = await service.query(tenant_id, filters, page=1, size=10000)
    entries_dicts = [
        {
            "id": e.id,
            "tenant_id": e.tenant_id,
            "user_id": e.user_id,
            "action": e.action,
            "resource_type": e.resource_type,
            "resource_id": e.resource_id,
            "outcome": e.outcome,
            "ip_address": e.ip_address,
            "user_agent": e.user_agent,
            "created_at": e.created_at,
        }
        for e in entries
    ]
    csv_content = AuditCSVExportService.to_csv(entries_dicts)
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=audit_logs_{tenant_id}.csv"},
    )
