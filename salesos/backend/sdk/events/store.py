"""PostgreSQL-backed event store implementation.

CI-19 Wave 2 Core (no sqlalchemy.text)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.schema import Table

from sdk.events.base import DomainEvent, EventStore

_domain_events_metadata = MetaData()

domain_events = Table(
    "domain_events",
    _domain_events_metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("event_id", String(255), nullable=False, unique=True),
    Column("event_type", String(100), nullable=False),
    Column("event_version", Integer, nullable=False),
    Column("aggregate_id", String(255), nullable=False),
    Column("aggregate_type", String(100), nullable=False),
    Column("tenant_id", String(255)),
    Column("occurred_at", DateTime(timezone=True), nullable=False),
    Column("data", JSONB),
    Column("metadata", JSONB),
)


class PostgresEventStore(EventStore):
    """Event store backed by PostgreSQL.

    Uses a dedicated 'domain_events' table for persistence.
    Supports event sourcing replay and query by type.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def append(self, event: DomainEvent) -> None:
        stmt = insert(domain_events).values(
            event_id=event.event_id,
            event_type=event.event_type,
            event_version=event.event_version,
            aggregate_id=event.aggregate_id,
            aggregate_type=event.aggregate_type,
            tenant_id=event.tenant_id,
            occurred_at=event.occurred_at,
            data=event.data,
            metadata=event.metadata,
        )
        await self._session.execute(stmt)

    async def read_stream(self, aggregate_type: str, aggregate_id: str) -> list[DomainEvent]:
        stmt = (
            select(domain_events)
            .where(
                domain_events.c.aggregate_type == aggregate_type,
                domain_events.c.aggregate_id == aggregate_id,
            )
            .order_by(domain_events.c.occurred_at.asc())
        )
        result = await self._session.execute(stmt)
        return [self._row_to_event(row) for row in result.fetchall()]

    async def read_by_type(
        self, event_type: str, since: datetime | None = None, limit: int = 100
    ) -> list[DomainEvent]:
        stmt = select(domain_events).where(domain_events.c.event_type == event_type)
        if since is not None:
            stmt = stmt.where(domain_events.c.occurred_at >= since)
        stmt = stmt.order_by(domain_events.c.occurred_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return [self._row_to_event(row) for row in result.fetchall()]

    def _row_to_event(self, row) -> DomainEvent:
        mapping = row._mapping
        data = mapping["data"] or {}
        metadata = mapping["metadata"] or {}
        return DomainEvent(
            event_id=mapping["event_id"],
            event_type=mapping["event_type"],
            event_version=mapping["event_version"],
            aggregate_id=mapping["aggregate_id"],
            aggregate_type=mapping["aggregate_type"],
            tenant_id=mapping["tenant_id"] or "",
            occurred_at=mapping["occurred_at"],
            data=data if isinstance(data, dict) else {},
            metadata=metadata if isinstance(metadata, dict) else {},
        )
