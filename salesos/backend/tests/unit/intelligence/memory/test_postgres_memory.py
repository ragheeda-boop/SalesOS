"""PostgresMemoryStore tests — mocked SQL layer."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest

from intelligence.memory.postgres_store import PostgresMemoryStore
from intelligence.memory.base import MemoryEntry, MemoryScope, MemoryEntryType


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.__aenter__.return_value = session
    return session


@pytest.fixture
def store(mock_session):
    factory = MagicMock(return_value=mock_session)
    return PostgresMemoryStore(session_factory=factory)


@pytest.mark.asyncio
async def test_store_and_get(store, mock_session):
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = {
        "id": "e1",
        "agent_id": "agent-1",
        "scope": "working",
        "type": "context",
        "content": "test data",
        "metadata": {},
        "timestamp": datetime.now(timezone.utc),
        "ttl_seconds": None,
        "session_id": None,
        "conversation_id": None,
    }
    mock_session.execute.return_value = mock_result

    entry = MemoryEntry(id="e1", agent_id="agent-1", scope=MemoryScope.WORKING, type=MemoryEntryType.CONTEXT, content="test data")
    await store.store(entry)

    retrieved = await store.get("e1")
    assert retrieved is not None
    assert retrieved.content == "test data"
    assert retrieved.scope == MemoryScope.WORKING


@pytest.mark.asyncio
async def test_get_nonexistent(store, mock_session):
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    assert await store.get("nonexistent") is None


@pytest.mark.asyncio
async def test_query_by_agent(store, mock_session):
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = [
        {"id": "e1", "agent_id": "agent-1", "scope": "working", "type": "context", "content": "data 1", "metadata": {}, "timestamp": datetime.now(timezone.utc), "ttl_seconds": None, "session_id": None, "conversation_id": None},
    ]
    mock_session.execute.return_value = mock_result

    results = await store.query(agent_id="agent-1")
    assert len(results) == 1
    assert results[0].id == "e1"


@pytest.mark.asyncio
async def test_query_by_scope(store, mock_session):
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = [
        {"id": "e1", "agent_id": "agent-1", "scope": "session", "type": "context", "content": "session data", "metadata": {}, "timestamp": datetime.now(timezone.utc), "ttl_seconds": None, "session_id": "s1", "conversation_id": None},
    ]
    mock_session.execute.return_value = mock_result

    results = await store.query(scope=MemoryScope.SESSION)
    assert len(results) == 1
    assert results[0].scope == MemoryScope.SESSION


@pytest.mark.asyncio
async def test_delete(store, mock_session):
    mock_session.rowcount = 1
    mock_session.execute.return_value = mock_session

    result = await store.delete("e1")
    assert result is True


@pytest.mark.asyncio
async def test_delete_not_found(store, mock_session):
    fake_result = MagicMock()
    fake_result.rowcount = 0
    mock_session.execute.return_value = fake_result

    result = await store.delete("nonexistent")
    assert result is False


@pytest.mark.asyncio
async def test_clear_all(store, mock_session):
    fake_result = MagicMock()
    fake_result.rowcount = 2
    mock_session.execute.return_value = fake_result

    count = await store.clear()
    assert count == 2


@pytest.mark.asyncio
async def test_clear_by_agent(store, mock_session):
    fake_result = MagicMock()
    fake_result.rowcount = 1
    mock_session.execute.return_value = fake_result

    count = await store.clear(agent_id="agent-1")
    assert count == 1


@pytest.mark.asyncio
async def test_cleanup_expired(store, mock_session):
    fake_result = MagicMock()
    fake_result.rowcount = 3
    mock_session.execute.return_value = fake_result

    count = await store.cleanup_expired()
    assert count == 3


@pytest.mark.asyncio
async def test_store_generates_id(store, mock_session):
    entry = MemoryEntry(id="", agent_id="agent-1", scope=MemoryScope.WORKING, type=MemoryEntryType.CONTEXT, content="auto-id")
    await store.store(entry)
    assert entry.id != ""


@pytest.mark.asyncio
async def test_query_with_session_and_conversation(store, mock_session):
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = [
        {"id": "e1", "agent_id": "agent-1", "scope": "conversation", "type": "message", "content": "Hello", "metadata": {}, "timestamp": datetime.now(timezone.utc), "ttl_seconds": None, "session_id": "s1", "conversation_id": "c1"},
    ]
    mock_session.execute.return_value = mock_result

    results = await store.query(session_id="s1", conversation_id="c1")
    assert len(results) == 1
    assert results[0].conversation_id == "c1"


@pytest.mark.asyncio
async def test_query_with_since(store, mock_session):
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    since = datetime.now(timezone.utc) - timedelta(hours=1)
    results = await store.query(since=since)
    assert len(results) == 0
