"""STORY-12-01 — In-memory Prompt Library store (no Alembic / FORCE RLS)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.modules.tenant_studio.prompt_library import (
    PromptLibraryEntry,
    PromptLibraryError,
    PromptVersionRecord,
    normalize_key,
    normalize_template,
    normalize_version,
)


@dataclass
class MemPromptLibraryStore:
    """Tenant-scoped Prompt Library for CAP-089 (extends CAP-023)."""

    _by_id: dict[str, PromptLibraryEntry] = field(default_factory=dict)

    def create(
        self,
        *,
        tenant_id: str,
        name: str,
        key: str,
        template: str,
        system: str = "",
        version: str = "1.0.0",
        changelog: str = "initial",
        domain: str = "gtm",
        category: str = "general",
        entry_id: str | None = None,
    ) -> PromptLibraryEntry:
        tid = (tenant_id or "").strip()
        if not tid:
            raise PromptLibraryError("tenant_id required")
        nm = (name or "").strip()
        if not nm:
            raise PromptLibraryError("name required")
        k = normalize_key(key)
        # uniqueness per tenant key
        for row in self._by_id.values():
            if row.tenant_id == tid and row.key == k:
                raise PromptLibraryError(f"prompt key already exists: {k}")

        ver = normalize_version(version)
        tmpl = normalize_template(template)
        now = datetime.now(UTC).isoformat()
        rid = (entry_id or "").strip() or uuid.uuid4().hex[:12]
        if rid in self._by_id:
            raise PromptLibraryError("entry id already exists")

        record = PromptVersionRecord(
            version=ver,
            template=tmpl,
            system=(system or "").strip()[:8000],
            changelog=(changelog or "initial").strip()[:500] or "initial",
            created_at=now,
        )
        entry = PromptLibraryEntry(
            id=rid,
            tenant_id=tid,
            name=nm,
            key=k,
            active_version=ver,
            versions=[record],
            domain=(domain or "gtm").strip() or "gtm",
            category=(category or "general").strip() or "general",
            schema_version=1,
            created_at=now,
            updated_at=now,
        )
        self._by_id[entry.id] = entry
        return entry

    def add_version(
        self,
        *,
        tenant_id: str,
        entry_id: str,
        template: str,
        version: str,
        system: str = "",
        changelog: str = "",
        activate: bool = True,
    ) -> PromptLibraryEntry:
        entry = self.get(entry_id, tenant_id=tenant_id)
        if entry is None:
            raise PromptLibraryError("prompt entry not found")
        ver = normalize_version(version)
        if any(v.version == ver for v in entry.versions):
            raise PromptLibraryError(f"version already exists: {ver}")
        tmpl = normalize_template(template)
        now = datetime.now(UTC).isoformat()
        record = PromptVersionRecord(
            version=ver,
            template=tmpl,
            system=(system or "").strip()[:8000],
            changelog=(changelog or f"version {ver}").strip()[:500],
            created_at=now,
        )
        entry.versions.append(record)
        if activate:
            entry.active_version = ver
        entry.schema_version += 1
        entry.updated_at = now
        return entry

    def rollback(
        self,
        *,
        tenant_id: str,
        entry_id: str,
        version: str,
    ) -> PromptLibraryEntry:
        entry = self.get(entry_id, tenant_id=tenant_id)
        if entry is None:
            raise PromptLibraryError("prompt entry not found")
        ver = normalize_version(version)
        if not any(v.version == ver for v in entry.versions):
            raise PromptLibraryError(f"version not found: {ver}")
        entry.active_version = ver
        entry.schema_version += 1
        entry.updated_at = datetime.now(UTC).isoformat()
        return entry

    def update_meta(
        self,
        *,
        tenant_id: str,
        entry_id: str,
        name: str | None = None,
        domain: str | None = None,
        category: str | None = None,
    ) -> PromptLibraryEntry:
        entry = self.get(entry_id, tenant_id=tenant_id)
        if entry is None:
            raise PromptLibraryError("prompt entry not found")
        if name is not None:
            nm = name.strip()
            if not nm:
                raise PromptLibraryError("name required")
            entry.name = nm
        if domain is not None:
            entry.domain = domain.strip() or entry.domain
        if category is not None:
            entry.category = category.strip() or entry.category
        entry.schema_version += 1
        entry.updated_at = datetime.now(UTC).isoformat()
        return entry

    def get(self, entry_id: str, *, tenant_id: str) -> PromptLibraryEntry | None:
        row = self._by_id.get(str(entry_id))
        if row is None or row.tenant_id != str(tenant_id):
            return None
        return row

    def list_for_tenant(self, *, tenant_id: str) -> list[PromptLibraryEntry]:
        tid = str(tenant_id)
        return sorted(
            [r for r in self._by_id.values() if r.tenant_id == tid],
            key=lambda r: r.updated_at or r.created_at or "",
            reverse=True,
        )

    def delete(self, entry_id: str, *, tenant_id: str) -> bool:
        row = self.get(entry_id, tenant_id=tenant_id)
        if row is None:
            return False
        del self._by_id[row.id]
        return True


DEFAULT_PROMPT_LIBRARY_STORE = MemPromptLibraryStore()
