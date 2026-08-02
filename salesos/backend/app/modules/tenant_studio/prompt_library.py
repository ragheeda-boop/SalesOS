"""STORY-12-01 — CAP-089 Prompt Library models (tenant-facing, extends CAP-023).

Tenant CRUD + versioning + rollback over Prompt Registry-shaped entries.
Not Production GO. DEC-085 untouched. No Alembic / FORCE RLS.
feature_ai_copilot remains False. No live LLM / RAG GO.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class PromptLibraryError(ValueError):
    """Invalid prompt library entry or version operation."""


@dataclass(frozen=True)
class PromptVersionRecord:
    """Immutable version snapshot for a tenant prompt."""

    version: str
    template: str
    system: str = ""
    changelog: str = ""
    created_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "template": self.template,
            "system": self.system,
            "changelog": self.changelog,
            "created_at": self.created_at,
        }


@dataclass
class PromptLibraryEntry:
    """Tenant-owned prompt library entry (CAP-089 / CAP-023-shaped)."""

    id: str
    tenant_id: str
    name: str
    key: str
    active_version: str
    versions: list[PromptVersionRecord] = field(default_factory=list)
    domain: str = "gtm"
    category: str = "general"
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "key": self.key,
            "active_version": self.active_version,
            "versions": [v.as_dict() for v in self.versions],
            "domain": self.domain,
            "category": self.category,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version_count": len(self.versions),
        }

    def active_record(self) -> PromptVersionRecord | None:
        for v in self.versions:
            if v.version == self.active_version:
                return v
        return self.versions[-1] if self.versions else None


def normalize_key(key: str) -> str:
    k = (key or "").strip().lower().replace(" ", ".")
    if not k:
        raise PromptLibraryError("key required")
    if not all(c.isalnum() or c in "._-" for c in k):
        raise PromptLibraryError("key must be alphanumeric with ._-")
    return k


def normalize_version(version: str) -> str:
    v = (version or "").strip()
    if not v:
        raise PromptLibraryError("version required")
    if len(v) > 32:
        raise PromptLibraryError("version too long")
    return v


def normalize_template(template: str) -> str:
    t = (template or "").strip()
    if not t:
        raise PromptLibraryError("template required")
    if len(t) > 20000:
        raise PromptLibraryError("template too long")
    return t
