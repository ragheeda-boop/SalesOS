"""Audit trail writer for recording all domain mutations."""

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AuditTrail:
    """Immutable audit log for all data mutations.

    Every create, update, and delete operation across all modules
    is recorded here. Logs cannot be modified or deleted.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def record(
        self,
        tenant_id: str | UUID,
        entity_type: str,
        entity_id: str | UUID,
        action: str,
        changes: dict[str, Any] | None = None,
        performed_by: str | UUID | None = None,
        ip_address: str | None = None,
        request_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        stmt = text("""
            INSERT INTO audit.audit_log (
                tenant_id, entity_type, entity_id, action,
                changes, performed_by, performed_at,
                ip_address, request_id, metadata
            ) VALUES (
                :tenant_id, :entity_type, :entity_id, :action,
                CAST(:changes AS jsonb), :performed_by, :performed_at,
                :ip_address, :request_id, CAST(:metadata AS jsonb)
            )
        """)
        await self._session.execute(
            stmt,
            {
                "tenant_id": str(tenant_id),
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "action": action,
                "changes": json.dumps(changes or {}),
                "performed_by": str(performed_by) if performed_by else None,
                "performed_at": datetime.now(timezone.utc),
                "ip_address": ip_address,
                "request_id": request_id,
                "metadata": json.dumps(metadata or {}),
            },
        )

    async def query(
        self,
        tenant_id: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        action: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        conditions = ["tenant_id = :tenant_id"]
        params: dict[str, Any] = {"tenant_id": tenant_id, "limit": limit, "offset": offset}

        if entity_type:
            conditions.append("entity_type = :entity_type")
            params["entity_type"] = entity_type
        if entity_id:
            conditions.append("entity_id = :entity_id")
            params["entity_id"] = entity_id
        if action:
            conditions.append("action = :action")
            params["action"] = action

        where = " AND ".join(conditions)
        stmt = text(f"""
            SELECT * FROM audit.audit_log
            WHERE {where}
            ORDER BY performed_at DESC
            LIMIT :limit OFFSET :offset
        """)
        result = await self._session.execute(stmt, params)
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
