"""Tenant-scoped, read-only AI governance audit feed."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from sdk.permissions import PermissionAction

router = APIRouter()


@router.get("/ai-governance/audit")
async def list_ai_governance_audit(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("audit", PermissionAction.READ)),
) -> dict:
    """List governance audit metadata without exposing comments or raw payloads."""
    filters = "tenant_id = :tenant_id AND resource_type LIKE 'ai:governance/%'"
    params = {"tenant_id": tenant_id}
    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM audit_logs WHERE {filters}"), params
    )
    total = int(count_result.scalar_one() or 0)

    offset = (page - 1) * page_size
    rows_result = await db.execute(
        text(f"""
            SELECT id, user_id, action, resource_type, resource_id, outcome,
                   request_id, created_at,
                   details->'metadata'->>'policy_name' AS policy_name,
                   details->'metadata'->>'decision' AS decision,
                   details->'metadata'->>'enforcement_action' AS enforcement_action
            FROM audit_logs
            WHERE {filters}
            ORDER BY created_at DESC, id DESC
            LIMIT :page_size OFFSET :offset
        """),
        {**params, "page_size": page_size, "offset": offset},
    )
    rows = rows_result.mappings().all()

    return {
        "items": [
            {
                "id": int(row["id"]),
                "user_id": row["user_id"],
                "action": row["action"],
                "resource_type": row["resource_type"],
                "resource_id": row["resource_id"],
                "outcome": row["outcome"],
                "request_id": row["request_id"],
                "created_at": row["created_at"].isoformat()
                if isinstance(row["created_at"], datetime)
                else None,
                "policy_name": row["policy_name"],
                "decision": row["decision"],
                "enforcement_action": row["enforcement_action"],
            }
            for row in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "generated_at": datetime.now(UTC).isoformat(),
        "read_only": True,
    }
