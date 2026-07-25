from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from .base import MemoryEntry, MemoryScope, MemoryStore


class InMemoryMemoryStore(MemoryStore):
    def __init__(self):
        self._entries: dict[str, MemoryEntry] = {}

    async def store(self, entry: MemoryEntry) -> None:
        if not entry.id:
            entry.id = uuid.uuid4().hex[:12]
        self._entries[entry.id] = entry

    async def get(self, entry_id: str) -> MemoryEntry | None:
        return self._entries.get(entry_id)

    async def query(
        self,
        agent_id: str | None = None,
        scope: MemoryScope | None = None,
        session_id: str | None = None,
        conversation_id: str | None = None,
        limit: int = 50,
        since: datetime | None = None,
    ) -> list[MemoryEntry]:
        results = list(self._entries.values())

        if agent_id:
            results = [e for e in results if e.agent_id == agent_id]
        if scope:
            results = [e for e in results if e.scope == scope]
        if session_id:
            results = [e for e in results if e.session_id == session_id]
        if conversation_id:
            results = [e for e in results if e.conversation_id == conversation_id]
        if since:
            results = [e for e in results if e.timestamp >= since]

        results.sort(key=lambda e: e.timestamp, reverse=True)
        return results[:limit]

    async def delete(self, entry_id: str) -> bool:
        return self._entries.pop(entry_id, None) is not None

    async def clear(self, agent_id: str | None = None, scope: MemoryScope | None = None) -> int:
        if not agent_id and not scope:
            count = len(self._entries)
            self._entries.clear()
            return count

        to_delete = [
            eid for eid, e in self._entries.items()
            if (agent_id is None or e.agent_id == agent_id)
            and (scope is None or e.scope == scope)
        ]
        for eid in to_delete:
            del self._entries[eid]
        return len(to_delete)

    async def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc)
        to_delete = []
        for eid, e in self._entries.items():
            if e.ttl_seconds and e.timestamp:
                age = (now - e.timestamp).total_seconds()
                if age > e.ttl_seconds:
                    to_delete.append(eid)
        for eid in to_delete:
            del self._entries[eid]
        return len(to_delete)
