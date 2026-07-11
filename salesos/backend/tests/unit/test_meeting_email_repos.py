"""Tests for PostgresMeetingRepository and PostgresEmailRepository (PostgreSQL)."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from domains.commercial.infrastructure.models import EmailModel, MeetingModel
from domains.commercial.infrastructure.postgres_repositories import (
    PostgresEmailRepository,
    PostgresMeetingRepository,
)
from domains.commercial.meeting.in_memory_repo import InMemoryMeetingRepository
from domains.commercial.email.in_memory_repo import InMemoryEmailRepository


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.delete = AsyncMock()
    return session


class MockResult:
    def __init__(self, rows=None, scalar=None):
        self._rows = rows or []
        self._scalar = scalar

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return MockScalars(self._rows)

    def all(self):
        return self._rows

    def fetchall(self):
        return [(r,) for r in self._rows]


class MockScalars:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class TestPostgresMeetingRepository:
    @pytest.mark.asyncio
    async def test_get_returns_none_when_not_found(self, mock_session):
        mock_session.execute.return_value = MockResult(scalar=None)
        repo = PostgresMeetingRepository(mock_session)
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_model_when_found(self, mock_session):
        meeting = MeetingModel(
            id="m-1", tenant_id="t-1", opportunity_id="opp-1",
            title="Test Meeting", meeting_date=datetime.now(timezone.utc),
        )
        mock_session.execute.return_value = MockResult(scalar=meeting)
        repo = PostgresMeetingRepository(mock_session)
        result = await repo.get("m-1")
        assert result is not None
        assert result.id == "m-1"
        assert result.title == "Test Meeting"

    @pytest.mark.asyncio
    async def test_list_by_opportunity_orders_by_date_desc(self, mock_session):
        mock_session.execute.return_value = MockResult(rows=[])
        repo = PostgresMeetingRepository(mock_session)
        result = await repo.list_by_opportunity("opp-1", "t-1")
        assert result == []

    @pytest.mark.asyncio
    async def test_save_adds_and_flushes(self, mock_session):
        meeting = MeetingModel(
            id="m-2", tenant_id="t-1", opportunity_id="opp-1",
            title="New Meeting", meeting_date=datetime.now(timezone.utc),
        )
        repo = PostgresMeetingRepository(mock_session)
        result = await repo.save(meeting)
        mock_session.add.assert_called_once_with(meeting)
        mock_session.flush.assert_awaited_once()
        assert result.id == meeting.id

    @pytest.mark.asyncio
    async def test_delete_returns_true_when_found(self, mock_session):
        meeting = MeetingModel(id="m-1", tenant_id="t-1", opportunity_id="opp-1", title="X", meeting_date=datetime.now(timezone.utc))
        mock_session.execute.return_value = MockResult(scalar=meeting)
        repo = PostgresMeetingRepository(mock_session)
        result = await repo.delete("m-1")
        assert result is True
        mock_session.delete.assert_called_once_with(meeting)

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_not_found(self, mock_session):
        mock_session.execute.return_value = MockResult(scalar=None)
        repo = PostgresMeetingRepository(mock_session)
        result = await repo.delete("nonexistent")
        assert result is False


class TestPostgresEmailRepository:
    @pytest.mark.asyncio
    async def test_get_returns_none_when_not_found(self, mock_session):
        mock_session.execute.return_value = MockResult(scalar=None)
        repo = PostgresEmailRepository(mock_session)
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_model_when_found(self, mock_session):
        email = EmailModel(
            id="em-1", tenant_id="t-1", opportunity_id="opp-1",
            subject="Test", from_address="a@b.com", sent_at=datetime.now(timezone.utc),
        )
        mock_session.execute.return_value = MockResult(scalar=email)
        repo = PostgresEmailRepository(mock_session)
        result = await repo.get("em-1")
        assert result is not None
        assert result.subject == "Test"

    @pytest.mark.asyncio
    async def test_list_by_opportunity_returns_empty(self, mock_session):
        mock_session.execute.return_value = MockResult(rows=[])
        repo = PostgresEmailRepository(mock_session)
        result = await repo.list_by_opportunity("opp-1", "t-1")
        assert result == []

    @pytest.mark.asyncio
    async def test_save_adds_and_flushes(self, mock_session):
        email = EmailModel(
            id="em-2", tenant_id="t-1", opportunity_id="opp-1",
            subject="New", from_address="a@b.com", sent_at=datetime.now(timezone.utc),
        )
        repo = PostgresEmailRepository(mock_session)
        result = await repo.save(email)
        mock_session.add.assert_called_once_with(email)
        mock_session.flush.assert_awaited_once()
        assert result.id == email.id

    @pytest.mark.asyncio
    async def test_delete_returns_true_when_found(self, mock_session):
        email = EmailModel(id="em-1", tenant_id="t-1", opportunity_id="opp-1", subject="X", from_address="a@b.com", sent_at=datetime.now(timezone.utc))
        mock_session.execute.return_value = MockResult(scalar=email)
        repo = PostgresEmailRepository(mock_session)
        result = await repo.delete("em-1")
        assert result is True
        mock_session.delete.assert_called_once_with(email)


class TestInMemoryMeetingRepository:
    @pytest.mark.asyncio
    async def test_get_returns_none_when_not_found(self):
        repo = InMemoryMeetingRepository()
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_save_and_get(self):
        repo = InMemoryMeetingRepository()
        meeting = MeetingModel(
            id="m-1", tenant_id="t-1", opportunity_id="opp-1",
            title="Test Meeting", meeting_date=datetime.now(timezone.utc),
        )
        await repo.save(meeting)
        result = await repo.get("m-1")
        assert result is not None
        assert result.id == "m-1"
        assert result.title == "Test Meeting"

    @pytest.mark.asyncio
    async def test_list_by_opportunity_filters_by_tenant(self):
        repo = InMemoryMeetingRepository()
        now = datetime.now(timezone.utc)
        m1 = MeetingModel(id="m-1", tenant_id="t-1", opportunity_id="opp-1", title="A", meeting_date=now)
        m2 = MeetingModel(id="m-2", tenant_id="t-2", opportunity_id="opp-1", title="B", meeting_date=now)
        await repo.save(m1)
        await repo.save(m2)
        result = await repo.list_by_opportunity("opp-1", "t-1")
        assert len(result) == 1
        assert result[0].id == "m-1"

    @pytest.mark.asyncio
    async def test_list_by_opportunity_orders_by_date_desc(self):
        repo = InMemoryMeetingRepository()
        now = datetime.now(timezone.utc)
        earlier = MeetingModel(id="m-1", tenant_id="t-1", opportunity_id="opp-1", title="Earlier", meeting_date=now)
        later = MeetingModel(id="m-2", tenant_id="t-1", opportunity_id="opp-1", title="Later", meeting_date=datetime(2025, 1, 1, tzinfo=timezone.utc))
        await repo.save(earlier)
        await repo.save(later)
        result = await repo.list_by_opportunity("opp-1", "t-1")
        assert result[0].id == "m-1"

    @pytest.mark.asyncio
    async def test_list_by_opportunity_respects_limit(self):
        repo = InMemoryMeetingRepository()
        now = datetime.now(timezone.utc)
        for i in range(5):
            await repo.save(MeetingModel(id=f"m-{i}", tenant_id="t-1", opportunity_id="opp-1", title=f"M{i}", meeting_date=now))
        result = await repo.list_by_opportunity("opp-1", "t-1", limit=3)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_delete_returns_true_when_exists(self):
        repo = InMemoryMeetingRepository()
        meeting = MeetingModel(id="m-1", tenant_id="t-1", opportunity_id="opp-1", title="X", meeting_date=datetime.now(timezone.utc))
        await repo.save(meeting)
        result = await repo.delete("m-1")
        assert result is True
        assert await repo.get("m-1") is None

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_not_exists(self):
        repo = InMemoryMeetingRepository()
        result = await repo.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_domain_converts_model(self):
        repo = InMemoryMeetingRepository()
        meeting = MeetingModel(
            id="m-1", tenant_id="t-1", opportunity_id="opp-1",
            title="Test", meeting_date=datetime.now(timezone.utc),
            duration_minutes=30, notes="Some notes", status="completed",
        )
        await repo.save(meeting)
        result = await repo.get_domain("m-1")
        assert result is not None
        assert result.id == "m-1"
        assert result.title == "Test"
        assert result.duration_minutes == 30
        assert result.notes == "Some notes"
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_get_domain_returns_none_when_missing(self):
        repo = InMemoryMeetingRepository()
        result = await repo.get_domain("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_domain_by_opportunity(self):
        repo = InMemoryMeetingRepository()
        now = datetime.now(timezone.utc)
        await repo.save(MeetingModel(id="m-1", tenant_id="t-1", opportunity_id="opp-1", title="A", meeting_date=now))
        results = await repo.list_domain_by_opportunity("opp-1", "t-1")
        assert len(results) == 1
        assert results[0].title == "A"


class TestInMemoryEmailRepository:
    @pytest.mark.asyncio
    async def test_get_returns_none_when_not_found(self):
        repo = InMemoryEmailRepository()
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_save_and_get(self):
        repo = InMemoryEmailRepository()
        email = EmailModel(
            id="em-1", tenant_id="t-1", opportunity_id="opp-1",
            subject="Test", from_address="a@b.com", sent_at=datetime.now(timezone.utc),
        )
        await repo.save(email)
        result = await repo.get("em-1")
        assert result is not None
        assert result.subject == "Test"

    @pytest.mark.asyncio
    async def test_list_by_opportunity_filters_by_tenant(self):
        repo = InMemoryEmailRepository()
        now = datetime.now(timezone.utc)
        e1 = EmailModel(id="em-1", tenant_id="t-1", opportunity_id="opp-1", subject="A", from_address="a@b.com", sent_at=now)
        e2 = EmailModel(id="em-2", tenant_id="t-2", opportunity_id="opp-1", subject="B", from_address="b@b.com", sent_at=now)
        await repo.save(e1)
        await repo.save(e2)
        result = await repo.list_by_opportunity("opp-1", "t-1")
        assert len(result) == 1
        assert result[0].id == "em-1"

    @pytest.mark.asyncio
    async def test_list_by_opportunity_orders_by_date_desc(self):
        repo = InMemoryEmailRepository()
        now = datetime.now(timezone.utc)
        earlier = EmailModel(id="em-1", tenant_id="t-1", opportunity_id="opp-1", subject="Earlier", from_address="a@b.com", sent_at=now)
        later = EmailModel(id="em-2", tenant_id="t-1", opportunity_id="opp-1", subject="Later", from_address="b@b.com", sent_at=datetime(2025, 1, 1, tzinfo=timezone.utc))
        await repo.save(earlier)
        await repo.save(later)
        result = await repo.list_by_opportunity("opp-1", "t-1")
        assert result[0].id == "em-1"

    @pytest.mark.asyncio
    async def test_list_by_opportunity_respects_limit(self):
        repo = InMemoryEmailRepository()
        now = datetime.now(timezone.utc)
        for i in range(5):
            await repo.save(EmailModel(id=f"em-{i}", tenant_id="t-1", opportunity_id="opp-1", subject=f"S{i}", from_address="a@b.com", sent_at=now))
        result = await repo.list_by_opportunity("opp-1", "t-1", limit=3)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_delete_returns_true_when_exists(self):
        repo = InMemoryEmailRepository()
        email = EmailModel(id="em-1", tenant_id="t-1", opportunity_id="opp-1", subject="X", from_address="a@b.com", sent_at=datetime.now(timezone.utc))
        await repo.save(email)
        result = await repo.delete("em-1")
        assert result is True
        assert await repo.get("em-1") is None

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_not_exists(self):
        repo = InMemoryEmailRepository()
        result = await repo.delete("nonexistent")
        assert result is False
