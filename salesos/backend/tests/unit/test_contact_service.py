"""Unit tests for ContactService — CRUD, search, bulk upsert, and edge cases."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.contact.service import ContactService


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    db.scalar = AsyncMock()
    return db


@pytest.fixture
def service(mock_db):
    return ContactService(db=mock_db)


def _make_mock_result(items, total=None):
    """Create a mock SQLAlchemy result."""
    result = MagicMock()
    result.scalars.return_value.all.return_value = items
    if total is not None:
        return result, total
    return result


class TestContactCreate:
    @pytest.mark.asyncio
    async def test_create_contact_basic(self, service, mock_db):
        tenant_id = str(uuid.uuid4())
        data = {"name": "Ahmed Al-Saud", "company_id": str(uuid.uuid4())}
        _ = await service.create(tenant_id, data)
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()
        added = mock_db.add.call_args[0][0]
        assert added.name == "Ahmed Al-Saud"
        assert str(added.tenant_id) == tenant_id

    @pytest.mark.asyncio
    async def test_create_contact_with_all_fields(self, service, mock_db):
        tenant_id = str(uuid.uuid4())
        company_id = str(uuid.uuid4())
        data = {
            "name": "Sara Al-Qahtani",
            "name_ar": "سارة القحطاني",
            "email": "sara@example.com",
            "phone": "+966500000000",
            "mobile": "+966500000001",
            "position": "Sales Manager",
            "position_ar": "مديرة المبيعات",
            "department": "Sales",
            "is_primary": True,
            "source": "balady",
            "company_id": company_id,
            "tags": ["vip", "enterprise"],
        }
        _ = await service.create(tenant_id, data)
        added = mock_db.add.call_args[0][0]
        assert added.name == "Sara Al-Qahtani"
        assert added.email == "sara@example.com"
        assert added.is_primary is True
        assert added.source == "balady"

    @pytest.mark.asyncio
    async def test_create_contact_optional_fields_none(self, service, mock_db):
        tenant_id = str(uuid.uuid4())
        data = {"name": "Minimal Contact", "company_id": str(uuid.uuid4())}
        _ = await service.create(tenant_id, data)
        added = mock_db.add.call_args[0][0]
        assert added.company_id is not None  # company_id is now required
        assert added.email is None
        assert added.phone is None
        assert added.is_primary is False
        assert added.tags == []


class TestContactGet:
    @pytest.mark.asyncio
    async def test_get_contact_found(self, service, mock_db):
        contact_id = str(uuid.uuid4())
        mock_contact = MagicMock()
        mock_contact.id = contact_id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_contact
        mock_db.execute.return_value = mock_result

        result = await service.get(contact_id, str(uuid.uuid4()))
        assert result == mock_contact

    @pytest.mark.asyncio
    async def test_get_contact_not_found(self, service, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.common.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await service.get(str(uuid.uuid4()), str(uuid.uuid4()))


class TestContactUpdate:
    @pytest.mark.asyncio
    async def test_update_contact_found(self, service, mock_db):
        contact_id = str(uuid.uuid4())
        mock_contact = MagicMock()
        mock_contact.id = contact_id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_contact
        mock_db.execute.return_value = mock_result

        _ = await service.update(contact_id, {"name": "Updated Name"}, str(uuid.uuid4()))
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_contact_not_found(self, service, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.common.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await service.update(str(uuid.uuid4()), {"name": "No One"}, str(uuid.uuid4()))


class TestContactDelete:
    @pytest.mark.asyncio
    async def test_delete_contact_found(self, service, mock_db):
        contact_id = str(uuid.uuid4())
        mock_contact = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_contact
        mock_db.execute.return_value = mock_result

        await service.delete(contact_id, str(uuid.uuid4()))
        mock_db.delete.assert_awaited_once_with(mock_contact)
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_contact_not_found(self, service, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.common.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await service.delete(str(uuid.uuid4()), str(uuid.uuid4()))


class TestContactSearch:
    @pytest.mark.asyncio
    async def test_search_no_filters(self, service, mock_db):
        tenant_id = str(uuid.uuid4())
        mock_items = [MagicMock(), MagicMock()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_items
        mock_db.execute.return_value = mock_result
        mock_db.scalar = AsyncMock(return_value=2)

        items, total = await service.search(tenant_id)
        assert total == 2
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_search_with_query(self, service, mock_db):
        tenant_id = str(uuid.uuid4())
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        mock_db.scalar = AsyncMock(return_value=0)

        items, total = await service.search(tenant_id, query="Ahmed")
        assert total == 0
        assert items == []

    @pytest.mark.asyncio
    async def test_search_with_filters(self, service, mock_db):
        tenant_id = str(uuid.uuid4())
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        mock_db.scalar = AsyncMock(return_value=0)

        items, total = await service.search(tenant_id, filters={"email": "test@example.com"})
        assert items == []

    @pytest.mark.asyncio
    async def test_search_pagination(self, service, mock_db):
        tenant_id = str(uuid.uuid4())
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        mock_db.scalar = AsyncMock(return_value=0)

        items, total = await service.search(tenant_id, page=3, page_size=10)
        assert items == []


class TestContactFindByCompany:
    @pytest.mark.asyncio
    async def test_find_by_company(self, service, mock_db):
        tenant_id = str(uuid.uuid4())
        company_id = str(uuid.uuid4())
        mock_items = [MagicMock()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_items
        mock_db.execute.return_value = mock_result

        result = await service.find_by_company(tenant_id, company_id)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_find_by_company_empty(self, service, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.find_by_company(str(uuid.uuid4()), str(uuid.uuid4()))
        assert result == []


class TestContactFindByEmail:
    @pytest.mark.asyncio
    async def test_find_by_email(self, service, mock_db):
        mock_items = [MagicMock()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_items
        mock_db.execute.return_value = mock_result

        result = await service.find_by_email(str(uuid.uuid4()), "test@example.com")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_find_by_email_empty(self, service, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.find_by_email(str(uuid.uuid4()), "nobody@example.com")
        assert result == []


class TestContactBulkUpsert:
    @pytest.mark.asyncio
    async def test_bulk_upsert_creates_new(self, service, mock_db):
        tenant_id = str(uuid.uuid4())
        records = [
            {"email": "new@example.com", "name": "New Contact"},
        ]
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        created, updated = await service.bulk_upsert(tenant_id, records)
        assert len(created) == 1
        assert len(updated) == 0

    @pytest.mark.asyncio
    async def test_bulk_upsert_updates_existing(self, service, mock_db):
        tenant_id = str(uuid.uuid4())
        existing_contact = MagicMock()
        existing_contact.email = "existing@example.com"
        existing_contact.name = "Old Name"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_contact
        mock_db.execute.return_value = mock_result

        records = [{"email": "existing@example.com", "name": "New Name"}]
        created, updated = await service.bulk_upsert(tenant_id, records)
        assert len(created) == 0
        assert len(updated) == 1
        assert updated[0].name == "New Name"

    @pytest.mark.asyncio
    async def test_bulk_upsert_skips_records_without_email(self, service, mock_db):
        tenant_id = str(uuid.uuid4())
        records = [{"name": "No Email"}]
        created, updated = await service.bulk_upsert(tenant_id, records)
        assert len(created) == 0
        assert len(updated) == 0

    @pytest.mark.asyncio
    async def test_bulk_upsert_empty_records(self, service, mock_db):
        created, updated = await service.bulk_upsert(str(uuid.uuid4()), [])
        assert created == []
        assert updated == []

    @pytest.mark.asyncio
    async def test_bulk_upsert_mixed_create_and_update(self, service, mock_db):
        tenant_id = str(uuid.uuid4())
        existing = MagicMock()
        existing.email = "existing@example.com"
        existing.name = "Existing"

        mock_result_existing = MagicMock()
        mock_result_existing.scalar_one_or_none.return_value = existing
        mock_result_new = MagicMock()
        mock_result_new.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_result_existing, mock_result_new]

        records = [
            {"email": "existing@example.com", "name": "Updated"},
            {"email": "brand-new@example.com", "name": "Brand New"},
        ]
        created, updated = await service.bulk_upsert(tenant_id, records)
        assert len(created) == 1
        assert len(updated) == 1
