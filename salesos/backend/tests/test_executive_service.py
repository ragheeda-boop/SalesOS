"""Tests for the ExecutiveService dashboard."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.executive.service import ExecutiveService
from app.modules.executive.schemas import ExecutiveDashboard


@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)

    async def mock_execute(text, params=None):
        result = AsyncMock()
        if "COUNT(*)" in str(text):
            result.mappings.return_value.one.return_value = {"total": 10, "active": 8}
            result.mappings.return_value.all.return_value = []
        elif "SUM" in str(text):
            result.mappings.return_value.one.return_value = {"total_pipeline": 1000000.0, "won_value": 500000.0}
            result.mappings.return_value.all.return_value = []
        elif "expiry_date" in str(text):
            result.mappings.return_value.one.return_value = {"due_30": 2, "due_90": 5}
        else:
            result.mappings.return_value.one.return_value = {"total": 0, "active": 0}
            result.mappings.return_value.all.return_value = []
        return result
    session.execute = mock_execute
    return session


class TestExecutiveService:
    async def test_get_dashboard_returns_executive_dashboard(self, mock_session):
        service = ExecutiveService(mock_session, "tenant-1")
        result = await service.get_dashboard()
        assert isinstance(result, ExecutiveDashboard)

    async def test_get_dashboard_has_revenue_kpi(self, mock_session):
        service = ExecutiveService(mock_session, "tenant-1")
        result = await service.get_dashboard()
        assert result.revenue.total_pipeline > 0

    async def test_get_dashboard_has_team_kpi(self, mock_session):
        service = ExecutiveService(mock_session, "tenant-1")
        result = await service.get_dashboard()
        assert result.team.total_employees == 10

    async def test_get_dashboard_has_pipeline_data(self, mock_session):
        service = ExecutiveService(mock_session, "tenant-1")
        result = await service.get_dashboard()
        assert result.pipeline is not None

    async def test_get_dashboard_has_growth_data(self, mock_session):
        service = ExecutiveService(mock_session, "tenant-1")
        result = await service.get_dashboard()
        assert result.growth is not None

    async def test_get_dashboard_has_health_data(self, mock_session):
        service = ExecutiveService(mock_session, "tenant-1")
        result = await service.get_dashboard()
        assert result.health is not None
        assert result.health.overall_health in ("good", "fair", "needs_attention")
