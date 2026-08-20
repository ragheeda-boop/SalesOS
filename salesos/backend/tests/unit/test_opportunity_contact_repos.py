"""ADR-030: Unit tests for PostgresOpportunityContactRepository."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from domains.commercial.infrastructure.postgres_repositories import PostgresOpportunityContactRepository
from domains.commercial.opportunity.contracts.opportunity_contact_repository import (
    OpportunityContact,
    OpportunityContactQuery,
)


class MockResult:
    """Simulates sqlalchemy Result for scalar_one_or_none / scalars / all."""

    def __init__(self, value=None, values=None):
        self._value = value
        self._values = values or []

    def scalar_one_or_none(self):
        return self._value

    def scalars(self):
        return MockScalars(self._values)

    def scalar(self):
        return self._value


class MockScalars:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


def _make_oc():
    return OpportunityContact(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        opportunity_id=str(uuid.uuid4()),
        contact_id=uuid.uuid4(),
    )


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.delete = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def repo(mock_session):
    return PostgresOpportunityContactRepository(session=mock_session)


class TestPostgresOpportunityContactRepository:

    async def test_create_adds_and_flushes(self, repo, mock_session):
        oc = _make_oc()
        mock_session.execute.return_value = MockResult()

        await repo.create(oc)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_awaited_once()

    async def test_get_returns_none_when_not_found(self, repo, mock_session):
        mock_session.execute.return_value = MockResult(value=None)

        result = await repo.get(uuid.uuid4())

        assert result is None

    async def test_get_returns_domain_when_found(self, repo, mock_session):
        from domains.commercial.infrastructure.models import OpportunityContactModel

        model = OpportunityContactModel(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            opportunity_id=str(uuid.uuid4()),
            contact_id=str(uuid.uuid4()),
        )
        mock_session.execute.return_value = MockResult(value=model)

        result = await repo.get(uuid.UUID(model.id))

        assert result is not None
        assert result.opportunity_id == model.opportunity_id

    async def test_get_by_opportunity_orders_primary_first(self, repo, mock_session):
        from domains.commercial.infrastructure.models import OpportunityContactModel

        primary = OpportunityContactModel(
            id=str(uuid.uuid4()), tenant_id=str(uuid.uuid4()),
            opportunity_id="opp-1", contact_id=str(uuid.uuid4()),
            is_primary=True,
        )
        secondary = OpportunityContactModel(
            id=str(uuid.uuid4()), tenant_id=str(uuid.uuid4()),
            opportunity_id="opp-1", contact_id=str(uuid.uuid4()),
            is_primary=False,
        )
        mock_session.execute.return_value = MockResult(values=[primary, secondary])

        results = await repo.get_by_opportunity("opp-1", str(uuid.uuid4()))

        assert len(results) == 2
        assert results[0].is_primary is True

    async def test_query_with_filters(self, repo, mock_session):
        tenant_id = str(uuid.uuid4())
        oc = _make_oc()
        oc.tenant_id = uuid.UUID(tenant_id)
        oc.opportunity_id = "opp-target"

        # Mock count query return
        mock_session.execute.side_effect = [
            MockResult(value=1),        # count
            MockResult(values=[oc]),    # actual query returns model objects
        ]

        query = OpportunityContactQuery(
            tenant_id=tenant_id, opportunity_id="opp-target", page=1, page_size=20,
        )
        result = await repo.query(query)

        assert mock_session.execute.call_count == 2
        assert result.total == 1

    async def test_delete_returns_true_when_found(self, repo, mock_session):
        from domains.commercial.infrastructure.models import OpportunityContactModel

        model = OpportunityContactModel(
            id=str(uuid.uuid4()), tenant_id=str(uuid.uuid4()),
            opportunity_id="opp-1", contact_id=str(uuid.uuid4()),
        )
        mock_session.execute.return_value = MockResult(value=model)

        result = await repo.delete(uuid.UUID(model.id))

        assert result is True
        mock_session.delete.assert_called_once_with(model)
        mock_session.flush.assert_awaited_once()

    async def test_delete_returns_false_when_not_found(self, repo, mock_session):
        mock_session.execute.return_value = MockResult(value=None)

        result = await repo.delete(uuid.uuid4())

        assert result is False

    async def test_delete_by_opportunity_returns_count(self, repo, mock_session):
        count_result = MagicMock()
        count_result.rowcount = 3
        mock_session.execute.return_value = count_result

        result = await repo.delete_by_opportunity("opp-1")

        assert result == 3
        mock_session.flush.assert_awaited_once()
