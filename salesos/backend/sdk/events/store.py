"""PostgreSQL-backed event store implementation."""

import json
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from sdk.events.base import DomainEvent, EventStore


class PostgresEventStore(EventStore):
    """Event store backed by PostgreSQL.

    Uses a dedicated 'domain_events' table for persistence.
    Supports event sourcing replay and query by type.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def append(self, event: DomainEvent) -> None:
        stmt = text("""
            INSERT INTO domain_events (
                event_id, event_type, event_version,
                aggregate_id, aggregate_type, tenant_id,
                occurred_at, data, metadata
            ) VALUES (
                :event_id, :event_type, :event_version,
                :aggregate_id, :aggregate_type, :tenant_id,
                :occurred_at, :data::jsonb, :metadata::jsonb
            )
        """)
        await self._session.execute(
            stmt,
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "event_version": event.event_version,
                "aggregate_id": event.aggregate_id,
                "aggregate_type": event.aggregate_type,
                "tenant_id": event.tenant_id,
                "occurred_at": event.occurred_at,
                "data": json.dumps(event.data),
                "metadata": json.dumps(event.metadata),
            },
        )

    async def read_stream(
        self, aggregate_type: str, aggregate_id: str
    ) -> list[DomainEvent]:
        stmt = text("""
            SELECT * FROM domain_events
            WHERE aggregate_type = :aggregate_type
              AND aggregate_id = :aggregate_id
            ORDER BY occurred_at ASC
        """)
        result = await self._session.execute(
            stmt, {"aggregate_type": aggregate_type, "aggregate_id": aggregate_id}
        )
        rows = result.fetchall()
        return [self._row_to_event(row) for row in rows]

    async def read_by_type(
        self, event_type: str, since: datetime | None = None, limit: int = 100
    ) -> list[DomainEvent]:
        conditions = "event_type = :event_type"
        params: dict[str, Any] = {"event_type": event_type, "limit": limit}

        if since:
            conditions += " AND occurred_at >= :since"
            params["since"] = since

        stmt = text(f"""
            SELECT * FROM domain_events
            WHERE {conditions}
            ORDER BY occurred_at DESC
            LIMIT :limit
        """)
        result = await self._session.execute(stmt, params)
        rows = result.fetchall()
        return [self._row_to_event(row) for row in rows]

    def _row_to_event(self, row) -> DomainEvent:
        return DomainEvent(
            event_id=row.event_id,
            event_type=row.event_type,
            event_version=row.event_version,
            aggregate_id=row.aggregate_id,
            aggregate_type=row.aggregate_type,
            tenant_id=row.tenant_id,
            occurred_at=row.occurred_at,
            data=row.data or {},
            metadata=row.metadata or {},
        )
