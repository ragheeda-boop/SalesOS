"""Activity Intelligence application service — real DB-backed aggregations."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from intelligence.activity_intelligence.adapters.postgres_readers import (
    PostgresEmailReader,
    PostgresMeetingReader,
)
from intelligence.activity_intelligence.contracts.models import (
    ActivityDashboardDTO,
    CompanyEngagementDTO,
    EngagementScore,
    FollowUpStatus,
)
from intelligence.activity_intelligence.engine.calendar_engine import CalendarEngine
from intelligence.activity_intelligence.engine.email_engine import EmailEngine
from intelligence.activity_intelligence.engine.engagement_engine import EngagementEngine
from intelligence.activity_intelligence.engine.followup_engine import FollowupEngine
from intelligence.activity_intelligence.engine.plugins import register_default_plugins


class ActivityIntelligenceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.email_reader = PostgresEmailReader(db)
        self.meeting_reader = PostgresMeetingReader(db)
        self.email_engine = EmailEngine(self.email_reader)
        self.calendar_engine = CalendarEngine(self.meeting_reader)
        self.engagement_engine = EngagementEngine(
            email_engine=self.email_engine,
            calendar_engine=self.calendar_engine,
        )
        register_default_plugins(self.engagement_engine)
        self.followup_engine = FollowupEngine(
            email_engine=self.email_engine,
            calendar_engine=self.calendar_engine,
        )

    async def get_dashboard(self, tenant_id: str) -> ActivityDashboardDTO:
        email_totals = await self.email_reader.tenant_totals(tenant_id)
        meeting_totals = await self.meeting_reader.tenant_totals(tenant_id)
        return ActivityDashboardDTO(
            email_count=email_totals["email_count"],
            meeting_count=meeting_totals["meeting_count"],
            followup_count=0,
            overdue_count=0,
            top_companies=[],
            engagement_trend=[],
        )

    async def get_company_engagement(
        self, company_id: str, tenant_id: str
    ) -> CompanyEngagementDTO:
        email_metrics = await self.email_engine.get_email_metrics(company_id, tenant_id)
        meeting_metrics = await self.calendar_engine.get_meeting_metrics(company_id, tenant_id)
        health = await self.engagement_engine.get_relationship_health(company_id, tenant_id)
        followup = await self.followup_engine.get_status(company_id, tenant_id)

        last_email = email_metrics.get("last_email_days")
        last_meeting = meeting_metrics.get("last_meeting_days")
        last_activity = None
        candidates = [d for d in (last_email, last_meeting) if d is not None]
        if candidates:
            last_activity = min(candidates)

        score = EngagementScore(
            company_id=company_id,
            email_count_sent=email_metrics.get("email_count_sent", 0),
            email_count_received=email_metrics.get("email_count_received", 0),
            reply_rate=email_metrics.get("reply_rate", 0.0),
            meeting_count=meeting_metrics.get("meeting_count", 0),
            meeting_hours=meeting_metrics.get("meeting_hours", 0.0),
            meeting_completion_rate=meeting_metrics.get("meeting_completion_rate", 0.0),
            last_email_days=last_email,
            last_meeting_days=last_meeting,
            last_activity_days=last_activity,
            relationship_health=health.get("relationship_health", 0.0),
        )

        return CompanyEngagementDTO(
            company_id=company_id,
            email_count=score.email_count_sent + score.email_count_received,
            meeting_count=score.meeting_count,
            last_activity=(
                (datetime.now(timezone.utc) - timedelta(days=last_activity)).isoformat()
                if last_activity is not None
                else None
            ),
            last_email=(
                (datetime.now(timezone.utc) - timedelta(days=last_email)).isoformat()
                if last_email is not None
                else None
            ),
            last_meeting=(
                (datetime.now(timezone.utc) - timedelta(days=last_meeting)).isoformat()
                if last_meeting is not None
                else None
            ),
            followup_status=followup.priority if isinstance(followup, FollowUpStatus) else "",
            score=score,
        )

    async def get_email_metrics(self, tenant_id: str) -> dict:
        totals = await self.email_reader.tenant_totals(tenant_id)
        return {"status": "ok", **totals}

    async def get_calendar_metrics(self, tenant_id: str) -> dict:
        totals = await self.meeting_reader.tenant_totals(tenant_id)
        return {"status": "ok", **totals}

    async def get_followups(self, tenant_id: str) -> dict:
        return {"status": "ok", "items": [], "tenant_id": tenant_id}

    async def get_engagement_summary(self, tenant_id: str) -> dict:
        email_totals = await self.email_reader.tenant_totals(tenant_id)
        meeting_totals = await self.meeting_reader.tenant_totals(tenant_id)
        return {
            "status": "ok",
            "email_count": email_totals["email_count"],
            "meeting_count": meeting_totals["meeting_count"],
        }
