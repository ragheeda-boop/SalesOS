from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from .base import MemoryEntry, MemoryEntryType, MemoryScope, MemoryStore


class SessionMemory:
    """Session-scoped memory that persists for the duration of a user session.

    Session memory is tied to a session_id and survives individual
    agent executions within the same session.
    """

    def __init__(self, store: MemoryStore, session_id: str, agent_id: str | None = None):
        self._store = store
        self._session_id = session_id
        self._agent_id = agent_id

    async def store_context(self, key: str, value: Any, metadata: dict[str, Any] | None = None) -> MemoryEntry:
        entry = MemoryEntry(
            id=f"sm-{uuid.uuid4().hex[:8]}",
            agent_id=self._agent_id or "system",
            scope=MemoryScope.SESSION,
            type=MemoryEntryType.CONTEXT,
            content=str(value),
            metadata={"key": key, **(metadata or {})},
            timestamp=datetime.now(timezone.utc),
            session_id=self._session_id,
        )
        await self._store.store(entry)
        return entry

    async def get_context(self, key: str) -> str | None:
        entries = await self._store.query(
            scope=MemoryScope.SESSION,
            session_id=self._session_id,
            limit=100,
        )
        for e in entries:
            if e.metadata.get("key") == key:
                return e.content
        return None

    async def get_all_context(self) -> dict[str, str]:
        entries = await self._store.query(
            scope=MemoryScope.SESSION,
            session_id=self._session_id,
            limit=200,
        )
        return {e.metadata.get("key", e.id): e.content for e in entries}

    async def add_decision(self, decision: str, outcome: str | None = None, metadata: dict[str, Any] | None = None) -> MemoryEntry:
        entry = MemoryEntry(
            id=f"sd-{uuid.uuid4().hex[:8]}",
            agent_id=self._agent_id or "system",
            scope=MemoryScope.SESSION,
            type=MemoryEntryType.DECISION,
            content=decision,
            metadata={"outcome": outcome, **(metadata or {})},
            timestamp=datetime.now(timezone.utc),
            session_id=self._session_id,
        )
        await self._store.store(entry)
        return entry

    async def clear(self) -> int:
        return await self._store.clear(scope=MemoryScope.SESSION)
