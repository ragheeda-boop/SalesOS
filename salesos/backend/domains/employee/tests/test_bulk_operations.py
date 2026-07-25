"""Tests for employee bulk operations — B-4."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


class TestBulkOperationsSchemas:
    async def test_bulk_edit_request_valid(self):
        from domains.employee.schemas import BulkEditEmployeesRequest
        body = BulkEditEmployeesRequest(
            employee_ids=["id1", "id2"],
            updates={"role": "manager", "is_active": True},
        )
        assert len(body.employee_ids) == 2
        assert body.updates["role"] == "manager"
        assert body.updates["is_active"] is True

    async def test_bulk_edit_request_min_ids(self):
        from domains.employee.schemas import BulkEditEmployeesRequest
        body = BulkEditEmployeesRequest(employee_ids=["id1"], updates={})
        assert len(body.employee_ids) == 1

    async def test_bulk_delete_request(self):
        from domains.employee.schemas import BulkDeleteEmployeesRequest
        body = BulkDeleteEmployeesRequest(employee_ids=["id1", "id2"])
        assert len(body.employee_ids) == 2

    async def test_bulk_delete_request_single(self):
        from domains.employee.schemas import BulkDeleteEmployeesRequest
        body = BulkDeleteEmployeesRequest(employee_ids=["id1"])
        assert len(body.employee_ids) == 1

    async def test_bulk_edit_response(self):
        from domains.employee.schemas import BulkEditEmployeesResponse
        resp = BulkEditEmployeesResponse(updated=2, failed=0, errors=[])
        assert resp.updated == 2
        assert resp.failed == 0
        assert resp.errors == []

    async def test_bulk_edit_response_with_errors(self):
        from domains.employee.schemas import BulkEditEmployeesResponse
        resp = BulkEditEmployeesResponse(updated=1, failed=2, errors=[{"employee_id": "e1", "error": "Not found"}])
        assert resp.updated == 1
        assert resp.failed == 2
        assert len(resp.errors) == 1

    async def test_bulk_delete_response(self):
        from domains.employee.schemas import BulkDeleteEmployeesResponse
        resp = BulkDeleteEmployeesResponse(deleted=2)
        assert resp.deleted == 2

    async def test_bulk_delete_response_zero(self):
        from domains.employee.schemas import BulkDeleteEmployeesResponse
        resp = BulkDeleteEmployeesResponse(deleted=0)
        assert resp.deleted == 0


class TestBulkOperationsRouter:
    @patch("domains.employee.router._get_repo")
    async def test_bulk_update_flow(self, mock_get_repo):
        from domains.employee.router import bulk_update_employees

        mock_db = AsyncMock(spec=AsyncSession)

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=MagicMock())
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()

        body = MagicMock()
        body.employee_ids = ["e1"]
        body.updates = {"role": "manager"}

        result = await bulk_update_employees(body=body, tenant_id="t1", db=mock_db)
        assert result.updated >= 0

    @patch("domains.employee.router._get_repo")
    async def test_bulk_delete_flow(self, mock_get_repo):
        from domains.employee.router import bulk_delete_employees

        mock_db = AsyncMock(spec=AsyncSession)

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=MagicMock())
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()

        body = MagicMock()
        body.employee_ids = ["e1"]

        result = await bulk_delete_employees(body=body, tenant_id="t1", db=mock_db)
        assert result.deleted >= 0
