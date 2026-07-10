"""Tests for the ExecutiveService dashboard."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.executive.service import ExecutiveService
from app.modules.executive.schemas import ExecutiveDashboard


class FakeMapping:
    def __init__(self, data):
        self._data = data
    def __getitem__(self, key):
        return self._data[key]
    def get(self, key, default=None):
        return self._data.get(key, default)
    def keys(self):
        return self._data.keys()
    def __iter__(self):
        return iter(self._data)
    def __len__(self):
        return len(self._data)


class FakeResult:
    def __init__(self, one=None, all_rows=None):
        self._one = one or {}
        self._all_rows = all_rows or []
    def mappings(self):
        class M:
            def __init__(self, p):
                self._p = p
            def one(self):
                return FakeMapping(self._p._one)
            def all(self):
                return [FakeMapping(r) for r in self._p._all_rows]
        return M(self)


@pytest.fixture
def mock_execute():
    """Always return a FakeResult with default non-zero values for any SQL query."""
    defaults = {
        "total": 10, "active": 8,
        "total_pipeline": 1000000.0, "won_value": 500000.0, "prev_value": 800000.0,
        "cnt": 3, "due_30": 2, "due_90": 5,
        "new_companies": 5, "new_contacts": 12, "new_opps": 8, "new_contracts": 3,
        "has_name": 45, "has_email": 30, "has_phone": 25, "has_city": 40, "has_industry": 35,
    }

    async def execute(text, params=None):
        return FakeResult(one=dict(defaults))
    return execute


@pytest.fixture
def mock_session(mock_execute):
    session = AsyncMock(spec=AsyncSession)
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
        assert result.revenue.total_pipeline == 1000000.0
        assert result.revenue.total_booked == 500000.0

    async def test_get_dashboard_has_team_kpi(self, mock_session):
        service = ExecutiveService(mock_session, "tenant-1")
        result = await service.get_dashboard()
        assert result.team.total_employees == 10
        assert result.team.active_employees == 8

    async def test_get_dashboard_has_pipeline_data(self, mock_session):
        service = ExecutiveService(mock_session, "tenant-1")
        result = await service.get_dashboard()
        assert result.pipeline.total_deals >= 0
        assert result.pipeline is not None

    async def test_get_dashboard_has_growth_data(self, mock_session):
        service = ExecutiveService(mock_session, "tenant-1")
        result = await service.get_dashboard()
        assert result.growth.new_companies_30d == 5
        assert result.growth.new_opportunities_30d == 8

    async def test_get_dashboard_has_health_data(self, mock_session):
        service = ExecutiveService(mock_session, "tenant-1")
        result = await service.get_dashboard()
        assert result.health is not None
        assert result.health.overall_health in ("good", "fair", "needs_attention")
        assert result.health.data_completeness > 0
