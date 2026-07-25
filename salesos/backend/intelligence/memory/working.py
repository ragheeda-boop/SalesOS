from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from .base import MemoryEntry, MemoryEntryType, MemoryScope, MemoryStore


class WorkingMemory:
    """Ephemeral memory for the current agent execution context.

    Working memory is scoped to a single agent execution/task.
    It is not persisted and is cleared when the task completes.
    """

    def __init__(self, store: MemoryStore, agent_id: str, session_id: str | None = None, ttl_seconds: int = 300):
        self._store = store
        self._agent_id = agent_id
        self._session_id = session_id
        self._ttl_seconds = ttl_seconds

    async def set(self, key: str, value: Any, metadata: dict[str, Any] | None = None) -> MemoryEntry:
        entry = MemoryEntry(
            id=f"wm-{uuid.uuid4().hex[:8]}",
            agent_id=self._agent_id,
            scope=MemoryScope.WORKING,
            type=MemoryEntryType.CONTEXT,
            content=str(value),
            metadata={"key": key, **(metadata or {})},
            timestamp=datetime.now(timezone.utc),
            ttl_seconds=self._ttl_seconds,
            session_id=self._session_id,
        )
        await self._store.store(entry)
        return entry

    async def get(self, key: str) -> str | None:
        entries = await self._store.query(
            agent_id=self._agent_id,
            scope=MemoryScope.WORKING,
            session_id=self._session_id,
            limit=50,
        )
        for e in entries:
            if e.metadata.get("key") == key:
                return e.content
        return None

    async def get_all(self) -> dict[str, str]:
        entries = await self._store.query(
            agent_id=self._agent_id,
            scope=MemoryScope.WORKING,
            session_id=self._session_id,
            limit=200,
        )
        return {e.metadata.get("key", e.id): e.content for e in entries}

    async def clear(self) -> int:
        return await self._store.clear(agent_id=self._agent_id, scope=MemoryScope.WORKING)

    async def add_observation(self, observation: str, metadata: dict[str, Any] | None = None) -> MemoryEntry:
        entry = MemoryEntry(
            id=f"obs-{uuid.uuid4().hex[:8]}",
            agent_id=self._agent_id,
            scope=MemoryScope.WORKING,
            type=MemoryEntryType.OBSERVATION,
            content=observation,
            metadata=metadata or {},
            timestamp=datetime.now(timezone.utc),
            ttl_seconds=self._ttl_seconds,
            session_id=self._session_id,
        )
        await self._store.store(entry)
        return entry
