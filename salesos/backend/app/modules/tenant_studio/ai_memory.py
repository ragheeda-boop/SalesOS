"""STORY-12-03 — CAP-063 AI Memory MVP models (conversation-level only).

Tenant-scoped, opt-in. Not Production GO. DEC-085 untouched.
No Alembic / FORCE RLS. feature_ai_copilot remains False.
No live LLM / RAG GO. Cross-session long-term memory deferred (DEC-007).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

MemoryRole = Literal["user", "assistant", "system"]

# Honesty: retention is conversation-scoped; long-term cross-session deferred.
DEFAULT_MAX_TURNS = 50
DEFAULT_RETENTION_HOURS = 24


class AiMemoryError(ValueError):
    """Invalid AI memory request or isolation violation."""


@dataclass(frozen=True)
class MemoryTurn:
    role: str
    content: str
    created_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at,
        }


@dataclass
class ConversationMemory:
    """Single conversation memory envelope (tenant + conversation scoped)."""

    id: str
    tenant_id: str
    conversation_id: str
    turns: list[MemoryTurn] = field(default_factory=list)
    provider_cache_key: str = ""
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "conversation_id": self.conversation_id,
            "turns": [t.as_dict() for t in self.turns],
            "turn_count": len(self.turns),
            "provider_cache_key": self.provider_cache_key,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "scope": "conversation",
        }


@dataclass
class TenantMemorySettings:
    """Opt-in AI Memory settings per tenant (default off)."""

    tenant_id: str
    enabled: bool = False
    max_turns: int = DEFAULT_MAX_TURNS
    retention_hours: int = DEFAULT_RETENTION_HOURS
    updated_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "enabled": self.enabled,
            "max_turns": self.max_turns,
            "retention_hours": self.retention_hours,
            "updated_at": self.updated_at,
            "opt_in": True,
            "cross_session": False,
            "feature_ai_copilot": False,
        }


def normalize_conversation_id(conversation_id: str) -> str:
    cid = (conversation_id or "").strip()
    if not cid:
        raise AiMemoryError("conversation_id required")
    if len(cid) > 128:
        raise AiMemoryError("conversation_id too long")
    return cid


def normalize_role(role: str) -> str:
    r = (role or "").strip().lower()
    if r not in {"user", "assistant", "system"}:
        raise AiMemoryError("role must be user|assistant|system")
    return r


def normalize_content(content: str) -> str:
    text = (content or "").strip()
    if not text:
        raise AiMemoryError("content required")
    if len(text) > 8000:
        raise AiMemoryError("content too long")
    return text
