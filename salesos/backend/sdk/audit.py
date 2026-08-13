"""Audit trail writer for recording all domain mutations.

CI-19 Wave 2 Core (no sqlalchemy.text)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, String, column, insert, select, table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession

# Lightweight table()/column() — avoid private MetaData island (EAB-001-P1-DRIFT-01).
# Live table is audit.audit_log (0001_baseline); this is a DML stub only.
audit_log = table(
    "audit_log",
    column("id", PGUUID(as_uuid=True)),
    column("tenant_id", String(255)),
    column("entity_type", String(100)),
    column("entity_id", String(255)),
    column("action", String(50)),
    column("changes", JSONB),
    column("performed_by", String(255)),
    column("performed_at", DateTime(timezone=True)),
    column("ip_address", String(50)),
    column("request_id", String(100)),
    column("metadata", JSONB),
    schema="audit",
)


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
        stmt = insert(audit_log).values(
            tenant_id=str(tenant_id),
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
            changes=changes or {},
            performed_by=str(performed_by) if performed_by else None,
            performed_at=datetime.now(UTC),
            ip_address=ip_address,
            request_id=request_id,
            metadata=metadata or {},
        )
        await self._session.execute(stmt)

    async def query(
        self,
        tenant_id: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        action: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        stmt = select(audit_log).where(audit_log.c.tenant_id == tenant_id)
        if entity_type:
            stmt = stmt.where(audit_log.c.entity_type == entity_type)
        if entity_id:
            stmt = stmt.where(audit_log.c.entity_id == entity_id)
        if action:
            stmt = stmt.where(audit_log.c.action == action)
        stmt = stmt.order_by(audit_log.c.performed_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
