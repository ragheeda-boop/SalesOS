"""Unit tests for Calendar, Email, Productivity, and Executive services."""

import pytest
from datetime import datetime, timezone, timedelta

from domains.employee.calendar_service import CalendarIntelligenceService
from domains.employee.email_service import EmailIntelligenceService
from domains.employee.productivity_service import ProductivityService, RelationshipService
from domains.employee.executive_service import ExecutiveDashboardService


class TestCalendarIntelligenceService:
    async def test_get_kpis_returns_defaults_for_no_data(self, db_session):
        svc = CalendarIntelligenceService(db_session)
        result = await svc.get_kpis("00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000001")
        assert result["today_count"] == 0
        assert result["week_count"] == 0
        assert result["month_count"] == 0
        assert result["total_hours"] == 0
        assert result["cancellation_rate"] == 0
        assert result["focus_time_hours"] == 160
        assert result["upcoming"] == []

    async def test_get_heatmap_returns_empty_for_no_data(self, db_session):
        svc = CalendarIntelligenceService(db_session)
        result = await svc.get_heatmap("00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000001")
        assert isinstance(result, list)
        assert len(result) == 0


class TestEmailIntelligenceService:
    async def test_get_kpis_returns_defaults_for_no_data(self, db_session):
        svc = EmailIntelligenceService(db_session)
        result = await svc.get_kpis("00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000001")
        assert result["sent"] == 0
        assert result["received"] == 0
        assert result["total"] == 0
        assert result["unread_count"] == 0
        assert result["avg_response_hours"] == 0.0
        assert result["period_days"] == 30

    async def test_get_top_contacts_empty(self, db_session):
        svc = EmailIntelligenceService(db_session)
        result = await svc.get_top_contacts("00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000001")
        assert isinstance(result, list)
        assert len(result) == 0

    async def test_get_daily_volume_empty(self, db_session):
        svc = EmailIntelligenceService(db_session)
        result = await svc.get_daily_volume("00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000001")
        assert isinstance(result, list)


class TestProductivityService:
    async def test_compute_returns_defaults_for_no_data(self, db_session):
        svc = ProductivityService(db_session)
        result = await svc.compute("00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000001")
        assert result["productivity_score"] == 0.0
        assert result["burnout_risk"] == "low"
        assert result["trend_direction"] == "stable"
        assert result["period_days"] == 30


class TestRelationshipService:
    async def test_compute_relationship_score_defaults(self, db_session):
        svc = RelationshipService(db_session)
        result = await svc.compute_relationship_score(
            "00000000-0000-0000-0000-000000000001",
            "00000000-0000-0000-0000-000000000001",
            "00000000-0000-0000-0000-000000000002",
            "company",
        )
        assert "relationship_score" in result
        assert "strength" in result
        assert result["meetings_last_90d"] == 0
        assert result["emails_last_90d"] == 0


class TestExecutiveDashboardService:
    async def test_get_summary_returns_structure(self, db_session):
        svc = ExecutiveDashboardService(db_session)
        result = await svc.get_summary("00000000-0000-0000-0000-000000000001")
        assert "total_employees" in result
        assert "active_employees" in result
        assert "avg_score" in result
        assert "departments" in result
        assert "top_performers" in result
        assert "generated_at" in result
        assert isinstance(result["departments"], list)
        assert isinstance(result["top_performers"], list)
