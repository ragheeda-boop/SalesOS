"""Unit tests for Activity Intelligence service wiring."""

from __future__ import annotations

from dataclasses import asdict
from unittest.mock import AsyncMock, MagicMock

import pytest

from intelligence.activity_intelligence.contracts.models import (
    ActivityDashboardDTO,
    CompanyEngagementDTO,
    EngagementScore,
    FollowUpStatus,
)
from intelligence.activity_intelligence.service import ActivityIntelligenceService


@pytest.mark.asyncio
async def test_get_dashboard_uses_readers():
    db = MagicMock()
    svc = ActivityIntelligenceService(db)
    svc.email_reader.tenant_totals = AsyncMock(return_value={"email_count": 12})
    svc.meeting_reader.tenant_totals = AsyncMock(return_value={"meeting_count": 4})

    result = await svc.get_dashboard("tenant-1")
    assert isinstance(result, ActivityDashboardDTO)
    assert result.email_count == 12
    assert result.meeting_count == 4


@pytest.mark.asyncio
async def test_get_company_engagement_serializable():
    db = MagicMock()
    svc = ActivityIntelligenceService(db)
    svc.email_engine.get_email_metrics = AsyncMock(
        return_value={
            "email_count_sent": 3,
            "email_count_received": 2,
            "reply_rate": 0.5,
            "last_email_days": 1,
        }
    )
    svc.calendar_engine.get_meeting_metrics = AsyncMock(
        return_value={
            "meeting_count": 1,
            "meeting_hours": 1.5,
            "meeting_completion_rate": 1.0,
            "last_meeting_days": 2,
        }
    )
    svc.engagement_engine.get_relationship_health = AsyncMock(
        return_value={"relationship_health": 0.7, "metrics": {}}
    )
    svc.followup_engine.get_status = AsyncMock(
        return_value=FollowUpStatus(company_id="c1", priority="medium")
    )

    result = await svc.get_company_engagement("c1", "t1")
    assert isinstance(result, CompanyEngagementDTO)
    assert result.email_count == 5
    assert result.meeting_count == 1
    assert isinstance(result.score, EngagementScore)
    serialized = asdict(result)
    assert serialized["company_id"] == "c1"
