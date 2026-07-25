from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .base import MemoryEntry, MemoryScope, MemoryStore


@dataclass
class MemoryResult:
    entries: list[MemoryEntry]
    total: int
    query_time_ms: float = 0.0


class MemoryRetrieval:
    """Unified memory retrieval across all memory scopes.

    Provides ranked retrieval with optional recency and relevance scoring.
    Extension point: add semantic search via embedding comparison.
    """

    def __init__(self, store: MemoryStore):
        self._store = store

    async def search(
        self,
        query: str | None = None,
        agent_id: str | None = None,
        scope: MemoryScope | None = None,
        session_id: str | None = None,
        conversation_id: str | None = None,
        limit: int = 50,
        recency_weight: float = 0.3,
    ) -> MemoryResult:
        import time
        start = time.monotonic()

        entries = await self._store.query(
            agent_id=agent_id,
            scope=scope,
            session_id=session_id,
            conversation_id=conversation_id,
            limit=limit * 2,
        )

        if query and entries:
            query_lower = query.lower()
            query_terms = set(query_lower.split())

            scored = []
            for e in entries:
                score = 0.0
                content_lower = e.content.lower()

                if query_lower in content_lower:
                    score += 0.5
                matched_terms = sum(1 for t in query_terms if t in content_lower)
                if query_terms:
                    score += (matched_terms / len(query_terms)) * 0.3

                if e.metadata.get("role") == query_lower:
                    score += 0.1

                if recency_weight > 0:
                    age_hours = (datetime.now(timezone.utc) - e.timestamp).total_seconds() / 3600
                    recency_score = max(0, 1 - (age_hours / 24))
                    score += recency_score * recency_weight

                scored.append((score, e))

            scored.sort(key=lambda x: x[0], reverse=True)
            entries = [e for _, e in scored[:limit]]
        else:
            entries = entries[:limit]

        elapsed = (time.monotonic() - start) * 1000

        return MemoryResult(
            entries=entries,
            total=len(entries),
            query_time_ms=round(elapsed, 2),
        )

    async def get_recent(
        self,
        agent_id: str | None = None,
        scope: MemoryScope | None = None,
        limit: int = 20,
    ) -> MemoryResult:
        entries = await self._store.query(
            agent_id=agent_id,
            scope=scope,
            limit=limit,
        )
        return MemoryResult(entries=entries, total=len(entries))

    async def get_conversation_context(
        self,
        conversation_id: str,
        limit: int = 20,
    ) -> MemoryResult:
        entries = await self._store.query(
            scope=MemoryScope.CONVERSATION,
            conversation_id=conversation_id,
            limit=limit,
        )
        entries.reverse()
        return MemoryResult(entries=entries, total=len(entries))
