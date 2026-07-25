"""Memory tests — store, working, session, conversation, retrieval."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta

from intelligence.memory import (
    InMemoryMemoryStore,
    WorkingMemory,
    SessionMemory,
    ConversationMemory,
    MemoryRetrieval,
    MemoryEntry,
    MemoryScope,
    MemoryEntryType,
)


@pytest.fixture
def store():
    return InMemoryMemoryStore()


# ── InMemoryMemoryStore ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_store_and_get(store):
    entry = MemoryEntry(id="e1", agent_id="agent-1", scope=MemoryScope.WORKING, type=MemoryEntryType.CONTEXT, content="test data")
    await store.store(entry)
    retrieved = await store.get("e1")
    assert retrieved is not None
    assert retrieved.content == "test data"


@pytest.mark.asyncio
async def test_get_nonexistent(store):
    assert await store.get("nonexistent") is None


@pytest.mark.asyncio
async def test_query_by_agent(store):
    await store.store(MemoryEntry(id="e1", agent_id="agent-1", scope=MemoryScope.WORKING, type=MemoryEntryType.CONTEXT, content="data 1"))
    await store.store(MemoryEntry(id="e2", agent_id="agent-2", scope=MemoryScope.WORKING, type=MemoryEntryType.CONTEXT, content="data 2"))
    results = await store.query(agent_id="agent-1")
    assert len(results) == 1
    assert results[0].id == "e1"


@pytest.mark.asyncio
async def test_query_by_scope(store):
    await store.store(MemoryEntry(id="e1", agent_id="agent-1", scope=MemoryScope.WORKING, type=MemoryEntryType.CONTEXT, content="working"))
    await store.store(MemoryEntry(id="e2", agent_id="agent-1", scope=MemoryScope.SESSION, type=MemoryEntryType.CONTEXT, content="session"))
    results = await store.query(scope=MemoryScope.SESSION)
    assert len(results) == 1
    assert results[0].id == "e2"


@pytest.mark.asyncio
async def test_delete(store):
    await store.store(MemoryEntry(id="e1", agent_id="agent-1", scope=MemoryScope.WORKING, type=MemoryEntryType.CONTEXT, content="data"))
    assert await store.delete("e1") is True
    assert await store.get("e1") is None
    assert await store.delete("e1") is False


@pytest.mark.asyncio
async def test_clear_all(store):
    await store.store(MemoryEntry(id="e1", agent_id="agent-1", scope=MemoryScope.WORKING, type=MemoryEntryType.CONTEXT, content="data"))
    await store.store(MemoryEntry(id="e2", agent_id="agent-2", scope=MemoryScope.SESSION, type=MemoryEntryType.CONTEXT, content="data"))
    count = await store.clear()
    assert count == 2
    assert len(await store.query()) == 0


@pytest.mark.asyncio
async def test_clear_by_agent(store):
    await store.store(MemoryEntry(id="e1", agent_id="agent-1", scope=MemoryScope.WORKING, type=MemoryEntryType.CONTEXT, content="data"))
    await store.store(MemoryEntry(id="e2", agent_id="agent-2", scope=MemoryScope.WORKING, type=MemoryEntryType.CONTEXT, content="data"))
    count = await store.clear(agent_id="agent-1")
    assert count == 1


@pytest.mark.asyncio
async def test_cleanup_expired(store):
    old_time = datetime.now(timezone.utc) - timedelta(seconds=100)
    await store.store(MemoryEntry(id="e1", agent_id="agent-1", scope=MemoryScope.WORKING, type=MemoryEntryType.CONTEXT, content="expired", ttl_seconds=10, timestamp=old_time))
    await store.store(MemoryEntry(id="e2", agent_id="agent-1", scope=MemoryScope.WORKING, type=MemoryEntryType.CONTEXT, content="fresh", ttl_seconds=3600))
    count = await store.cleanup_expired()
    assert count == 1
    assert await store.get("e2") is not None


# ── WorkingMemory ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_working_memory_set_and_get(store):
    wm = WorkingMemory(store, agent_id="agent-1", session_id="session-1")
    await wm.set("user_name", "Ahmed")
    value = await wm.get("user_name")
    assert value == "Ahmed"


@pytest.mark.asyncio
async def test_working_memory_get_missing(store):
    wm = WorkingMemory(store, agent_id="agent-1")
    assert await wm.get("nonexistent") is None


@pytest.mark.asyncio
async def test_working_memory_get_all(store):
    wm = WorkingMemory(store, agent_id="agent-1")
    await wm.set("key1", "val1")
    await wm.set("key2", "val2")
    all_data = await wm.get_all()
    assert all_data["key1"] == "val1"
    assert all_data["key2"] == "val2"


@pytest.mark.asyncio
async def test_working_memory_observation(store):
    wm = WorkingMemory(store, agent_id="agent-1")
    entry = await wm.add_observation("User seemed confused")
    assert entry.type == MemoryEntryType.OBSERVATION
    assert entry.content == "User seemed confused"


@pytest.mark.asyncio
async def test_working_memory_clear(store):
    wm = WorkingMemory(store, agent_id="agent-1")
    await wm.set("key1", "val1")
    count = await wm.clear()
    assert count == 1


# ── SessionMemory ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_session_memory_context(store):
    sm = SessionMemory(store, session_id="session-1")
    await sm.store_context("language", "Arabic")
    value = await sm.get_context("language")
    assert value == "Arabic"


@pytest.mark.asyncio
async def test_session_memory_get_all(store):
    sm = SessionMemory(store, session_id="session-1")
    await sm.store_context("lang", "en")
    await sm.store_context("theme", "dark")
    all_ctx = await sm.get_all_context()
    assert all_ctx["lang"] == "en"
    assert all_ctx["theme"] == "dark"


@pytest.mark.asyncio
async def test_session_memory_decision(store):
    sm = SessionMemory(store, session_id="session-1")
    entry = await sm.add_decision("Approved discount", outcome="pending")
    assert entry.type == MemoryEntryType.DECISION
    assert entry.metadata.get("outcome") == "pending"


@pytest.mark.asyncio
async def test_session_memory_clear(store):
    sm = SessionMemory(store, session_id="session-1")
    await sm.store_context("key", "value")
    count = await sm.clear()
    assert count == 1


# ── ConversationMemory ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_conversation_add_message(store):
    cm = ConversationMemory(store, conversation_id="conv-1")
    await cm.add_message("user", "Hello")
    await cm.add_message("assistant", "Hi there")
    history = await cm.get_history()
    assert len(history) == 2
    roles = [h["role"] for h in history]
    assert "user" in roles
    assert "assistant" in roles
    assert history[0]["content"] == "Hello" or history[0]["content"] == "Hi there"


@pytest.mark.asyncio
async def test_conversation_context_messages(store):
    cm = ConversationMemory(store, conversation_id="conv-1")
    await cm.add_message("user", "Q1")
    await cm.add_message("assistant", "A1")
    await cm.add_message("user", "Q2")
    ctx = await cm.get_context_messages(limit=2)
    assert len(ctx) == 2
    roles = [m["role"] for m in ctx]
    assert "user" in roles
    assert "assistant" in roles


@pytest.mark.asyncio
async def test_conversation_facts(store):
    cm = ConversationMemory(store, conversation_id="conv-1")
    await cm.add_fact("Customer prefers email")
    await cm.add_fact("Budget is $50K")
    facts = await cm.get_facts()
    assert len(facts) == 2
    assert any("prefers email" in f for f in facts)


@pytest.mark.asyncio
async def test_conversation_clear(store):
    cm = ConversationMemory(store, conversation_id="conv-1")
    await cm.add_message("user", "test")
    count = await cm.clear()
    assert count == 1


# ── MemoryRetrieval ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_retrieval_search(store):
    cm = ConversationMemory(store, conversation_id="conv-1")
    await cm.add_message("user", "What is the pricing for enterprise?")
    await cm.add_message("assistant", "Enterprise pricing starts at $50K/year")

    retrieval = MemoryRetrieval(store)
    result = await retrieval.search(query="pricing", conversation_id="conv-1")
    assert result.total > 0


@pytest.mark.asyncio
async def test_retrieval_search_no_query(store):
    cm = ConversationMemory(store, conversation_id="conv-1")
    await cm.add_message("user", "Hello")
    retrieval = MemoryRetrieval(store)
    result = await retrieval.search(conversation_id="conv-1")
    assert result.total == 1


@pytest.mark.asyncio
async def test_retrieval_get_recent(store):
    wm = WorkingMemory(store, agent_id="agent-1")
    await wm.set("k1", "v1")
    await wm.set("k2", "v2")
    retrieval = MemoryRetrieval(store)
    result = await retrieval.get_recent(agent_id="agent-1", scope=MemoryScope.WORKING)
    assert result.total == 2


@pytest.mark.asyncio
async def test_retrieval_conversation_context(store):
    cm = ConversationMemory(store, conversation_id="conv-1")
    await cm.add_message("user", "Hi")
    await cm.add_message("assistant", "Hello")
    retrieval = MemoryRetrieval(store)
    result = await retrieval.get_conversation_context("conv-1")
    assert result.total == 2


# ── MemoryEntry defaults ──────────────────────────────────────────────────


def test_memory_entry_defaults():
    entry = MemoryEntry(id="e1", agent_id="agent-1", scope=MemoryScope.WORKING, type=MemoryEntryType.CONTEXT, content="test")
    assert entry.ttl_seconds is None
    assert entry.session_id is None
    assert entry.conversation_id is None
    assert entry.timestamp is not None
