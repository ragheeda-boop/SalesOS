"""Postgres-backed episodic memory store.

CI-19 Wave 2 Core (no sqlalchemy.text)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    DateTime,
    Integer,
    String,
    Text,
    and_,
    column,
    delete,
    func,
    select,
    table,
    true,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert

from .base import MemoryEntry, MemoryScope, MemoryStore

# Lightweight table()/column() — avoid private MetaData island (EAB-001-P1-DRIFT-01).
# DML stub only; not copied onto Base (DEC-156 would be required for that merge).
episodic_memory = table(
    "episodic_memory",
    column("id", String(64)),
    column("agent_id", String(128)),
    column("scope", String(64)),
    column("type", String(64)),
    column("content", Text),
    column("metadata", JSONB),
    column("timestamp", DateTime(timezone=True)),
    column("ttl_seconds", Integer),
    column("session_id", String(128)),
    column("conversation_id", String(128)),
)


def _query_where(
    *,
    agent_id: str | None = None,
    scope: MemoryScope | None = None,
    session_id: str | None = None,
    conversation_id: str | None = None,
    since: datetime | None = None,
):
    conditions = []
    if agent_id is not None:
        conditions.append(episodic_memory.c.agent_id == agent_id)
    if scope is not None:
        conditions.append(episodic_memory.c.scope == scope.value)
    if session_id is not None:
        conditions.append(episodic_memory.c.session_id == session_id)
    if conversation_id is not None:
        conditions.append(episodic_memory.c.conversation_id == conversation_id)
    if since is not None:
        conditions.append(episodic_memory.c.timestamp >= since)
    return and_(*conditions) if conditions else true()


class PostgresMemoryStore(MemoryStore):
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def store(self, entry: MemoryEntry) -> None:
        if not entry.id:
            entry.id = uuid.uuid4().hex[:12]
        stmt = pg_insert(episodic_memory).values(
            id=entry.id,
            agent_id=entry.agent_id,
            scope=entry.scope.value,
            type=entry.type.value,
            content=entry.content,
            metadata=entry.metadata or {},
            timestamp=entry.timestamp,
            ttl_seconds=entry.ttl_seconds,
            session_id=entry.session_id,
            conversation_id=entry.conversation_id,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[episodic_memory.c.id],
            set_={
                "content": stmt.excluded.content,
                "metadata": stmt.excluded["metadata"],
                "ttl_seconds": stmt.excluded.ttl_seconds,
            },
        )
        async with self._session_factory() as session:
            await session.execute(stmt)
            await session.commit()

    async def get(self, entry_id: str) -> MemoryEntry | None:
        async with self._session_factory() as session:
            row = await session.execute(
                select(episodic_memory).where(episodic_memory.c.id == entry_id)
            )
            data = row.mappings().first()
            return self._row_to_entry(dict(data)) if data else None

    async def query(
        self,
        agent_id: str | None = None,
        scope: MemoryScope | None = None,
        session_id: str | None = None,
        conversation_id: str | None = None,
        limit: int = 50,
        since: datetime | None = None,
    ) -> list[MemoryEntry]:
        where = _query_where(
            agent_id=agent_id,
            scope=scope,
            session_id=session_id,
            conversation_id=conversation_id,
            since=since,
        )
        stmt = (
            select(episodic_memory)
            .where(where)
            .order_by(episodic_memory.c.timestamp.desc())
            .limit(limit)
        )
        async with self._session_factory() as session:
            rows = await session.execute(stmt)
            return [self._row_to_entry(dict(r)) for r in rows.mappings().all()]

    async def delete(self, entry_id: str) -> bool:
        async with self._session_factory() as session:
            result = await session.execute(
                delete(episodic_memory).where(episodic_memory.c.id == entry_id)
            )
            await session.commit()
            return result.rowcount > 0

    async def clear(self, agent_id: str | None = None, scope: MemoryScope | None = None) -> int:
        where = _query_where(agent_id=agent_id, scope=scope)
        async with self._session_factory() as session:
            result = await session.execute(delete(episodic_memory).where(where))
            await session.commit()
            return result.rowcount

    async def cleanup_expired(self) -> int:
        ttl = episodic_memory.c.ttl_seconds
        # timestamp + make_interval(secs => ttl_seconds) < NOW()
        expiry = episodic_memory.c.timestamp + func.make_interval(0, 0, 0, 0, 0, 0, ttl)
        stmt = delete(episodic_memory).where(
            ttl.is_not(None),
            expiry < func.now(),
        )
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount

    def _row_to_entry(self, data: dict[str, Any]) -> MemoryEntry:
        return MemoryEntry(
            id=data["id"],
            agent_id=data["agent_id"],
            scope=MemoryScope(data["scope"]),
            type=data.get("type", "message"),
            content=data.get("content", ""),
            metadata=data.get("metadata") or {},
            timestamp=data.get("timestamp") or datetime.now(timezone.utc),
            ttl_seconds=data.get("ttl_seconds"),
            session_id=data.get("session_id"),
            conversation_id=data.get("conversation_id"),
        )
