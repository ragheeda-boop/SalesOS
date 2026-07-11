"""Tests for MeetingRepository and EmailRepository (PostgreSQL)."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from domains.commercial.infrastructure.models import EmailModel, MeetingModel
from domains.commercial.infrastructure.postgres_repositories import (
    EmailRepository,
    MeetingRepository,
)


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


class TestMeetingRepository:
    @pytest.mark.asyncio
    async def test_get_returns_none_when_not_found(self, mock_session):
        mock_session.execute.return_value = MockResult(scalar=None)
        repo = MeetingRepository(mock_session)
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_model_when_found(self, mock_session):
        meeting = MeetingModel(
            id="m-1", tenant_id="t-1", opportunity_id="opp-1",
            title="Test Meeting", meeting_date=datetime.now(timezone.utc),
        )
        mock_session.execute.return_value = MockResult(scalar=meeting)
        repo = MeetingRepository(mock_session)
        result = await repo.get("m-1")
        assert result is not None
        assert result.id == "m-1"
        assert result.title == "Test Meeting"

    @pytest.mark.asyncio
    async def test_list_by_opportunity_orders_by_date_desc(self, mock_session):
        mock_session.execute.return_value = MockResult(rows=[])
        repo = MeetingRepository(mock_session)
        result = await repo.list_by_opportunity("opp-1", "t-1")
        assert result == []

    @pytest.mark.asyncio
    async def test_save_adds_and_flushes(self, mock_session):
        meeting = MeetingModel(
            id="m-2", tenant_id="t-1", opportunity_id="opp-1",
            title="New Meeting", meeting_date=datetime.now(timezone.utc),
        )
        repo = MeetingRepository(mock_session)
        result = await repo.save(meeting)
        mock_session.add.assert_called_once_with(meeting)
        mock_session.flush.assert_awaited_once()
        assert result.id == meeting.id

    @pytest.mark.asyncio
    async def test_delete_returns_true_when_found(self, mock_session):
        meeting = MeetingModel(id="m-1", tenant_id="t-1", opportunity_id="opp-1", title="X", meeting_date=datetime.now(timezone.utc))
        mock_session.execute.return_value = MockResult(scalar=meeting)
        repo = MeetingRepository(mock_session)
        result = await repo.delete("m-1")
        assert result is True
        mock_session.delete.assert_called_once_with(meeting)

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_not_found(self, mock_session):
        mock_session.execute.return_value = MockResult(scalar=None)
        repo = MeetingRepository(mock_session)
        result = await repo.delete("nonexistent")
        assert result is False


class TestEmailRepository:
    @pytest.mark.asyncio
    async def test_get_returns_none_when_not_found(self, mock_session):
        mock_session.execute.return_value = MockResult(scalar=None)
        repo = EmailRepository(mock_session)
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_model_when_found(self, mock_session):
        email = EmailModel(
            id="em-1", tenant_id="t-1", opportunity_id="opp-1",
            subject="Test", from_address="a@b.com", sent_at=datetime.now(timezone.utc),
        )
        mock_session.execute.return_value = MockResult(scalar=email)
        repo = EmailRepository(mock_session)
        result = await repo.get("em-1")
        assert result is not None
        assert result.subject == "Test"

    @pytest.mark.asyncio
    async def test_list_by_opportunity_returns_empty(self, mock_session):
        mock_session.execute.return_value = MockResult(rows=[])
        repo = EmailRepository(mock_session)
        result = await repo.list_by_opportunity("opp-1", "t-1")
        assert result == []

    @pytest.mark.asyncio
    async def test_save_adds_and_flushes(self, mock_session):
        email = EmailModel(
            id="em-2", tenant_id="t-1", opportunity_id="opp-1",
            subject="New", from_address="a@b.com", sent_at=datetime.now(timezone.utc),
        )
        repo = EmailRepository(mock_session)
        result = await repo.save(email)
        mock_session.add.assert_called_once_with(email)
        mock_session.flush.assert_awaited_once()
        assert result.id == email.id

    @pytest.mark.asyncio
    async def test_delete_returns_true_when_found(self, mock_session):
        email = EmailModel(id="em-1", tenant_id="t-1", opportunity_id="opp-1", subject="X", from_address="a@b.com", sent_at=datetime.now(timezone.utc))
        mock_session.execute.return_value = MockResult(scalar=email)
        repo = EmailRepository(mock_session)
        result = await repo.delete("em-1")
        assert result is True
        mock_session.delete.assert_called_once_with(email)
