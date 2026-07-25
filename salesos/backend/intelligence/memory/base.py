from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class MemoryScope(str, Enum):
    WORKING = "working"
    SESSION = "session"
    CONVERSATION = "conversation"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


class MemoryEntryType(str, Enum):
    MESSAGE = "message"
    CONTEXT = "context"
    FACT = "fact"
    OBSERVATION = "observation"
    DECISION = "decision"
    ERROR = "error"


@dataclass
class MemoryEntry:
    id: str
    agent_id: str
    scope: MemoryScope
    type: MemoryEntryType
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_seconds: int | None = None
    embedding: list[float] | None = None
    session_id: str | None = None
    conversation_id: str | None = None


class MemoryStore(ABC):
    @abstractmethod
    async def store(self, entry: MemoryEntry) -> None:
        ...

    @abstractmethod
    async def get(self, entry_id: str) -> MemoryEntry | None:
        ...

    @abstractmethod
    async def query(
        self,
        agent_id: str | None = None,
        scope: MemoryScope | None = None,
        session_id: str | None = None,
        conversation_id: str | None = None,
        limit: int = 50,
        since: datetime | None = None,
    ) -> list[MemoryEntry]:
        ...

    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        ...

    @abstractmethod
    async def clear(self, agent_id: str | None = None, scope: MemoryScope | None = None) -> int:
        ...

    @abstractmethod
    async def cleanup_expired(self) -> int:
        ...
