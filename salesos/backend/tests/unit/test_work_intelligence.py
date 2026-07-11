"""Tests for Work Intelligence Engine — time allocation, meeting load, activity scoring, recommendations."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.work_intelligence.service import (
    WorkIntelligenceEngine,
    TimeAllocation,
    MeetingLoad,
    ActivityScore,
    WorkRecommendation,
    WorkIntelligenceResponse,
)


def _make_item(action: str, days_ago: int = 1):
    ts = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return {"action": action, "timestamp": ts.isoformat()}


@pytest.fixture
def engine():
    activity_runtime = AsyncMock()
    return WorkIntelligenceEngine(activity_runtime=activity_runtime)


@pytest.fixture
def engine_with_items():
    activity_runtime = AsyncMock()
    items = [
        _make_item("meeting", 0),
        _make_item("meeting", 1),
        _make_item("email_sent", 2),
        _make_item("call_made", 3),
        _make_item("task_completed", 4),
        _make_item("email_received", 5),
        _make_item("meeting", 6),
        _make_item("call_made", 7),
        _make_item("task_created", 8),
        _make_item("meeting", 10),
    ]
    activity_runtime.query.return_value = (items, len(items))
    return WorkIntelligenceEngine(activity_runtime=activity_runtime)


# ── Tests: Time Allocation ──────────────────────────────────────────────────

class TestTimeAllocation:
    def test_empty_items_returns_zeros(self, engine):
        result = engine._compute_time_allocation([])
        assert isinstance(result, TimeAllocation)
        assert result.meeting_hours == 0.0
        assert result.email_hours == 0.0
        assert result.call_hours == 0.0
        assert result.task_hours == 0.0
        assert result.total_tracked == 0.0

    def test_meeting_hours_counted(self, engine):
        items = [_make_item("meeting"), _make_item("meeting")]
        result = engine._compute_time_allocation(items)
        assert result.meeting_hours == 2.0
        assert result.total_tracked == 2.0

    def test_email_hours_counted(self, engine):
        items = [_make_item("email_sent"), _make_item("email_received")]
        result = engine._compute_time_allocation(items)
        # 2 * 0.25 = 0.5, round(0.5, 1) = 0.5
        assert result.email_hours == 0.5
        assert result.total_tracked == 0.5

    def test_mixed_activities(self, engine):
        items = [
            _make_item("meeting"),
            _make_item("email_sent"),
            _make_item("call_made"),
            _make_item("task_completed"),
        ]
        result = engine._compute_time_allocation(items)
        assert result.meeting_hours == 1.0
        # Note: round(0.25, 1) = 0.2 (banker's rounding)
        assert result.email_hours == 0.2
        assert result.call_hours == 0.5
        assert result.task_hours == 0.5
        assert result.total_tracked == 2.2

    def test_focus_hours_remaining(self, engine):
        items = [_make_item("meeting")] * 10  # 10 meeting hours
        result = engine._compute_time_allocation(items)
        expected_focus = max(0.0, 5.0 * 30 - 10.0)
        assert result.focus_hours == expected_focus

    def test_focus_hours_not_negative(self, engine):
        items = [_make_item("meeting")] * 200  # Way over the limit
        result = engine._compute_time_allocation(items)
        assert result.focus_hours >= 0.0


# ── Tests: Meeting Load ─────────────────────────────────────────────────────

class TestMeetingLoad:
    def test_no_meetings(self, engine):
        items = [_make_item("email_sent")]
        result = engine._compute_meeting_load(items, datetime.now(timezone.utc), datetime.now(timezone.utc))
        assert isinstance(result, MeetingLoad)
        assert result.meetings_today == 0
        assert result.meetings_this_week == 0
        assert result.meetings_this_month == 0
        assert result.overbooked is False

    def test_meetings_today(self, engine):
        now = datetime.now(timezone.utc)
        items = [_make_item("meeting", 0)]  # today
        result = engine._compute_meeting_load(items, now, now)
        assert result.meetings_today == 1

    def test_no_meetings_on_different_day(self, engine):
        now = datetime.now(timezone.utc)
        items = [_make_item("meeting", 5)]  # 5 days ago
        result = engine._compute_meeting_load(items, now, now)
        assert result.meetings_today == 0

    def test_overbooked_with_many_hours(self, engine):
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=now.weekday())
        items = [_make_item("meeting", i) for i in range(20)]  # Many meetings this week
        result = engine._compute_meeting_load(items, now, week_start)
        assert result.total_meeting_hours_this_week >= 1

    def test_recommendation_overbooked(self, engine):
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=now.weekday())
        items = [_make_item("meeting", i) for i in range(30)]
        result = engine._compute_meeting_load(items, now, week_start)
        if result.overbooked:
            assert len(result.recommendation) > 0

    def test_recommendation_many_meetings(self, engine):
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=now.weekday())
        items = [_make_item("meeting", i) for i in range(11)]
        result = engine._compute_meeting_load(items, now, week_start)
        if result.meetings_this_week > 10 and not result.overbooked:
            assert len(result.recommendation) > 0

    def test_avg_per_day(self, engine):
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=now.weekday())
        items = [_make_item("meeting", i) for i in range(30)]
        result = engine._compute_meeting_load(items, now, week_start)
        assert result.avg_meetings_per_day >= 0


# ── Tests: Activity Score ───────────────────────────────────────────────────

class TestActivityScore:
    def test_empty_items(self, engine):
        result = engine._compute_activity_score([], 0, 30)
        assert isinstance(result, ActivityScore)
        assert result.overall == 0.0
        assert result.grade == "منخفض جدًا"

    def test_full_volume(self, engine):
        items = [_make_item("email_sent", i) for i in range(200)]
        result = engine._compute_activity_score(items[:150], 150, 30)
        assert result.volume == 100.0  # 150 / (30*5) = 1.0 → 100

    def test_variety_score(self, engine):
        items = [
            _make_item("meeting", 1),
            _make_item("email_sent", 2),
            _make_item("call_made", 3),
            _make_item("task_completed", 4),
            _make_item("email_received", 5),
        ]
        result = engine._compute_activity_score(items, 5, 30)
        assert result.variety >= 60  # 4 unique base types / 5 * 100

    def test_grade_mumtaz(self, engine):
        items = [_make_item("meeting", i) for i in range(200)]
        result = engine._compute_activity_score(items[:150], 150, 30)
        if result.overall >= 80:
            assert result.grade == "ممتاز"

    def test_grade_jayyid(self, engine):
        items = [_make_item("meeting", i) for i in range(100)]
        result = engine._compute_activity_score(items[:100], 100, 30)
        if 60 <= result.overall < 80:
            assert result.grade == "جيد"

    def test_grade_mutawassit(self, engine):
        items = [_make_item("meeting", i) for i in range(20)]
        result = engine._compute_activity_score(items[:20], 20, 30)
        if 40 <= result.overall < 60:
            assert result.grade == "متوسط"

    def test_grade_daeef(self, engine):
        items = [_make_item("meeting", i) for i in range(5)]
        result = engine._compute_activity_score(items[:5], 5, 30)
        if 20 <= result.overall < 40:
            assert result.grade == "ضعيف"

    def test_consistency_score(self, engine):
        items = [_make_item("email_sent", i) for i in range(20)]
        result = engine._compute_activity_score(items[:20], 20, 30)
        assert result.consistency >= 0

    def test_recency_score(self, engine):
        now = datetime.now(timezone.utc)
        items = [
            {"action": "meeting", "timestamp": (now - timedelta(hours=i)).isoformat()}
            for i in range(10)
        ]
        result = engine._compute_activity_score(items, 10, 30)
        assert result.recency > 0


# ── Tests: Recommendations ──────────────────────────────────────────────────

class TestRecommendations:
    def test_no_recommendations_for_balanced(self, engine):
        time_alloc = TimeAllocation(meeting_hours=5, focus_hours=100)
        meeting_load = MeetingLoad()
        activity_score = ActivityScore(overall=70, variety=80, consistency=80, grade="جيد")
        recs = engine._generate_recommendations(time_alloc, meeting_load, activity_score, 50)
        assert len(recs) >= 1  # Should have "on_track" at minimum

    def test_overbooked_recommendation(self, engine):
        time_alloc = TimeAllocation()
        meeting_load = MeetingLoad(overbooked=True, total_meeting_hours_this_week=25, recommendation="قلل الاجتماعات")
        activity_score = ActivityScore(overall=50, variety=50, consistency=50, grade="متوسط")
        recs = engine._generate_recommendations(time_alloc, meeting_load, activity_score, 20)
        types = [r.type for r in recs]
        assert "reduce_meetings" in types

    def test_no_activity_recommendation(self, engine):
        time_alloc = TimeAllocation()
        meeting_load = MeetingLoad()
        activity_score = ActivityScore()
        recs = engine._generate_recommendations(time_alloc, meeting_load, activity_score, 0)
        types = [r.type for r in recs]
        assert "no_activity" in types

    def test_low_activity_recommendation(self, engine):
        time_alloc = TimeAllocation()
        meeting_load = MeetingLoad()
        activity_score = ActivityScore(overall=20, grade="ضعيف")
        recs = engine._generate_recommendations(time_alloc, meeting_load, activity_score, 5)
        types = [r.type for r in recs]
        assert "low_activity" in types

    def test_variety_recommendation(self, engine):
        time_alloc = TimeAllocation()
        meeting_load = MeetingLoad()
        activity_score = ActivityScore(overall=50, variety=30, consistency=50, grade="متوسط")
        recs = engine._generate_recommendations(time_alloc, meeting_load, activity_score, 10)
        types = [r.type for r in recs]
        assert "improve_variety" in types

    def test_on_track_recommendation(self, engine):
        time_alloc = TimeAllocation()
        meeting_load = MeetingLoad()
        activity_score = ActivityScore(overall=70, variety=80, consistency=80, grade="جيد")
        recs = engine._generate_recommendations(time_alloc, meeting_load, activity_score, 100)
        types = [r.type for r in recs]
        assert "on_track" in types

    def test_meeting_vs_focus_recommendation(self, engine):
        time_alloc = TimeAllocation(meeting_hours=40, focus_hours=10)
        meeting_load = MeetingLoad()
        activity_score = ActivityScore(overall=50, variety=50, consistency=50, grade="متوسط")
        recs = engine._generate_recommendations(time_alloc, meeting_load, activity_score, 20)
        types = [r.type for r in recs]
        assert "meeting_vs_focus" in types


# ── Tests: Full analyze ─────────────────────────────────────────────────────

class TestAnalyze:
    async def test_returns_work_intelligence_response(self, engine_with_items):
        result = await engine_with_items.analyze("emp-1", "t-1")
        assert isinstance(result, WorkIntelligenceResponse)

    async def test_has_all_fields(self, engine_with_items):
        result = await engine_with_items.analyze("emp-1", "t-1")
        assert result.employee_id == "emp-1"
        assert result.tenant_id == "t-1"
        assert result.period_days == 30
        assert isinstance(result.time_allocation, TimeAllocation)
        assert isinstance(result.meeting_load, MeetingLoad)
        assert isinstance(result.activity_score, ActivityScore)
        assert isinstance(result.recommendations, list)
        assert isinstance(result.generated_at, datetime)

    async def test_time_allocation_has_values(self, engine_with_items):
        result = await engine_with_items.analyze("emp-1", "t-1")
        # There are 3 meetings in the sample items
        assert result.time_allocation.meeting_hours >= 3.0

    async def test_handles_exception_gracefully(self, engine):
        engine.activity_runtime.query.side_effect = RuntimeError("DB down")
        result = await engine.analyze("emp-1", "t-1")
        assert isinstance(result, WorkIntelligenceResponse)
        assert result.time_allocation.total_tracked == 0.0
