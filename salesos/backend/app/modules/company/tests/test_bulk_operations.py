"""Tests for B-1 Bulk Operations and B-2 Advanced Filtering."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.common.exceptions import NotFoundError
from app.modules.company.models import Company
from app.modules.company.schemas import (
    BulkDeleteRequest,
    BulkDeleteResponse,
    BulkEditRequest,
    BulkEditResponse,
)
from app.modules.company.service import CompanyService

# ── Bulk Update Tests ────────────────────────────────────────────────────


class TestBulkUpdate:
    @pytest.mark.asyncio
    async def test_bulk_update_allowed_fields(self):
        service = CompanyService.__new__(CompanyService)
        service.db = AsyncMock()
        service.event_bus = AsyncMock()
        service.logger = None

        c1 = MagicMock(
            spec=Company,
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            industry="Tech",
            status="active",
            tags=["a"],
        )
        c1.__class__ = Company
        c2 = MagicMock(
            spec=Company,
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            industry="Finance",
            status="active",
            tags=["b"],
        )
        c2.__class__ = Company

        with patch.object(service, "get_company") as mock_get:
            mock_get.side_effect = [c1, c2]
            result = await service.bulk_update_companies(
                [str(c1.id), str(c2.id)],
                {"industry": "Healthcare", "status": "inactive", "tags": ["x", "y"]},
                tenant_id="t1",
            )

        assert result["updated"] == 2
        assert result["failed"] == 0
        assert c1.industry == "Healthcare"
        assert c1.status == "inactive"
        assert c2.industry == "Healthcare"
        assert c2.status == "inactive"

    @pytest.mark.asyncio
    async def test_bulk_update_ignores_disallowed_fields(self):
        service = CompanyService.__new__(CompanyService)
        service.db = AsyncMock()
        service.event_bus = AsyncMock()
        service.logger = None

        c1 = MagicMock(
            spec=Company,
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            industry="Tech",
            name_ar="Old Name",
        )
        c1.__class__ = Company

        with patch.object(service, "get_company") as mock_get:
            mock_get.return_value = c1
            result = await service.bulk_update_companies(
                [str(c1.id)],
                {"industry": "Healthcare", "name_ar": "Should Not Update"},
                tenant_id="t1",
            )

        assert result["updated"] == 1
        assert c1.industry == "Healthcare"
        assert c1.name_ar == "Old Name"

    @pytest.mark.asyncio
    async def test_bulk_update_handles_errors(self):
        service = CompanyService.__new__(CompanyService)
        service.db = AsyncMock()
        service.event_bus = None
        service.logger = None

        with patch.object(service, "get_company") as mock_get:
            mock_get.side_effect = [NotFoundError("Company", "bad-id")]
            result = await service.bulk_update_companies(
                ["00000000-0000-0000-0000-000000000000"],
                {"industry": "Healthcare"},
                tenant_id="t1",
            )

        assert result["updated"] == 0
        assert result["failed"] == 1
        assert len(result["errors"]) == 1


# ── Bulk Delete Tests ────────────────────────────────────────────────────


class TestBulkDelete:
    @pytest.mark.asyncio
    async def test_bulk_delete_soft_delete(self):
        service = CompanyService.__new__(CompanyService)
        service.db = AsyncMock()
        service.event_bus = None
        service.logger = None

        c1 = MagicMock(
            spec=Company, id=uuid.uuid4(), tenant_id=uuid.uuid4(), status="active", is_active=True
        )
        c1.__class__ = Company

        with patch.object(service, "get_company") as mock_get:
            mock_get.return_value = c1
            result = await service.bulk_delete_companies([str(c1.id)], tenant_id="t1")

        assert result["deleted"] == 1
        assert c1.status == "deleted"
        assert c1.is_active is False

    @pytest.mark.asyncio
    async def test_bulk_delete_handles_errors_gracefully(self):
        service = CompanyService.__new__(CompanyService)
        service.db = AsyncMock()
        service.event_bus = None
        service.logger = None

        with patch.object(service, "get_company") as mock_get:
            mock_get.side_effect = NotFoundError("Company", "bad-id")
            result = await service.bulk_delete_companies(
                ["00000000-0000-0000-0000-000000000000"], tenant_id="t1"
            )

        assert result["deleted"] == 0


# ── Bulk Edit Schema Tests ───────────────────────────────────────────────


class TestBulkEditSchema:
    def test_valid_bulk_edit_request(self):
        req = BulkEditRequest(
            company_ids=["00000000-0000-0000-0000-000000000001"],
            updates={"industry": "Tech", "status": "active"},
        )
        assert len(req.company_ids) == 1
        assert req.updates["industry"] == "Tech"

    def test_bulk_edit_response(self):
        resp = BulkEditResponse(
            updated=5, failed=1, errors=[{"company_id": "x", "error": "not found"}]
        )
        assert resp.updated == 5
        assert len(resp.errors) == 1


class TestBulkDeleteSchema:
    def test_valid_bulk_delete_request(self):
        req = BulkDeleteRequest(company_ids=["00000000-0000-0000-0000-000000000001"])
        assert len(req.company_ids) == 1

    def test_bulk_delete_response(self):
        resp = BulkDeleteResponse(deleted=3)
        assert resp.deleted == 3
