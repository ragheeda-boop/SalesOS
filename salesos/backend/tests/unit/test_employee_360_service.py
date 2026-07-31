"""Unit tests for Employee360Service — profile, portfolio, KPIs, and AI coach."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from datetime import datetime, timezone

from app.modules.employee_360.service import Employee360Service
from app.modules.employee_360.schemas import (
    AICoachAction,
    ActivityIntelligence,
    EmployeePortfolio,
    EmployeePortfolioItem,
    EmployeeKPIs,
)


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def service(mock_db):
    return Employee360Service(db=mock_db)


def _mock_user(**kwargs):
    defaults = {
        "id": uuid.uuid4(),
        "full_name": "Test User",
        "full_name_ar": "مستخدم اختبار",
        "email": "test@example.com",
        "role": "user",
        "department": "Engineering",
        "phone": "+966500000000",
        "avatar_url": None,
        "is_active": True,
        "tenant_id": uuid.uuid4(),
        "created_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    user = MagicMock()
    for k, v in defaults.items():
        setattr(user, k, v)
    return user


class TestComputeKpis:
    def test_compute_kpis_with_deals(self, service):
        portfolio = EmployeePortfolio(
            companies=[],
            contacts=[],
            pipeline=[
                EmployeePortfolioItem(id="1", name="Won Deal", type="opportunity",
                                      value=100000, status="closed_won"),
                EmployeePortfolioItem(id="2", name="Lost Deal", type="opportunity",
                                      value=50000, status="closed_lost"),
                EmployeePortfolioItem(id="3", name="Active Deal", type="opportunity",
                                      value=75000, status="qualifying"),
            ],
            revenue=100000,
            contracts=[],
            projects=[],
        )
        activity = ActivityIntelligence(total=30)

        kpis = service._compute_kpis(portfolio, activity)
        assert kpis.revenue == 100000
        assert kpis.pipeline == 75000
        assert kpis.win_rate == 0.5
        assert kpis.activities == 30
        assert kpis.productivity == 1.0

    def test_compute_kpis_empty_pipeline(self, service):
        portfolio = EmployeePortfolio(
            companies=[], contacts=[], pipeline=[],
            revenue=0, contracts=[], projects=[],
        )
        activity = ActivityIntelligence(total=0)

        kpis = service._compute_kpis(portfolio, activity)
        assert kpis.revenue == 0
        assert kpis.pipeline == 0
        assert kpis.win_rate == 0.0
        assert kpis.activities == 0
        assert kpis.productivity == 0.0

    def test_compute_kpis_all_won(self, service):
        portfolio = EmployeePortfolio(
            companies=[], contacts=[],
            pipeline=[
                EmployeePortfolioItem(id="1", name="Deal 1", type="opportunity",
                                      value=100000, status="closed_won"),
                EmployeePortfolioItem(id="2", name="Deal 2", type="opportunity",
                                      value=200000, status="won"),
            ],
            revenue=300000,
            contracts=[], projects=[],
        )
        activity = ActivityIntelligence(total=60)

        kpis = service._compute_kpis(portfolio, activity)
        assert kpis.win_rate == 1.0
        assert kpis.pipeline == 0

    def test_compute_kpis_only_active_deals(self, service):
        portfolio = EmployeePortfolio(
            companies=[], contacts=[],
            pipeline=[
                EmployeePortfolioItem(id="1", name="Active", type="opportunity",
                                      value=200000, status="developing"),
                EmployeePortfolioItem(id="2", name="Active 2", type="opportunity",
                                      value=300000, status="proposing"),
            ],
            revenue=0, contracts=[], projects=[],
        )
        activity = ActivityIntelligence(total=15)

        kpis = service._compute_kpis(portfolio, activity)
        assert kpis.pipeline == 500000
        assert kpis.win_rate == 0.0
        assert kpis.productivity == 0.5


class TestGenerateCoachActions:
    def test_empty_pipeline_generates_high_priority(self, service):
        portfolio = EmployeePortfolio(
            companies=[], contacts=[], pipeline=[],
            revenue=0, contracts=[], projects=[],
        )
        kpis = EmployeeKPIs(
            revenue=0, pipeline=0, win_rate=0.0,
            activities=0, productivity=0.0,
        )

        actions = service._generate_coach_actions(portfolio, kpis)
        assert len(actions) == 1
        assert actions[0].type == "pipeline_empty"
        assert actions[0].priority == "high"

    def test_low_win_rate_generates_medium_priority(self, service):
        portfolio = EmployeePortfolio(
            companies=[], contacts=[],
            pipeline=[
                EmployeePortfolioItem(id="1", name="Deal", type="opportunity",
                                      value=10000, status="closed_lost"),
            ],
            revenue=0, contracts=[], projects=[],
        )
        kpis = EmployeeKPIs(
            revenue=0, pipeline=0, win_rate=0.2,
            activities=10, productivity=0.33,
        )

        actions = service._generate_coach_actions(portfolio, kpis)
        types = {a.type for a in actions}
        assert "win_rate_low" in types
        assert any(a.priority == "medium" for a in actions if a.type == "win_rate_low")

    def test_healthy_pipeline_generates_on_track(self, service):
        portfolio = EmployeePortfolio(
            companies=[], contacts=[],
            pipeline=[
                EmployeePortfolioItem(id="1", name="Deal", type="opportunity",
                                      value=100000, status="qualifying"),
            ],
            revenue=200000, contracts=[], projects=[],
        )
        kpis = EmployeeKPIs(
            revenue=200000, pipeline=100000, win_rate=0.6,
            activities=30, productivity=1.0,
        )

        actions = service._generate_coach_actions(portfolio, kpis)
        assert len(actions) == 1
        assert actions[0].type in ("low_activity", "on_track")
        assert actions[0].priority in ("low", "medium")

    def test_both_empty_and_low_win_rate(self, service):
        portfolio = EmployeePortfolio(
            companies=[], contacts=[], pipeline=[],
            revenue=0, contracts=[], projects=[],
        )
        kpis = EmployeeKPIs(
            revenue=0, pipeline=0, win_rate=0.1,
            activities=5, productivity=0.17,
        )

        actions = service._generate_coach_actions(portfolio, kpis)
        types = {a.type for a in actions}
        assert "pipeline_empty" in types


class TestGetActivityIntelligence:
    @pytest.mark.asyncio
    async def test_no_activity_runtime(self, service):
        service.activity_runtime = None
        result = await service._get_activity_intelligence(str(uuid.uuid4()), str(uuid.uuid4()))
        assert result.meetings == 0
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_with_activity_runtime(self, service):
        mock_runtime = AsyncMock()
        mock_runtime.get_by_actor.return_value = (
            [
                {"action": "meeting.created"},
                {"action": "meeting.updated"},
                {"action": "email.sent"},
                {"action": "call.completed"},
                {"action": "task.created"},
                {"action": "task.completed"},
                {"action": "meeting.scheduled"},
            ],
            7,
        )
        service.activity_runtime = mock_runtime

        result = await service._get_activity_intelligence(str(uuid.uuid4()), str(uuid.uuid4()))
        assert result.meetings == 3
        assert result.emails == 1
        assert result.calls == 1
        assert result.tasks == 2
        assert result.total == 7

    @pytest.mark.asyncio
    async def test_activity_runtime_exception(self, service):
        mock_runtime = AsyncMock()
        mock_runtime.get_by_actor.side_effect = RuntimeError("Connection failed")
        service.activity_runtime = mock_runtime

        result = await service._get_activity_intelligence(str(uuid.uuid4()), str(uuid.uuid4()))
        assert result.total == 0


class TestGetProfile:
    @pytest.mark.asyncio
    async def test_get_profile_found(self, service, mock_db):
        user = _mock_user()
        team_user = _mock_user(full_name="Team Member")
        team_user.id = uuid.uuid4()

        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = user
        team_result = MagicMock()
        team_result.scalars.return_value.all.return_value = [user, team_user]

        mock_db.execute.side_effect = [user_result, team_result]

        profile = await service._get_profile(str(user.id), str(user.tenant_id))
        assert profile.full_name == "Test User"
        assert profile.email == "test@example.com"
        assert len(profile.team) == 1
        assert profile.team[0]["full_name"] == "Team Member"

    @pytest.mark.asyncio
    async def test_get_profile_not_found(self, service, mock_db):
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = user_result

        from app.common.exceptions import NotFoundError
        with pytest.raises(NotFoundError):
            await service._get_profile(str(uuid.uuid4()), str(uuid.uuid4()))
