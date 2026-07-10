"""Tests for Dashboard widget mappers."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dashboard.mappers.company_mapper import CompanyMapper
from app.application.dashboard.mappers.scoring_mapper import ScoringMapper
from app.application.dashboard.mappers.ai_mapper import AIMapper
from app.application.dashboard.mappers.timeline_mapper import TimelineMapper
from app.application.dashboard.dto.dashboard_dto import (
    MissionCenterData, DecisionQueueData, AIBriefData, RecentActivityData,
)


@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    mappings = MagicMock()
    mappings.all.return_value = []
    mappings.one.return_value = MagicMock()
    mappings.one.return_value.__getitem__.side_effect = lambda k: 0
    session.execute.return_value = AsyncMock()
    session.execute.return_value.mappings = MagicMock(return_value=mappings)
    return session


class TestCompanyMapper:
    async def test_get_stats_returns_mission_center_data(self, mock_session):
        mapper = CompanyMapper(mock_session, "tenant-1")
        result = await mapper.get_stats()
        assert isinstance(result, MissionCenterData)
        assert hasattr(result, "companiesTracked")
        assert hasattr(result, "activeDeals")
        assert hasattr(result, "pipelineValue")
        assert hasattr(result, "signalsToday")
        assert hasattr(result, "decisionsPending")


class TestScoringMapper:
    async def test_get_decisions_returns_decision_queue_data(self, mock_session):
        mapper = ScoringMapper(mock_session, "tenant-1")
        result = await mapper.get_decisions()
        assert isinstance(result, DecisionQueueData)
        assert hasattr(result, "items")
        assert hasattr(result, "total")


class TestAIMapper:
    async def test_get_brief_returns_ai_brief_data(self, mock_session):
        mapper = AIMapper(mock_session, "tenant-1")
        result = await mapper.get_brief()
        assert isinstance(result, AIBriefData)
        assert hasattr(result, "summary")
        assert hasattr(result, "highlights")
        assert hasattr(result, "generatedAt")


class TestTimelineMapper:
    async def test_get_recent_returns_recent_activity_data(self, mock_session):
        mapper = TimelineMapper(mock_session, "tenant-1")
        result = await mapper.get_recent()
        assert isinstance(result, RecentActivityData)
        assert hasattr(result, "items")
        assert hasattr(result, "total")
