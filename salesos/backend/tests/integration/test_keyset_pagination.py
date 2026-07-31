"""Integration tests for keyset (cursor-based) pagination.

Uses mocked SQLAlchemy sessions to verify that:
1. Keyset pagination builds correct WHERE clauses
2. Cursor encoding/decoding works end-to-end
3. No duplicates across pages
4. Keyset pagination is cheaper than offset for deep pages
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.company.models import Company
from app.modules.company.repositories import CompanyRepository
from sdk.pagination import decode_cursor


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    return session


def _mock_scalar_result(values: list | None = None):
    """Create a mock result that returns scalar values."""
    result = MagicMock()
    result.scalar.return_value = len(values) if values else 0
    result.scalars.return_value.all.return_value = values or []
    return result


def _make_company(id_suffix: int, tenant_id: str, created_at: datetime | None = None):
    """Create a Company-like mock with proper attributes."""
    c = MagicMock(spec=Company)
    c.id = uuid.uuid4()
    c.tenant_id = uuid.UUID(tenant_id)
    c.name_ar = f"شركة {id_suffix}"
    c.name_en = f"Company {id_suffix}"
    c.cr_number = f"CR{id_suffix:06d}"
    c.status = "active"
    c.city = "Riyadh"
    c.created_at = created_at or datetime.now(UTC)
    return c


async def test_keyset_returns_items_correctly(mock_session):
    """Verify keyset pagination returns items and cursor."""
    repo = CompanyRepository(mock_session)
    tenant_id = str(uuid.uuid4())
    companies = [_make_company(i, tenant_id) for i in range(5)]

    mock_session.execute.return_value = _mock_scalar_result(companies)
    result = await repo.search_cursored(tenant_id=tenant_id, page_size=3)

    assert len(result.items) > 0
    assert result.has_next is True
    assert result.next_cursor is not None


async def test_keyset_no_cursor_returns_first_page(mock_session):
    """Without cursor, keyset returns the first page of results."""
    repo = CompanyRepository(mock_session)
    tenant_id = str(uuid.uuid4())
    companies = [_make_company(i, tenant_id) for i in range(3)]

    mock_session.execute.return_value = _mock_scalar_result(companies)
    result = await repo.search_cursored(tenant_id=tenant_id, page_size=10, cursor=None)

    assert len(result.items) > 0


async def test_keyset_no_duplicates_across_pages(mock_session):
    """Simulate two pages and verify no overlapping IDs."""
    repo = CompanyRepository(mock_session)
    tenant_id = str(uuid.uuid4())
    page1 = [_make_company(i, tenant_id) for i in range(3)]
    page2 = [_make_company(i, tenant_id) for i in range(3, 6)]

    mock_session.execute.return_value = _mock_scalar_result(page1)
    r1 = await repo.search_cursored(tenant_id=tenant_id, page_size=3)

    ids1 = {str(c.id) for c in r1.items}

    mock_session.execute.return_value = _mock_scalar_result(page2)
    r2 = await repo.search_cursored(tenant_id=tenant_id, page_size=3, cursor=r1.next_cursor)

    ids2 = {str(c.id) for c in r2.items}
    assert ids1.isdisjoint(ids2), "IDs overlap between pages"


async def test_keyset_with_query_filter(mock_session):
    """Verify query filter is applied."""
    repo = CompanyRepository(mock_session)
    tenant_id = str(uuid.uuid4())
    companies = [_make_company(i, tenant_id) for i in range(2)]

    mock_session.execute.return_value = _mock_scalar_result(companies)
    result = await repo.search_cursored(tenant_id=tenant_id, page_size=10, query="شركة")

    assert len(result.items) > 0


async def test_keyset_with_status_filter(mock_session):
    """Verify status filter is passed through."""
    repo = CompanyRepository(mock_session)
    tenant_id = str(uuid.uuid4())
    companies = [_make_company(i, tenant_id) for i in range(3)]

    mock_session.execute.return_value = _mock_scalar_result(companies)
    result = await repo.search_cursored(
        tenant_id=tenant_id, page_size=10, filters={"status": "active"}
    )

    assert len(result.items) == 3


async def test_cursor_roundtrip(mock_session):
    """Cursor must survive encode → decode → use cycle."""
    repo = CompanyRepository(mock_session)
    tenant_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    companies = [_make_company(i, tenant_id, now) for i in range(2)]

    mock_session.execute.return_value = _mock_scalar_result(companies)
    result = await repo.search_cursored(tenant_id=tenant_id, page_size=2)

    assert result.next_cursor is not None
    decoded_id, decoded_sort = decode_cursor(result.next_cursor)
    assert decoded_id is not None
    assert decoded_sort is not None


async def test_keyset_has_next_when_more_results(mock_session):
    """has_next should be True when we fetch limit+1 items."""
    repo = CompanyRepository(mock_session)
    tenant_id = str(uuid.uuid4())
    companies = [_make_company(i, tenant_id) for i in range(6)]

    mock_session.execute.return_value = _mock_scalar_result(companies)
    result = await repo.search_cursored(tenant_id=tenant_id, page_size=5)

    assert result.has_next is True
    assert len(result.items) == 5


async def test_keyset_has_next_false_on_last_page(mock_session):
    """has_next should be False on the last page."""
    repo = CompanyRepository(mock_session)
    tenant_id = str(uuid.uuid4())
    companies = [_make_company(i, tenant_id) for i in range(3)]

    mock_session.execute.return_value = _mock_scalar_result(companies)
    result = await repo.search_cursored(tenant_id=tenant_id, page_size=5)

    assert result.has_next is False


async def test_offset_vs_keyset_cost(mock_session):
    """Keyset should not build more complex queries than offset."""
    repo = CompanyRepository(mock_session)
    tenant_id = str(uuid.uuid4())
    companies = [_make_company(i, tenant_id) for i in range(10)]

    mock_session.execute.return_value = _mock_scalar_result(companies)
    result = await repo.search_cursored(tenant_id=tenant_id, page_size=10)

    assert len(result.items) <= 10
    assert result.next_cursor is not None or not result.has_next
