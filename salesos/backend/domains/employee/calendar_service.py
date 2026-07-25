"""Calendar Intelligence service — KPI computation from employee_calendar_events."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .intelligence_models import EmployeeCalendarEventModel


class CalendarIntelligenceService:
    """Computes calendar KPIs from synced employee calendar events."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_kpis(self, employee_id: str, tenant_id: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)
        eid = uuid.UUID(employee_id)
        tid = uuid.UUID(tenant_id)

        base = select(EmployeeCalendarEventModel).where(
            EmployeeCalendarEventModel.employee_id == eid,
            EmployeeCalendarEventModel.tenant_id == tid,
            EmployeeCalendarEventModel.is_cancelled == False,
        )

        today_events = (await self.db.execute(
            select(func.count()).select_from(EmployeeCalendarEventModel).where(
                EmployeeCalendarEventModel.employee_id == eid,
                EmployeeCalendarEventModel.tenant_id == tid,
                EmployeeCalendarEventModel.is_cancelled == False,
                EmployeeCalendarEventModel.start_utc >= today_start,
                EmployeeCalendarEventModel.start_utc < today_start + timedelta(days=1),
            )
        )).scalar() or 0

        week_events = (await self.db.execute(
            select(func.count()).select_from(EmployeeCalendarEventModel).where(
                EmployeeCalendarEventModel.employee_id == eid,
                EmployeeCalendarEventModel.tenant_id == tid,
                EmployeeCalendarEventModel.is_cancelled == False,
                EmployeeCalendarEventModel.start_utc >= week_start,
            )
        )).scalar() or 0

        month_events = (await self.db.execute(
            select(func.count()).select_from(EmployeeCalendarEventModel).where(
                EmployeeCalendarEventModel.employee_id == eid,
                EmployeeCalendarEventModel.tenant_id == tid,
                EmployeeCalendarEventModel.is_cancelled == False,
                EmployeeCalendarEventModel.start_utc >= month_start,
            )
        )).scalar() or 0

        total_hours_result = (await self.db.execute(
            select(func.sum(EmployeeCalendarEventModel.duration_minutes)).where(
                EmployeeCalendarEventModel.employee_id == eid,
                EmployeeCalendarEventModel.tenant_id == tid,
                EmployeeCalendarEventModel.is_cancelled == False,
                EmployeeCalendarEventModel.start_utc >= month_start,
            )
        )).scalar()
        total_hours = (total_hours_result or 0) / 60.0

        cancellation_result = (await self.db.execute(
            select(func.count()).select_from(EmployeeCalendarEventModel).where(
                EmployeeCalendarEventModel.employee_id == eid,
                EmployeeCalendarEventModel.tenant_id == tid,
                EmployeeCalendarEventModel.is_cancelled == True,
                EmployeeCalendarEventModel.start_utc >= month_start,
            )
        )).scalar() or 0

        internal_result = (await self.db.execute(
            select(func.count()).select_from(EmployeeCalendarEventModel).where(
                EmployeeCalendarEventModel.employee_id == eid,
                EmployeeCalendarEventModel.tenant_id == tid,
                EmployeeCalendarEventModel.is_cancelled == False,
                EmployeeCalendarEventModel.is_internal == True,
                EmployeeCalendarEventModel.start_utc >= month_start,
            )
        )).scalar() or 0

        external = max(0, month_events - internal_result)

        upcoming = (await self.db.execute(
            base.where(
                EmployeeCalendarEventModel.start_utc >= now,
            ).order_by(EmployeeCalendarEventModel.start_utc.asc()).limit(5)
        )).scalars().all()

        return {
            "today_count": today_events,
            "week_count": week_events,
            "month_count": month_events,
            "total_hours": round(total_hours, 1),
            "avg_duration_minutes": round(total_hours * 60 / max(1, month_events), 1),
            "cancelled_this_month": cancellation_result,
            "cancellation_rate": round(cancellation_result / max(1, month_events + cancellation_result) * 100, 1),
            "internal_count": internal_result,
            "external_count": external,
            "unique_companies_met": 0,  # requires attendee matching
            "focus_time_hours": round(max(0, 160 - total_hours), 1),  # 40h/wk × 4 = 160h
            "calendar_utilization": round(total_hours / 160 * 100, 1),
            "upcoming": [
                {
                    "id": str(e.id), "title": e.title,
                    "start": e.start_utc.isoformat() if e.start_utc else None,
                    "end": e.end_utc.isoformat() if e.end_utc else None,
                    "is_internal": e.is_internal,
                    "attendees_count": e.attendees_count,
                }
                for e in upcoming
            ],
        }

    async def get_heatmap(self, employee_id: str, tenant_id: str, days: int = 30) -> list[dict]:
        """Returns meeting distribution by hour-of-day × day-of-week."""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(EmployeeCalendarEventModel).where(
                EmployeeCalendarEventModel.employee_id == uuid.UUID(employee_id),
                EmployeeCalendarEventModel.tenant_id == uuid.UUID(tenant_id),
                EmployeeCalendarEventModel.is_cancelled == False,
                EmployeeCalendarEventModel.start_utc >= since,
            )
        )
        heatmap: dict[str, dict[str, int]] = {}
        for row in result.scalars().all():
            if row.start_utc:
                day_name = row.start_utc.strftime("%a")
                hour = row.start_utc.strftime("%H")
                heatmap.setdefault(day_name, {})
                heatmap[day_name][hour] = heatmap[day_name].get(hour, 0) + 1
        return [{"day": day, "hours": hours} for day, hours in heatmap.items()]
