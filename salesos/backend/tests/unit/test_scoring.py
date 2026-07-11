"""Tests for scoring — ScoringMapper, feature computers, and scoring logic."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dashboard.mappers.scoring_mapper import ScoringMapper
from app.application.dashboard.dto.dashboard_dto import DecisionQueueData, DecisionItem
from runtime.feature_store import FeatureResult, FeatureComputer
from runtime.feature_store.features import (
    IcpComputer,
    FundingScoreComputer,
    HiringScoreComputer,
    GrowthScoreComputer,
    IntentScoreComputer,
    ExpansionScoreComputer,
    RevenueScoreComputer,
)


# ── Fake SQLAlchemy helpers ──────────────────────────────────────────────────

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


class FakeMappings:
    def __init__(self, rows=None, one=None):
        self._rows = rows or []
        self._one = one

    def one(self):
        return FakeMapping(self._one) if self._one else None

    def all(self):
        return [FakeMapping(r) for r in self._rows]


class FakeResult:
    def __init__(self, mappings_obj=None):
        self._mappings = mappings_obj or FakeMappings()

    def mappings(self):
        return self._mappings

    def scalar(self):
        return 0

    def scalar_one_or_none(self):
        return None


# ── ScoringMapper Tests ──────────────────────────────────────────────────────

class FakeExecute:
    """Returns different data based on SQL text patterns."""
    DEFAULT_ROWS = [
        {"id": "co-1", "name_ar": "شركة أ", "feature_name": "icp_score", "score": 0.85},
        {"id": "co-2", "name_ar": "شركة ب", "feature_name": "growth_score", "score": 0.72},
        {"id": "co-3", "name_ar": "شركة ج", "feature_name": "intent_score", "score": 0.91},
    ]

    def __init__(self, rows=None):
        self._rows = self.DEFAULT_ROWS if rows is None else rows

    async def __call__(self, sql_str, params=None):
        text = str(sql_str)
        if "company_features" in text:
            return FakeResult(FakeMappings(rows=self._rows))
        return FakeResult(FakeMappings())


@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    session.execute = FakeExecute()
    return session


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

    async def test_get_decisions_items_are_decision_items(self, mock_session):
        mapper = ScoringMapper(mock_session, "tenant-1")
        result = await mapper.get_decisions()
        for item in result.items:
            assert isinstance(item, DecisionItem)

    async def test_decision_item_has_required_fields(self, mock_session):
        mapper = ScoringMapper(mock_session, "tenant-1")
        result = await mapper.get_decisions()
        for item in result.items:
            assert item.id
            assert item.companyId
            assert item.companyName
            assert item.type == "opportunity"
            assert item.priority in ("high", "medium")
            assert 0 <= item.score <= 1

    async def test_high_score_means_high_priority(self, mock_session):
        mapper = ScoringMapper(mock_session, "tenant-1")
        result = await mapper.get_decisions()
        high_items = [i for i in result.items if i.score >= 0.85]
        for item in high_items:
            assert item.priority == "high"

    async def test_medium_score_means_medium_priority(self, mock_session):
        mapper = ScoringMapper(mock_session, "tenant-1")
        result = await mapper.get_decisions()
        medium_items = [i for i in result.items if i.score < 0.85]
        for item in medium_items:
            assert item.priority == "medium"

    async def test_total_matches_items_length(self, mock_session):
        mapper = ScoringMapper(mock_session, "tenant-1")
        result = await mapper.get_decisions()
        assert result.total == len(result.items)

    async def test_empty_results(self):
        session = AsyncMock(spec=AsyncSession)
        session.execute = FakeExecute(rows=[])
        mapper = ScoringMapper(session, "tenant-1")
        result = await mapper.get_decisions()
        assert len(result.items) == 0
        assert result.total == 0

    async def test_decision_item_title_includes_company_name(self, mock_session):
        mapper = ScoringMapper(mock_session, "tenant-1")
        result = await mapper.get_decisions()
        for item in result.items:
            assert item.companyName in item.title


# ── Feature Computer Tests ──────────────────────────────────────────────────

class TestIcpComputer:
    @pytest.fixture
    def computer(self):
        return IcpComputer()

    async def test_name(self, computer):
        assert computer.name == "icp_score"

    async def test_high_tech_score(self, computer):
        company = {"industry": "technology", "employee_count": 200, "country": "saudi arabia", "annual_revenue": 10000000}
        result = await computer.compute(company, AsyncMock())
        assert isinstance(result, FeatureResult)
        assert result.score > 0

    async def test_low_unknown_industry(self, computer):
        company = {"industry": "unknown", "employee_count": 1, "country": "unknown", "annual_revenue": 1000}
        result = await computer.compute(company, AsyncMock())
        assert result.score >= 0

    async def test_saudi_arabia_gets_full_region_points(self, computer):
        company = {"industry": "tech", "employee_count": 50, "country": "saudi arabia", "annual_revenue": 1000000}
        result = await computer.compute(company, AsyncMock())
        signals = result.contributing_signals
        assert signals.get("region") == "primary"

    async def test_gcc_country_gets_partial_points(self, computer):
        company = {"industry": "tech", "employee_count": 50, "country": "uae", "annual_revenue": 1000000}
        result = await computer.compute(company, AsyncMock())
        signals = result.contributing_signals
        assert signals.get("region") == "gcc"

    async def test_score_bounded(self, computer):
        company = {"industry": "technology", "employee_count": 1000, "country": "saudi arabia", "annual_revenue": 100000000}
        result = await computer.compute(company, AsyncMock())
        assert 0 <= result.score <= 100

    async def test_missing_fields_default_gracefully(self, computer):
        company = {}
        result = await computer.compute(company, AsyncMock())
        assert 0 <= result.score <= 100

    async def test_employee_tier_mapping(self, computer):
        company = {"industry": "tech", "employee_count": 250, "country": "sa", "annual_revenue": 1000000}
        result = await computer.compute(company, AsyncMock())
        signals = result.contributing_signals
        assert signals.get("employee_tier") == "201-1000"

    async def test_medium_company_tier(self, computer):
        company = {"industry": "tech", "employee_count": 200, "country": "sa", "annual_revenue": 1000000}
        result = await computer.compute(company, AsyncMock())
        signals = result.contributing_signals
        assert signals.get("employee_tier") == "51-200"

    async def test_small_company_tier(self, computer):
        company = {"industry": "tech", "employee_count": 5, "country": "sa", "annual_revenue": 1000000}
        result = await computer.compute(company, AsyncMock())
        signals = result.contributing_signals
        assert signals.get("employee_tier") == "1-10"

    async def test_confidence_depends_on_industry(self, computer):
        company_known = {"industry": "technology"}
        company_unknown = {"industry": "unknown"}
        result_known = await computer.compute(company_known, AsyncMock())
        result_unknown = await computer.compute(company_unknown, AsyncMock())
        assert result_known.confidence > result_unknown.confidence


class TestFeatureResult:
    def test_feature_result_creation(self):
        now = datetime.now(timezone.utc)
        result = FeatureResult(
            score=85.5,
            version=1,
            computed_at=now,
            confidence=0.8,
            contributing_signals={"industry_match": "high"},
            explanation="Test explanation",
        )
        assert result.score == 85.5
        assert result.version == 1
        assert result.confidence == 0.8
        assert result.contributing_signals == {"industry_match": "high"}
        assert result.explanation == "Test explanation"

    def test_feature_result_has_computed_at(self):
        now = datetime.now(timezone.utc)
        result = FeatureResult(score=50, version=1, computed_at=now, confidence=0.5, contributing_signals={}, explanation="")
        assert isinstance(result.computed_at, datetime)


class TestFeatureComputerBase:
    async def test_base_raises_not_implemented(self):
        computer = FeatureComputer()
        computer.name = "test"
        with pytest.raises(NotImplementedError):
            await computer.compute({}, AsyncMock())
