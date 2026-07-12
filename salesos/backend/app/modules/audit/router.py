from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_current_user_id, get_db_session, verify_token

from .service import AuditService, PostgresAuditRepository

router = APIRouter()


def get_service(request: Request, db: AsyncSession = Depends(get_db_session)) -> AuditService:
    repo = PostgresAuditRepository(db)
    return AuditService(repository=repo)


@router.get("/audit/logs")
async def query_audit_logs(
    request: Request,
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    user_id: str | None = Query(None),
    resource_id: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    token: dict = Depends(verify_token),
    tenant_id: str = Depends(get_current_tenant_id),
    service: AuditService = Depends(get_service),
):
    filters: dict[str, Any] = {}
    if action:
        filters["action"] = action
    if resource_type:
        filters["resource_type"] = resource_type
    if user_id:
        filters["user_id"] = user_id
    if resource_id:
        filters["resource_id"] = resource_id
    if date_from:
        filters["date_from"] = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
    if date_to:
        filters["date_to"] = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
    if search:
        filters["search"] = search

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
    service: AuditService = Depends(get_service),
):
    return await service.stats(tenant_id, days)
