from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from .base import MemoryEntry, MemoryEntryType, MemoryScope, MemoryStore


class ConversationMemory:
    """Conversation memory that tracks message history within a conversation.

    Used by agents and copilot to maintain conversational context.
    """

    def __init__(self, store: MemoryStore, conversation_id: str, agent_id: str | None = None):
        self._store = store
        self._conversation_id = conversation_id
        self._agent_id = agent_id

    async def add_message(self, role: str, content: str, metadata: dict[str, Any] | None = None) -> MemoryEntry:
        entry = MemoryEntry(
            id=f"msg-{uuid.uuid4().hex[:8]}",
            agent_id=self._agent_id or "system",
            scope=MemoryScope.CONVERSATION,
            type=MemoryEntryType.MESSAGE,
            content=content,
            metadata={"role": role, **(metadata or {})},
            timestamp=datetime.now(timezone.utc),
            conversation_id=self._conversation_id,
        )
        await self._store.store(entry)
        return entry

    async def get_history(self, limit: int = 50, since: datetime | None = None) -> list[dict[str, str]]:
        entries = await self._store.query(
            scope=MemoryScope.CONVERSATION,
            conversation_id=self._conversation_id,
            limit=limit,
            since=since,
        )
        entries.reverse()
        return [
            {"role": e.metadata.get("role", "user"), "content": e.content, "timestamp": e.timestamp.isoformat()}
            for e in entries
        ]

    async def get_context_messages(self, limit: int = 20) -> list[dict[str, str]]:
        entries = await self._store.query(
            scope=MemoryScope.CONVERSATION,
            conversation_id=self._conversation_id,
            limit=limit,
        )
        entries.reverse()
        return [
            {"role": e.metadata.get("role", "user"), "content": e.content}
            for e in entries
        ]

    async def add_fact(self, fact: str, metadata: dict[str, Any] | None = None) -> MemoryEntry:
        entry = MemoryEntry(
            id=f"fact-{uuid.uuid4().hex[:8]}",
            agent_id=self._agent_id or "system",
            scope=MemoryScope.CONVERSATION,
            type=MemoryEntryType.FACT,
            content=fact,
            metadata=metadata or {},
            timestamp=datetime.now(timezone.utc),
            conversation_id=self._conversation_id,
        )
        await self._store.store(entry)
        return entry

    async def get_facts(self) -> list[str]:
        entries = await self._store.query(
            scope=MemoryScope.CONVERSATION,
            conversation_id=self._conversation_id,
            limit=100,
        )
        return [e.content for e in entries if e.type == MemoryEntryType.FACT]

    async def clear(self) -> int:
        return await self._store.clear(scope=MemoryScope.CONVERSATION)
