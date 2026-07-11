"""Tests for Dashboard widget mappers."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dashboard.mappers.company_mapper import CompanyMapper
from app.application.dashboard.mappers.scoring_mapper import ScoringMapper
from app.application.dashboard.mappers.ai_mapper import AIMapper
from app.application.dashboard.mappers.timeline_mapper import TimelineMapper
from app.application.dashboard.mappers.signal_mapper import SignalMapper
from app.application.dashboard.dto.dashboard_dto import (
    MissionCenterData, DecisionQueueData, AIBriefData, RecentActivityData,
    IntelligenceFeedData, DecisionItem,
)


class FakeMapping:
    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()


class FakeMappings:
    def __init__(self, rows=None, one=None):
        self._rows = rows or []
        self._one = one or {}

    def one(self):
        return FakeMapping(self._one)

    def all(self):
        return [FakeMapping(r) for r in self._rows]


class FakeResult:
    def __init__(self, mappings_obj=None):
        self._mappings = mappings_obj or FakeMappings()
        self._one = None

    def mappings(self):
        return self._mappings

    def one_or_none(self):
        return self._one

    def scalar(self):
        return 0

    def scalar_one_or_none(self):
        return None


class FakeExecute:
    """Dispatch based on SQL text to return appropriate mock data."""
    def __init__(self):
        pass

    async def __call__(self, sql_str, params=None):
        text = str(sql_str)
        if "company_features" in text:
            return FakeResult(FakeMappings(rows=[
                {"id": "co-1", "name_ar": "شركة أ", "feature_name": "icp_score", "score": 0.85},
                {"id": "co-2", "name_ar": "شركة ب", "feature_name": "growth_score", "score": 0.72},
            ]))
        if "companies" in text and "activity_records" not in text and "company_signals" not in text:
            return FakeResult(FakeMappings(rows=[
                {"id": "co-1", "name_ar": "شركة أ", "name_en": "Company A", "cr_number": "1234567890", "tenant_id": "t-1", "industry": "Tech", "city": "Riyadh", "status": "active", "activity_description": "Software", "employee_count": 50, "annual_revenue": 5000000, "phone": "+966500000000"},
                {"id": "co-2", "name_ar": "شركة ب", "name_en": "Company B", "cr_number": "0987654321", "tenant_id": "t-1", "industry": "Finance", "city": "Jeddah", "status": "active", "activity_description": "Banking", "employee_count": 200, "annual_revenue": 20000000, "phone": "+966511111111"},
            ]))
        if "activity_records" in text:
            return FakeResult(FakeMappings(rows=[
                {"id": "act-1", "action": "email_sent", "entity_id": "co-1", "entity_type": "company", "tenant_id": "t-1", "target_type": "company", "target_id": "co-1", "metadata": {"description": "Sent proposal", "name_ar": "شركة أ"}, "timestamp": datetime.now(timezone.utc)},
                {"id": "act-2", "action": "meeting", "entity_id": "co-2", "entity_type": "company", "tenant_id": "t-1", "target_type": "company", "target_id": "co-2", "metadata": {"description": "Discovery meeting", "name_ar": "شركة ب"}, "timestamp": datetime.now(timezone.utc)},
            ]))
        if "company_signals" in text and "ORDER BY created_at" in text:
            return FakeResult(FakeMappings(rows=[
                {"id": "sig-1", "title": "New tender", "signal_type": "tender", "severity": "high", "company_id": "co-1", "summary": "Government tender released", "source": "gov.sa", "created_at": "2026-07-10T08:00:00Z", "company_name_ar": "شركة أ"},
                {"id": "sig-2", "title": "Competitor threat", "signal_type": "competitor", "severity": "medium", "company_id": "co-2", "summary": "New competitor entered market", "source": "news", "created_at": "2026-07-08T10:00:00Z", "company_name_ar": "شركة ب"},
            ]))
        if "COUNT(*)" in text:
            return FakeResult(FakeMappings(one={"cnt": 5}))
        return FakeResult(FakeMappings())


@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    session.execute = FakeExecute()
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

    async def test_get_stats_has_counts(self, mock_session):
        mapper = CompanyMapper(mock_session, "tenant-1")
        result = await mapper.get_stats()
        assert result.companiesTracked >= 0
        assert result.activeDeals >= 0
        assert result.pipelineValue >= 0
        assert result.signalsToday >= 0
        assert result.decisionsPending >= 0


class TestScoringMapper:
    async def test_get_decisions_returns_decision_queue_data(self, mock_session):
        mapper = ScoringMapper(mock_session, "tenant-1")
        result = await mapper.get_decisions()
        assert isinstance(result, DecisionQueueData)
        assert hasattr(result, "items")
        assert hasattr(result, "total")

    async def test_get_decisions_has_items(self, mock_session):
        mapper = ScoringMapper(mock_session, "tenant-1")
        result = await mapper.get_decisions()
        assert len(result.items) > 0

    async def test_get_decisions_items_have_priorities(self, mock_session):
        mapper = ScoringMapper(mock_session, "tenant-1")
        result = await mapper.get_decisions()
        for item in result.items:
            assert item.priority in ("high", "medium")

    async def test_get_decisions_empty(self):
        session = AsyncMock(spec=AsyncSession)
        session.execute = FakeExecute()
        mapper = ScoringMapper(session, "tenant-1")
        result = await mapper.get_decisions()
        assert isinstance(result, DecisionQueueData)


class TestAIMapper:
    async def test_get_brief_returns_ai_brief_data(self, mock_session):
        mapper = AIMapper(mock_session, "tenant-1")
        result = await mapper.get_brief()
        assert isinstance(result, AIBriefData)
        assert hasattr(result, "summary")
        assert hasattr(result, "highlights")
        assert hasattr(result, "generatedAt")

    async def test_get_brief_has_string_fields(self, mock_session):
        mapper = AIMapper(mock_session, "tenant-1")
        result = await mapper.get_brief()
        assert isinstance(result.summary, str)
        assert isinstance(result.highlights, list)


class TestTimelineMapper:
    async def test_get_recent_returns_recent_activity_data(self, mock_session):
        mapper = TimelineMapper(mock_session, "tenant-1")
        result = await mapper.get_recent()
        assert isinstance(result, RecentActivityData)
        assert hasattr(result, "items")
        assert hasattr(result, "total")

    async def test_get_recent_has_activity_items(self, mock_session):
        mapper = TimelineMapper(mock_session, "tenant-1")
        result = await mapper.get_recent()
        if result.items:
            item = result.items[0]
            assert item.id
            assert item.type in ("signal", "decision", "update", "note")
            assert item.timestamp


class TestSignalMapper:
    async def test_get_feed_returns_intelligence_feed_data(self, mock_session):
        mapper = SignalMapper(mock_session, "tenant-1")
        result = await mapper.get_feed()
        assert isinstance(result, IntelligenceFeedData)
        assert hasattr(result, "items")
        assert hasattr(result, "total")
        assert hasattr(result, "unseenCount")

    async def test_get_feed_has_signals(self, mock_session):
        mapper = SignalMapper(mock_session, "tenant-1")
        result = await mapper.get_feed()
        if result.items:
            item = result.items[0]
            assert item.id
            assert item.category in ("tender", "regulatory", "competitor", "financial", "news")
            assert item.severity in ("low", "medium", "high", "critical")
