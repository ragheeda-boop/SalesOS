"""Productivity Intelligence — advanced KPIs for Employee 360.

Tracks: focus score, burnout detection, task completion rate, workload balance,
meeting load, communication balance, activity trends, benchmarks.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .db_models import EmployeeSignalModel, EmployeeScoreModel
from .intelligence_models import EmployeeCalendarEventModel, EmployeeEmailEventModel


class ProductivityService:
    """Computes advanced productivity KPIs from signals, calendar, and email data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute(self, employee_id: str, tenant_id: str, period_days: int = 30) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=period_days)
        eid = uuid.UUID(employee_id)
        tid = uuid.UUID(tenant_id)

        # Signal activity
        signal_count = (await self.db.execute(
            select(func.count()).select_from(EmployeeSignalModel).where(
                EmployeeSignalModel.employee_id == eid,
                EmployeeSignalModel.tenant_id == tid,
                EmployeeSignalModel.timestamp >= since,
            )
        )).scalar() or 0

        # Task completion rate
        task_total = (await self.db.execute(
            select(func.count()).select_from(EmployeeSignalModel).where(
                EmployeeSignalModel.employee_id == eid,
                EmployeeSignalModel.tenant_id == tid,
                EmployeeSignalModel.timestamp >= since,
                EmployeeSignalModel.signal_type.in_(["task_created", "task_completed"]),
            )
        )).scalar() or 0

        task_completed = (await self.db.execute(
            select(func.count()).select_from(EmployeeSignalModel).where(
                EmployeeSignalModel.employee_id == eid,
                EmployeeSignalModel.tenant_id == tid,
                EmployeeSignalModel.timestamp >= since,
                EmployeeSignalModel.signal_type == "task_completed",
            )
        )).scalar() or 0

        task_completion_rate = round(task_completed / max(1, task_total) * 100, 1)

        # Calendar load
        meeting_count = (await self.db.execute(
            select(func.count()).select_from(EmployeeCalendarEventModel).where(
                EmployeeCalendarEventModel.employee_id == eid,
                EmployeeCalendarEventModel.tenant_id == tid,
                EmployeeCalendarEventModel.is_cancelled == False,
                EmployeeCalendarEventModel.start_utc >= since,
            )
        )).scalar() or 0

        meeting_hours = (await self.db.execute(
            select(func.sum(EmployeeCalendarEventModel.duration_minutes)).where(
                EmployeeCalendarEventModel.employee_id == eid,
                EmployeeCalendarEventModel.tenant_id == tid,
                EmployeeCalendarEventModel.is_cancelled == False,
                EmployeeCalendarEventModel.start_utc >= since,
            )
        )).scalar() or 0
        total_meeting_hours = round((meeting_hours or 0) / 60.0, 1)

        # Email load
        email_count = (await self.db.execute(
            select(func.count()).select_from(EmployeeEmailEventModel).where(
                EmployeeEmailEventModel.employee_id == eid,
                EmployeeEmailEventModel.tenant_id == tid,
                EmployeeEmailEventModel.timestamp_utc >= since,
            )
        )).scalar() or 0

        # Workload score (0-100, normalized against benchmarks)
        signals_per_day = signal_count / max(1, period_days)
        meetings_per_day = meeting_count / max(1, period_days)
        emails_per_day = email_count / max(1, period_days)

        # Normalize: 5 signals/day → 100, 3 meetings/day → ideal, 30 emails/day → high
        activity_score = min(100, round(signals_per_day / 5 * 100, 1))
        meeting_score = max(0, min(100, round((1 - abs(meetings_per_day - 3) / 3) * 100, 1)))
        email_score = max(0, min(100, round((1 - abs(emails_per_day - 20) / 20) * 100, 1)))

        # Focus score: inverse of meeting load
        work_days = min(period_days, 22)
        focus_time = max(0, work_days * 8 - total_meeting_hours)
        focus_score = min(100, round(focus_time / (work_days * 4) * 100, 1))

        # Composite productivity
        productivity = round(activity_score * 0.30 + focus_score * 0.25 + meeting_score * 0.20 + email_score * 0.15 + task_completion_rate * 0.10, 1)

        # Burnout indicator
        burnout_risk = "low"
        if meetings_per_day > 5 or emails_per_day > 50:
            burnout_risk = "high"
        elif meetings_per_day > 3 or emails_per_day > 35:
            burnout_risk = "medium"

        # Trend: compare first half vs second half of period
        mid = since + timedelta(days=period_days / 2)
        first_half = (await self.db.execute(
            select(func.count()).select_from(EmployeeSignalModel).where(
                EmployeeSignalModel.employee_id == eid,
                EmployeeSignalModel.tenant_id == tid,
                EmployeeSignalModel.timestamp >= since,
                EmployeeSignalModel.timestamp < mid,
            )
        )).scalar() or 0

        second_half = (await self.db.execute(
            select(func.count()).select_from(EmployeeSignalModel).where(
                EmployeeSignalModel.employee_id == eid,
                EmployeeSignalModel.tenant_id == tid,
                EmployeeSignalModel.timestamp >= mid,
            )
        )).scalar() or 0

        trend_direction = "stable"
        if first_half > 0 and second_half > 0:
            change = (second_half - first_half) / first_half
            if change > 0.15:
                trend_direction = "improving"
            elif change < -0.15:
                trend_direction = "declining"

        return {
            "productivity_score": productivity,
            "activity_score": activity_score,
            "focus_score": focus_score,
            "task_completion_rate": task_completion_rate,
            "meetings_per_day": round(meetings_per_day, 1),
            "emails_per_day": round(emails_per_day, 1),
            "meeting_hours_total": total_meeting_hours,
            "signal_count": signal_count,
            "burnout_risk": burnout_risk,
            "trend_direction": trend_direction,
            "first_half_signals": first_half,
            "second_half_signals": second_half,
            "period_days": period_days,
        }


class RelationshipService:
    """Relationship Intelligence — engagement scoring and stakeholder mapping."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_relationship_score(self, employee_id: str, tenant_id: str, target_id: str, target_type: str) -> dict[str, Any]:
        """Compute engagement score between employee and a company/contact/opportunity."""
        now = datetime.now(timezone.utc)
        since_90d = now - timedelta(days=90)
        eid = uuid.UUID(employee_id)
        tid = uuid.UUID(tenant_id)

        # Count meetings with this target
        meeting_count = (await self.db.execute(
            select(func.count()).select_from(EmployeeCalendarEventModel).where(
                EmployeeCalendarEventModel.employee_id == eid,
                EmployeeCalendarEventModel.tenant_id == tid,
                EmployeeCalendarEventModel.is_cancelled == False,
                EmployeeCalendarEventModel.start_utc >= since_90d,
                EmployeeCalendarEventModel.related_company_ids.contains([target_id]) if hasattr(EmployeeCalendarEventModel.related_company_ids, "contains") else True,
            )
        )).scalar() or 0

        # Count emails with this target
        email_count = (await self.db.execute(
            select(func.count()).select_from(EmployeeEmailEventModel).where(
                EmployeeEmailEventModel.employee_id == eid,
                EmployeeEmailEventModel.tenant_id == tid,
                EmployeeEmailEventModel.timestamp_utc >= since_90d,
            )
        )).scalar() or 0

        # Recency bonus: more recent = higher score
        latest_meeting = (await self.db.execute(
            select(EmployeeCalendarEventModel.start_utc).where(
                EmployeeCalendarEventModel.employee_id == eid,
                EmployeeCalendarEventModel.tenant_id == tid,
                EmployeeCalendarEventModel.is_cancelled == False,
            ).order_by(EmployeeCalendarEventModel.start_utc.desc()).limit(1)
        )).scalar()

        recency_days = (now - latest_meeting).days if latest_meeting else 90
        recency_score = max(0, min(100, (1 - recency_days / 90) * 100))

        # Composite relationship score
        engagement = min(100, meeting_count * 10 + email_count * 1)
        score = round(engagement * 0.6 + recency_score * 0.4, 1)

        strength = "strong" if score >= 70 else "moderate" if score >= 40 else "weak"

        return {
            "employee_id": employee_id,
            "target_id": target_id,
            "target_type": target_type,
            "relationship_score": score,
            "strength": strength,
            "meetings_last_90d": meeting_count,
            "emails_last_90d": email_count,
            "days_since_last_contact": recency_days,
        }
