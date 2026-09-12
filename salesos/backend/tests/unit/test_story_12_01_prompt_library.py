"""STORY-12-01 — Prompt Library (tenant CRUD + version + rollback)."""

from __future__ import annotations

import pytest

from app.config import settings
from app.modules.tenant_studio.prompt_library import PromptLibraryError, normalize_key
from app.modules.tenant_studio.prompt_library_store import MemPromptLibraryStore


def test_create_version_and_rollback() -> None:
    store = MemPromptLibraryStore()
    entry = store.create(
        tenant_id="pilot-1",
        name="Outreach intro",
        key="gtm.outreach.intro",
        template="Hello {name}",
        version="1.0.0",
    )
    assert entry.active_version == "1.0.0"
    assert len(entry.versions) == 1

    v2 = store.add_version(
        tenant_id="pilot-1",
        entry_id=entry.id,
        template="Hi {name} — v2",
        version="1.1.0",
        activate=True,
    )
    assert v2.active_version == "1.1.0"
    assert len(v2.versions) == 2

    rolled = store.rollback(tenant_id="pilot-1", entry_id=entry.id, version="1.0.0")
    assert rolled.active_version == "1.0.0"
    assert rolled.active_record() is not None
    assert rolled.active_record().template == "Hello {name}"


def test_duplicate_key_rejected() -> None:
    store = MemPromptLibraryStore()
    store.create(
        tenant_id="t1",
        name="A",
        key="shared.key",
        template="x",
    )
    with pytest.raises(PromptLibraryError, match="already exists"):
        store.create(tenant_id="t1", name="B", key="shared.key", template="y")
    # other tenant ok
    other = store.create(tenant_id="t2", name="B", key="shared.key", template="y")
    assert other.tenant_id == "t2"


def test_tenant_isolation() -> None:
    store = MemPromptLibraryStore()
    a = store.create(tenant_id="a", name="A", key="k1", template="t")
    assert store.get(a.id, tenant_id="b") is None
    assert store.list_for_tenant(tenant_id="b") == []
    assert store.delete(a.id, tenant_id="b") is False
    assert store.delete(a.id, tenant_id="a") is True


def test_normalize_key_guards() -> None:
    with pytest.raises(PromptLibraryError):
        normalize_key("  ")
    with pytest.raises(PromptLibraryError):
        normalize_key("bad key!")
    assert normalize_key("Gtm.Outreach") == "gtm.outreach"


def test_feature_ai_copilot_stays_false() -> None:
    assert settings.feature_ai_copilot is False


def test_rollback_unknown_version() -> None:
    store = MemPromptLibraryStore()
    e = store.create(tenant_id="t", name="N", key="k", template="t", version="1.0.0")
    with pytest.raises(PromptLibraryError, match="version not found"):
        store.rollback(tenant_id="t", entry_id=e.id, version="9.9.9")
