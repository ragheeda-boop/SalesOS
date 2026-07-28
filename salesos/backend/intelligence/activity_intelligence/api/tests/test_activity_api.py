"""Unit tests for Activity Intelligence API router."""
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from intelligence.activity_intelligence.api.router import router


class TestActivityRouterRegistration:
    def test_router_has_expected_routes(self):
        paths = [route.path for route in router.routes]
        assert "/api/v1/activity/dashboard" in paths
        assert "/api/v1/activity/company/{company_id}" in paths
        assert "/api/v1/activity/email" in paths
        assert "/api/v1/activity/calendar" in paths
        assert "/api/v1/activity/followups" in paths
        assert "/api/v1/activity/engagement" in paths
        assert "/api/v1/activity/employee/{employee_id}/email" in paths
        assert "/api/v1/activity/employee/{employee_id}/calendar" in paths
        assert len(paths) == 8


class TestActivityDashboardEndpoint:
    @pytest.mark.asyncio
    async def test_dashboard_returns_email_and_calendar_counts(self):
        from intelligence.activity_intelligence.api.router import get_dashboard

        mock_db = AsyncMock()
        call_count = [0]

        email_result = MagicMock()
        email_result.mappings.return_value.one.return_value = {
            "total": 150, "inbound": 90, "outbound": 60
        }
        cal_result = MagicMock()
        cal_result.mappings.return_value.one.return_value = {
            "total": 45, "active": 40, "cancelled": 5, "total_minutes": 2700
        }
        top_result = MagicMock()
        top_result.mappings.return_value.all.return_value = []

        async def mock_execute(sql, params=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return email_result
            elif call_count[0] == 2:
                return cal_result
            elif call_count[0] == 3:
                # top_companies_total
                total_result = MagicMock()
                total_result.mappings.return_value.one.return_value = {"c": 0}
                return total_result
            elif call_count[0] == 5:
                # followup_row
                follow_result = MagicMock()
                follow_result.mappings.return_value.one.return_value = {
                    "need_followup": 0,
                    "overdue": 0,
                }
                return follow_result
            return top_result

        mock_db.execute = mock_execute

        result = await get_dashboard(tenant_id=str(uuid4()), db=mock_db)

        assert result["email_count"] == 150
        assert result["email_inbound"] == 90
        assert result["email_outbound"] == 60
        assert result["meeting_count"] == 45
        assert result["meeting_active"] == 40
        assert result["meeting_hours"] == 45.0
        assert result["period"] == "30d"
        assert "limit" in result
        assert "offset" in result
        assert "top_companies_total" in result
