"""Calendar Engine — calendar intelligence and metrics (ADR-012 §3).

Provides:
- Meeting frequency analysis
- Scheduling pattern detection
- Duration tracking
"""

from __future__ import annotations

from datetime import datetime, timezone


class CalendarEngine:
    """Computes calendar intelligence from the meeting domain."""

    def __init__(self, meeting_reader=None):
        self._reader = meeting_reader

    async def get_count(
        self, company_id: str, tenant_id: str
    ) -> int:
        """Get meeting count for a company."""
        if self._reader:
            return await self._reader.count_by_company(company_id, tenant_id)
        return 0

    async def get_last_meeting(
        self, company_id: str, tenant_id: str
    ) -> dict | None:
        """Get the most recent meeting for a company."""
        if self._reader:
            return await self._reader.last_meeting(company_id, tenant_id)
        return None

    async def get_meeting_hours(
        self, company_id: str, tenant_id: str
    ) -> float:
        """Get total meeting hours for a company."""
        if not self._reader:
            return 0.0

        meetings = await self._reader.list_by_company(company_id, tenant_id, limit=200)
        total_minutes = sum(
            m.get("duration_minutes", 0) for m in meetings
        )
        return round(total_minutes / 60, 1)

    async def get_meeting_metrics(
        self, company_id: str, tenant_id: str
    ) -> dict:
        """Get comprehensive meeting metrics for a company."""
        count = await self.get_count(company_id, tenant_id)
        hours = await self.get_meeting_hours(company_id, tenant_id)
        last = await self.get_last_meeting(company_id, tenant_id)

        last_days = None
        if last and last.get("date"):
            last_date = last["date"]
            if isinstance(last_date, str):
                last_date = datetime.fromisoformat(last_date.replace("Z", "+00:00"))
            last_days = (datetime.now(timezone.utc) - last_date).days

        # Meeting completion rate: completed / total
        completion_rate = 0.0
        if self._reader:
            meetings = await self._reader.list_by_company(company_id, tenant_id, limit=200)
            if meetings:
                completed = sum(1 for m in meetings if m.get("status") == "completed")
                completion_rate = round(completed / len(meetings), 4)

        return {
            "company_id": company_id,
            "meeting_count": count,
            "meeting_hours": hours,
            "meeting_completion_rate": completion_rate,
            "last_meeting_days": last_days,
        }
