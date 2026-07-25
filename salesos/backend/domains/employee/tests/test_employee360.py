"""Tests for Employee360 enhanced response and timeline filter — B-1, B-2."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domains.employee.models import EmployeeSignal, EmployeeScore, SignalSource, SignalType
from app.modules.employee_360.schemas import (
    Employee360Response,
    EmployeeTimeline,
    PerformanceInsights,
    ScoreTrend,
    PeerComparison,
    RiskFlagItem,
    TimelineEvent,
    EmployeeProfile,
    EmployeeSignals,
    EmployeeSignalSummary,
)

NOW = datetime.now(timezone.utc)


def _signal(
    employee_id: str, tenant_id: str,
    signal_type: str, source: str,
    timestamp: datetime | None = None,
    metadata: dict | None = None,
) -> EmployeeSignal:
    return EmployeeSignal(
        id=str(uuid.uuid4()),
        employee_id=employee_id,
        tenant_id=tenant_id,
        signal_type=signal_type,
        source=source,
        metadata=metadata or {},
        timestamp=timestamp or datetime.now(timezone.utc),
    )


class TestEmployee360ResponseSchemas:
    def test_360_response_includes_timeline(self):
        resp = Employee360Response(
            profile=EmployeeProfile(
                id="e1", full_name="Test", email="t@t.com",
                role="user", tenant_id="t1", is_active=True,
                created_at=NOW,
            ),
            timeline=EmployeeTimeline(
                events=[
                    TimelineEvent(
                        id="ev1", signal_type="email_sent",
                        source="timeline", timestamp=datetime.now(timezone.utc),
                    ),
                ],
                total=1,
            ),
        )
        assert len(resp.timeline.events) == 1
        assert resp.timeline.events[0].signal_type == "email_sent"

    def test_360_response_includes_performance(self):
        resp = Employee360Response(
            profile=EmployeeProfile(
                id="e1", full_name="Test", email="t@t.com",
                role="user", tenant_id="t1", is_active=True,
                created_at=NOW,
            ),
            performance=PerformanceInsights(
                trend=ScoreTrend(
                    current_score=0.8,
                    previous_score=0.6,
                    delta=0.2,
                    direction="improving",
                ),
                peer_comparison=PeerComparison(
                    employee_score=0.8,
                    department_average=0.65,
                    percentile=75,
                    above_average=True,
                ),
                risk_flags=[
                    RiskFlagItem(
                        flag="declining_signals",
                        severity="high",
                        message="Signal volume dropped 60%",
                    ),
                ],
            ),
        )
        assert resp.performance.trend.direction == "improving"
        assert resp.performance.peer_comparison.above_average is True
        assert len(resp.performance.risk_flags) == 1

    def test_360_response_defaults(self):
        resp = Employee360Response(
            profile=EmployeeProfile(
                id="e1", full_name="Test", email="t@t.com",
                role="user", tenant_id="t1", is_active=True,
                created_at=NOW,
            ),
        )
        assert resp.timeline.events == []
        assert resp.timeline.total == 0
        assert resp.performance.trend.direction == "stable"
        assert resp.performance.risk_flags == []

    def test_timeline_event_schema(self):
        ev = TimelineEvent(
            id="ev1",
            signal_type="meeting_completed",
            source="timeline",
            metadata={"duration": 30},
            timestamp=datetime.now(timezone.utc),
        )
        assert ev.source == "timeline"
        assert ev.metadata["duration"] == 30

    def test_score_trend_schema(self):
        t = ScoreTrend(current_score=0.9, delta=0.15, direction="improving")
        assert t.period_days == 30

    def test_peer_comparison_schema(self):
        pc = PeerComparison(employee_score=0.8, department_average=0.6, percentile=80)
        assert pc.above_average is False

    def test_risk_flag_schema(self):
        rf = RiskFlagItem(flag="low_engagement", severity="medium", message="Low activity")
        assert rf.detail == {}

    def test_performance_insights_defaults(self):
        pi = PerformanceInsights()
        assert pi.trend.direction == "stable"
        assert pi.peer_comparison.percentile == 0
        assert pi.risk_flags == []


class TestEmployeeTimelineSchema:
    def test_empty_timeline(self):
        t = EmployeeTimeline()
        assert t.events == []
        assert t.total == 0
        assert t.next_cursor is None

    def test_timeline_with_cursor(self):
        t = EmployeeTimeline(
            events=[],
            total=50,
            next_cursor="abc123",
        )
        assert t.next_cursor == "abc123"

    def test_timeline_multiple_events(self):
        now = datetime.now(timezone.utc)
        events = [
            TimelineEvent(
                id=f"ev{i}",
                signal_type="email_sent",
                source="timeline",
                timestamp=now - timedelta(hours=i),
            )
            for i in range(10)
        ]
        t = EmployeeTimeline(events=events, total=10)
        assert len(t.events) == 10
        assert t.events[0].id == "ev0"


class TestEmployee360ServiceTimeline:
    @pytest.fixture
    def mock_repo(self):
        repo = MagicMock()
        repo.save = AsyncMock()
        repo.save_many = AsyncMock()
        repo.save_score = AsyncMock()
        repo.get_by_employee = AsyncMock(return_value=([], 0, None))
        repo.get_latest_score = AsyncMock(return_value=None)
        repo.get_summary = AsyncMock(return_value={
            "total_signals": 0,
            "by_source": {},
            "by_type": {},
            "recent_signals": [],
        })
        return repo

    @pytest.fixture
    def mock_db(self):
        from unittest.mock import AsyncMock
        db = AsyncMock()
        result = AsyncMock()
        result.scalar_one_or_none = MagicMock(return_value=None)
        db.execute = AsyncMock(return_value=result)
        db.scalar = AsyncMock(return_value=0)
        return db

    async def test_get_timeline_with_signals(self, mock_repo):
        now = datetime.now(timezone.utc)
        signals = [
            _signal("e1", "t1", SignalType.EMAIL_SENT.value, SignalSource.TIMELINE.value,
                    now - timedelta(hours=i))
            for i in range(5)
        ]
        mock_repo.get_by_employee = AsyncMock(return_value=(signals, 5, None))

        from app.modules.employee_360.service import Employee360Service
        from app.modules.employee_360.schemas import EmployeeTimeline

        service = Employee360Service(db=AsyncMock(), signal_repo=mock_repo)
        timeline = await service._get_timeline("e1", "t1")

        assert isinstance(timeline, EmployeeTimeline)
        assert len(timeline.events) == 5
        assert timeline.total == 5

    async def test_get_timeline_no_repo(self):
        from app.modules.employee_360.service import Employee360Service

        service = Employee360Service(db=AsyncMock(), signal_repo=None)
        timeline = await service._get_timeline("e1", "t1")
        assert timeline.events == []

    async def test_get_timeline_repo_error(self, mock_repo):
        mock_repo.get_by_employee = AsyncMock(side_effect=Exception("db error"))
        from app.modules.employee_360.service import Employee360Service

        service = Employee360Service(db=AsyncMock(), signal_repo=mock_repo)
        timeline = await service._get_timeline("e1", "t1")
        assert timeline.events == []


class TestEmployee360ServicePerformance:
    @pytest.fixture
    def mock_repo(self):
        repo = MagicMock()
        repo.save = AsyncMock()
        repo.save_many = AsyncMock()
        repo.save_score = AsyncMock()
        repo.get_by_employee = AsyncMock(return_value=([], 0, None))
        repo.get_latest_score = AsyncMock(return_value=None)
        return repo

    async def test_get_performance_with_score(self, mock_repo):
        mock_repo.get_latest_score = AsyncMock(return_value=EmployeeScore(
            id="s1", employee_id="e1", tenant_id="t1",
            overall_score=0.75,
        ))
        mock_repo.get_by_employee = AsyncMock(return_value=([], 0, None))

        from app.modules.employee_360.service import Employee360Service
        from domains.employee.performance import EmployeePerformanceEngine
        service = Employee360Service(db=AsyncMock(), signal_repo=mock_repo)

        signal_data = {
            "score": {
                "id": "s1", "employee_id": "e1", "tenant_id": "t1",
                "overall_score": 0.75,
                "signal_volume_score": 0.7,
                "recency_score": 0.8,
                "diversity_score": 0.6,
                "completion_rate": 0.8,
                "confidence_interval_low": 0.6,
                "confidence_interval_high": 0.9,
                "signal_count": 15,
            }
        }
        with patch.object(EmployeePerformanceEngine, '_get_peer_scores', new_callable=AsyncMock, return_value=[]):
            perf = await service._get_performance("e1", "t1", signal_data)
        assert isinstance(perf, PerformanceInsights)
        assert perf.trend.current_score == 0.75

    async def test_get_performance_no_repo(self):
        from app.modules.employee_360.service import Employee360Service
        service = Employee360Service(db=AsyncMock(), signal_repo=None)
        perf = await service._get_performance("e1", "t1", None)
        assert perf.trend.direction == "stable"
        assert perf.risk_flags == []

    async def test_get_performance_repo_error(self, mock_repo):
        mock_repo.get_by_employee = AsyncMock(side_effect=Exception("db error"))
        from app.modules.employee_360.service import Employee360Service
        service = Employee360Service(db=AsyncMock(), signal_repo=mock_repo)
        perf = await service._get_performance("e1", "t1", None)
        assert perf.trend.direction == "stable"


class TestCoachActionsPerformance:
    def test_coach_with_risk_flags(self):
        from app.modules.employee_360.service import Employee360Service
        from app.modules.employee_360.schemas import (
            PerformanceInsights, RiskFlagItem, ScoreTrend, PeerComparison,
            EmployeePortfolio, EmployeeKPIs,
        )

        service = Employee360Service(db=AsyncMock())
        perf = PerformanceInsights(
            risk_flags=[
                RiskFlagItem(flag="declining_signals", severity="high", message="Activity dropping"),
                RiskFlagItem(flag="low_engagement", severity="medium", message="Low activity"),
            ],
        )
        actions = service._generate_coach_actions(
            EmployeePortfolio(),
            EmployeeKPIs(signal_count=10, diversity_score=0.5),
            perf,
        )
        types = [a.type for a in actions]
        assert "declining_signals" in types
        assert "low_engagement" in types

    def test_coach_no_performance(self):
        from app.modules.employee_360.service import Employee360Service
        from app.modules.employee_360.schemas import EmployeePortfolio, EmployeeKPIs

        service = Employee360Service(db=AsyncMock())
        actions = service._generate_coach_actions(
            EmployeePortfolio(), EmployeeKPIs(),
        )
        assert len(actions) == 1
        assert actions[0].type == "pipeline_empty"
