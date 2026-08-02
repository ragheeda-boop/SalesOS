"""STORY-12-03 — AI Memory MVP (conversation-level + adversarial isolation)."""

from __future__ import annotations

import pytest

from app.config import settings
from app.modules.tenant_studio.ai_memory import AiMemoryError, ConversationMemory
from app.modules.tenant_studio.ai_memory_engine import (
    adversarial_probe_cross_tenant_cache,
    provider_cache_key,
)
from app.modules.tenant_studio.ai_memory_store import MemAiMemoryStore


def test_opt_in_required_before_write() -> None:
    store = MemAiMemoryStore()
    with pytest.raises(AiMemoryError, match="opt-in"):
        store.append_turn(
            tenant_id="t1",
            conversation_id="c1",
            role="user",
            content="hello",
        )


def test_conversation_round_trip_and_delete() -> None:
    store = MemAiMemoryStore()
    store.set_settings(tenant_id="t1", enabled=True, max_turns=3)
    a = store.append_turn(
        tenant_id="t1",
        conversation_id="conv-a",
        role="user",
        content="hi",
    )
    b = store.append_turn(
        tenant_id="t1",
        conversation_id="conv-a",
        role="assistant",
        content="hello back",
    )
    assert a.id == b.id
    assert len(b.turns) == 2
    got = store.get_conversation(tenant_id="t1", conversation_id="conv-a")
    assert got is not None
    assert len(got.turns) == 2
    assert store.delete_conversation(tenant_id="t1", conversation_id="conv-a") is True
    assert store.get_conversation(tenant_id="t1", conversation_id="conv-a") is None


def test_max_turns_trim() -> None:
    store = MemAiMemoryStore()
    store.set_settings(tenant_id="t1", enabled=True, max_turns=2)
    store.append_turn(tenant_id="t1", conversation_id="c", role="user", content="1")
    store.append_turn(tenant_id="t1", conversation_id="c", role="user", content="2")
    row = store.append_turn(tenant_id="t1", conversation_id="c", role="user", content="3")
    assert len(row.turns) == 2
    assert row.turns[0].content == "2"
    assert row.turns[1].content == "3"


def test_adversarial_cross_tenant_db_isolation() -> None:
    store = MemAiMemoryStore()
    store.set_settings(tenant_id="owner", enabled=True)
    store.set_settings(tenant_id="attacker", enabled=True)
    store.append_turn(
        tenant_id="owner",
        conversation_id="shared-cid",
        role="user",
        content="secret-owner",
    )
    assert store.get_conversation(tenant_id="attacker", conversation_id="shared-cid") is None
    report = store.adversarial_isolation_report(
        owner_tenant_id="owner",
        attacker_tenant_id="attacker",
        conversation_id="shared-cid",
    )
    assert report["suite_pass"] is True
    assert report["db_isolation_ok"] is True
    assert report["attacker_cache_read_blocked"] is True
    assert report["keys_collide"] is False


def test_provider_cache_keys_differ_by_tenant() -> None:
    a = provider_cache_key(tenant_id="a", conversation_id="c1")
    b = provider_cache_key(tenant_id="b", conversation_id="c1")
    assert a != b
    probe = adversarial_probe_cross_tenant_cache(
        owner_tenant_id="a",
        attacker_tenant_id="b",
        conversation_id="c1",
    )
    assert probe["isolation_ok"] is True


def test_feature_ai_copilot_stays_false() -> None:
    assert settings.feature_ai_copilot is False


def test_settings_default_disabled() -> None:
    store = MemAiMemoryStore()
    s = store.get_settings(tenant_id="fresh")
    assert s.enabled is False
    assert s.as_dict()["cross_session"] is False


def test_encryption_envelope_tenant_bound() -> None:
    from app.modules.tenant_studio.ai_memory_crypto import decrypt_content, encrypt_content

    env = encrypt_content(tenant_id="t-a", plaintext="secret")
    assert env["alg"] == "fixture-hmac-sha256-v1"
    assert decrypt_content(tenant_id="t-a", envelope=env) == "secret"
    with pytest.raises(AiMemoryError, match="tenant boundary"):
        decrypt_content(tenant_id="t-b", envelope=env)


def test_retention_purge_expires_conversation() -> None:
    from datetime import UTC, datetime, timedelta

    store = MemAiMemoryStore()
    store.set_settings(tenant_id="t1", enabled=True, retention_hours=1)
    row = store.append_turn(
        tenant_id="t1",
        conversation_id="old",
        role="user",
        content="stale",
    )
    # Force updated_at into the past beyond retention.
    stale = datetime.now(UTC) - timedelta(hours=2)
    store._by_conv[("t1", "old")] = ConversationMemory(
        id=row.id,
        tenant_id="t1",
        conversation_id="old",
        turns=list(row.turns),
        provider_cache_key=row.provider_cache_key,
        schema_version=row.schema_version,
        created_at=row.created_at,
        updated_at=stale.isoformat(),
    )
    assert store.get_conversation(tenant_id="t1", conversation_id="old") is None
