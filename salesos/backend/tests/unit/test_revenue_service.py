"""Unit tests for RevenueService — opportunities, tasks, and pipeline."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.revenue_execution.service import STAGE_WEIGHTS, RevenueService


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    return db


@pytest.fixture
def service(mock_db):
    return RevenueService(db=mock_db)


def _mock_row(**kwargs):
    row = MagicMock()
    row._mapping = kwargs
    for k, v in kwargs.items():
        setattr(row, k, v)
    return row


def _setup_execute_with_row(mock_db, row):
    """Set up mock_db.execute to return a result whose fetchone/fetchall work synchronously."""
    result_mock = MagicMock()
    result_mock.fetchone.return_value = row
    mock_db.execute.return_value = result_mock
    return result_mock


def _setup_execute_with_rows(mock_db, rows):
    result_mock = MagicMock()
    result_mock.fetchall.return_value = rows
    result_mock.scalar.return_value = len(rows) if rows else 0
    mock_db.execute.return_value = result_mock
    return result_mock


class TestCreateOpportunity:
    @pytest.mark.asyncio
    async def test_create_opportunity_basic(self, service, mock_db):
        _setup_execute_with_row(
            mock_db,
            _mock_row(
                id="1",
                title="Deal A",
                stage="identified",
                estimated_value=50000,
                confidence=0.7,
                source="nba",
                risk_level="medium",
            ),
        )
        result = await service.create_opportunity(
            tenant_id=str(uuid.uuid4()),
            company_id=str(uuid.uuid4()),
            title="Deal A",
            estimated_value=50000,
            confidence=0.7,
        )
        assert result is not None
        assert result["title"] == "Deal A"
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_opportunity_high_confidence_low_risk(self, service, mock_db):
        _setup_execute_with_row(
            mock_db,
            _mock_row(
                id="2",
                title="High Deal",
                stage="identified",
                estimated_value=100000,
                confidence=0.95,
                source="nba",
                risk_level="low",
            ),
        )
        result = await service.create_opportunity(
            tenant_id=str(uuid.uuid4()),
            company_id=str(uuid.uuid4()),
            title="High Deal",
            estimated_value=100000,
            confidence=0.95,
        )
        assert result["risk_level"] == "low"

    @pytest.mark.asyncio
    async def test_create_opportunity_low_confidence_high_risk(self, service, mock_db):
        _setup_execute_with_row(
            mock_db,
            _mock_row(
                id="3",
                title="Risky Deal",
                stage="identified",
                estimated_value=10000,
                confidence=0.2,
                source="nba",
                risk_level="high",
            ),
        )
        result = await service.create_opportunity(
            tenant_id=str(uuid.uuid4()),
            company_id=str(uuid.uuid4()),
            title="Risky Deal",
            estimated_value=10000,
            confidence=0.2,
        )
        assert result["risk_level"] == "high"

    @pytest.mark.asyncio
    async def test_create_opportunity_returns_none_on_empty(self, service, mock_db):
        _setup_execute_with_row(mock_db, None)
        result = await service.create_opportunity(
            tenant_id=str(uuid.uuid4()),
            company_id=str(uuid.uuid4()),
            title="No Result",
            estimated_value=0,
            confidence=0.0,
        )
        assert result is None


class TestUpdateStage:
    @pytest.mark.asyncio
    async def test_update_stage_success(self, service, mock_db):
        _setup_execute_with_row(
            mock_db,
            _mock_row(
                id="1",
                title="Deal",
                stage="qualifying",
                estimated_value=50000,
                confidence=0.7,
            ),
        )
        result = await service.update_stage("1", "qualifying", str(uuid.uuid4()))
        assert result is not None
        assert result["stage"] == "qualifying"

    @pytest.mark.asyncio
    async def test_update_stage_not_found(self, service, mock_db):
        _setup_execute_with_row(mock_db, None)
        result = await service.update_stage("999", "closing", str(uuid.uuid4()))
        assert result is None


class TestCreateTask:
    @pytest.mark.asyncio
    async def test_create_task_basic(self, service, mock_db):
        _setup_execute_with_row(
            mock_db,
            _mock_row(
                id="1",
                title="Follow up",
                priority="medium",
                source="manual",
                completed=False,
            ),
        )
        result = await service.create_task(
            tenant_id=str(uuid.uuid4()),
            title="Follow up",
        )
        assert result is not None
        assert result["title"] == "Follow up"

    @pytest.mark.asyncio
    async def test_create_task_with_priority(self, service, mock_db):
        _setup_execute_with_row(
            mock_db,
            _mock_row(
                id="2",
                title="Urgent Task",
                priority="high",
                source="nba",
                completed=False,
            ),
        )
        result = await service.create_task(
            tenant_id=str(uuid.uuid4()),
            title="Urgent Task",
            priority="high",
            source="nba",
        )
        assert result["priority"] == "high"

    @pytest.mark.asyncio
    async def test_create_task_with_due_date(self, service, mock_db):
        _setup_execute_with_row(
            mock_db,
            _mock_row(
                id="3",
                title="Dated Task",
                priority="low",
                source="manual",
                completed=False,
            ),
        )
        result = await service.create_task(
            tenant_id=str(uuid.uuid4()),
            title="Dated Task",
            due_date="2026-08-01",
        )
        assert result is not None


class TestCompleteTask:
    @pytest.mark.asyncio
    async def test_complete_task_success(self, service, mock_db):
        _setup_execute_with_row(
            mock_db,
            _mock_row(
                id="1",
                title="Done",
                completed=True,
            ),
        )
        result = await service.complete_task("1", str(uuid.uuid4()))
        assert result is not None
        assert result["completed"] is True

    @pytest.mark.asyncio
    async def test_complete_task_not_found(self, service, mock_db):
        _setup_execute_with_row(mock_db, None)
        result = await service.complete_task("999", str(uuid.uuid4()))
        assert result is None


class TestGetPipeline:
    @pytest.mark.asyncio
    async def test_get_pipeline_empty(self, service, mock_db):
        _setup_execute_with_rows(mock_db, [])
        result = await service.get_pipeline(str(uuid.uuid4()))
        assert result["total_deals"] == 0
        assert result["total_value"] == 0
        assert result["weighted_value"] == 0
        assert result["stages"] == []

    @pytest.mark.asyncio
    async def test_get_pipeline_with_stages(self, service, mock_db):
        _setup_execute_with_rows(
            mock_db,
            [
                _mock_row(stage="identified", deals=3, value=150000),
                _mock_row(stage="qualifying", deals=2, value=200000),
                _mock_row(stage="closing", deals=1, value=500000),
            ],
        )
        result = await service.get_pipeline(str(uuid.uuid4()))
        assert result["total_deals"] == 6
        assert result["total_value"] == 850000
        assert result["weighted_value"] > 0
        assert len(result["stages"]) == 3

    @pytest.mark.asyncio
    async def test_get_pipeline_weight_calculation(self, service, mock_db):
        _setup_execute_with_rows(
            mock_db,
            [
                _mock_row(stage="identified", deals=1, value=100),
                _mock_row(stage="closing", deals=1, value=100),
            ],
        )
        result = await service.get_pipeline(str(uuid.uuid4()))
        expected_weighted = 100 * STAGE_WEIGHTS["identified"] + 100 * STAGE_WEIGHTS["closing"]
        assert abs(result["weighted_value"] - expected_weighted) < 0.01


class TestListOpportunities:
    @pytest.mark.asyncio
    async def test_list_opportunities_empty(self, service, mock_db):
        result_mock = MagicMock()
        result_mock.fetchall.return_value = []
        result_mock.scalar.return_value = 0
        mock_db.execute.return_value = result_mock
        result = await service.list_opportunities(str(uuid.uuid4()))
        assert result["opportunities"] == []
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_list_opportunities_with_data(self, service, mock_db):
        result_mock = MagicMock()
        result_mock.fetchall.return_value = [
            _mock_row(id="1", title="Deal A", stage="identified"),
            _mock_row(id="2", title="Deal B", stage="closing"),
        ]
        result_mock.scalar.return_value = 2
        mock_db.execute.return_value = result_mock
        result = await service.list_opportunities(str(uuid.uuid4()))
        assert len(result["opportunities"]) == 2
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_list_opportunities_with_stage_filter(self, service, mock_db):
        result_mock = MagicMock()
        result_mock.fetchall.return_value = [
            _mock_row(id="1", title="Deal A", stage="closing"),
        ]
        result_mock.scalar.return_value = 1
        mock_db.execute.return_value = result_mock
        result = await service.list_opportunities(str(uuid.uuid4()), stage="closing")
        assert len(result["opportunities"]) == 1


class TestListTasks:
    @pytest.mark.asyncio
    async def test_list_tasks_empty(self, service, mock_db):
        _setup_execute_with_rows(mock_db, [])
        result = await service.list_tasks(str(uuid.uuid4()))
        assert result == []

    @pytest.mark.asyncio
    async def test_list_tasks_with_data(self, service, mock_db):
        _setup_execute_with_rows(
            mock_db,
            [
                _mock_row(id="1", title="Task A", priority="high"),
                _mock_row(id="2", title="Task B", priority="low"),
            ],
        )
        result = await service.list_tasks(str(uuid.uuid4()))
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_tasks_with_priority_filter(self, service, mock_db):
        _setup_execute_with_rows(
            mock_db,
            [
                _mock_row(id="1", title="Urgent", priority="high"),
            ],
        )
        result = await service.list_tasks(str(uuid.uuid4()), priority="high")
        assert len(result) == 1
