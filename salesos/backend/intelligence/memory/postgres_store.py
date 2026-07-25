from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .base import MemoryEntry, MemoryScope, MemoryStore


class PostgresMemoryStore(MemoryStore):
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def store(self, entry: MemoryEntry) -> None:
        if not entry.id:
            entry.id = uuid.uuid4().hex[:12]
        async with self._session_factory() as session:
            await session.execute(
                text("""
                    INSERT INTO episodic_memory (id, agent_id, scope, type, content, metadata, timestamp, ttl_seconds, session_id, conversation_id)
                    VALUES (:id, :agent_id, :scope, :type, :content, :metadata::jsonb, :timestamp, :ttl_seconds, :session_id, :conversation_id)
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata,
                        ttl_seconds = EXCLUDED.ttl_seconds
                """),
                {
                    "id": entry.id,
                    "agent_id": entry.agent_id,
                    "scope": entry.scope.value,
                    "type": entry.type.value,
                    "content": entry.content,
                    "metadata": json.dumps(entry.metadata),
                    "timestamp": entry.timestamp,
                    "ttl_seconds": entry.ttl_seconds,
                    "session_id": entry.session_id,
                    "conversation_id": entry.conversation_id,
                },
            )
            await session.commit()

    async def get(self, entry_id: str) -> MemoryEntry | None:
        async with self._session_factory() as session:
            row = await session.execute(
                text("SELECT * FROM episodic_memory WHERE id = :id"),
                {"id": entry_id},
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
        conditions = []
        params: dict[str, Any] = {}

        if agent_id:
            conditions.append("agent_id = :agent_id")
            params["agent_id"] = agent_id
        if scope:
            conditions.append("scope = :scope")
            params["scope"] = scope.value
        if session_id:
            conditions.append("session_id = :session_id")
            params["session_id"] = session_id
        if conversation_id:
            conditions.append("conversation_id = :conversation_id")
            params["conversation_id"] = conversation_id
        if since:
            conditions.append("timestamp >= :since")
            params["since"] = since

        where = " AND ".join(conditions) if conditions else "TRUE"
        sql = f"SELECT * FROM episodic_memory WHERE {where} ORDER BY timestamp DESC LIMIT :limit"
        params["limit"] = limit

        async with self._session_factory() as session:
            rows = await session.execute(text(sql), params)
            return [self._row_to_entry(dict(r)) for r in rows.mappings().all()]

    async def delete(self, entry_id: str) -> bool:
        async with self._session_factory() as session:
            result = await session.execute(
                text("DELETE FROM episodic_memory WHERE id = :id"),
                {"id": entry_id},
            )
            await session.commit()
            return result.rowcount > 0

    async def clear(self, agent_id: str | None = None, scope: MemoryScope | None = None) -> int:
        conditions = []
        params: dict[str, Any] = {}

        if agent_id:
            conditions.append("agent_id = :agent_id")
            params["agent_id"] = agent_id
        if scope:
            conditions.append("scope = :scope")
            params["scope"] = scope.value

        where = " AND ".join(conditions) if conditions else "TRUE"
        sql = f"DELETE FROM episodic_memory WHERE {where}"

        async with self._session_factory() as session:
            result = await session.execute(text(sql), params)
            await session.commit()
            return result.rowcount

    async def cleanup_expired(self) -> int:
        async with self._session_factory() as session:
            result = await session.execute(
                text("""
                    DELETE FROM episodic_memory
                    WHERE ttl_seconds IS NOT NULL
                    AND (timestamp + make_interval(secs => ttl_seconds)) < NOW()
                """),
            )
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
