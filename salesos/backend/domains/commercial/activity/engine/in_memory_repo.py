"""In-memory Activity repository for testing and development."""

from __future__ import annotations

from datetime import datetime

from ..contracts.models import Activity, ActivitySession, ActivityStatus, ActivityType
from ..contracts.repository import ActivityRepository, ActivitySessionQuery


class InMemoryActivityRepository(ActivityRepository):

    def __init__(self):
        self._sessions: dict[str, ActivitySession] = {}

    async def save_session(self, session: ActivitySession) -> ActivitySession:
        self._sessions[session.id] = session
        return session

    async def get_session(self, session_id: str) -> ActivitySession | None:
        return self._sessions.get(session_id)

    async def query_sessions(self, query: ActivitySessionQuery) -> list[ActivitySession]:
        items = list(self._sessions.values())
        if query.tenant_id:
            items = [s for s in items if s.tenant_id == query.tenant_id]
        if query.target_id:
            items = [s for s in items if s.target_id == query.target_id]
        if query.target_type:
            items = [s for s in items if s.target_type == query.target_type]
        if query.status:
            items = [s for s in items if s.status.value == query.status]
        items.sort(key=lambda s: s.created_at, reverse=True)
        return items

    async def count_sessions(self, query: ActivitySessionQuery) -> int:
        return len(await self.query_sessions(query))

    async def get_activities_by_target(self, target_id: str, target_type: str, limit: int = 50) -> list[Activity]:
        result: list[Activity] = []
        for session in self._sessions.values():
            if session.target_id == target_id and session.target_type == target_type:
                result.extend(session.activities)
        result.sort(key=lambda a: a.completed_at or a.scheduled_at or datetime.min, reverse=True)
        return result[:limit]

    async def kpi_summary(self, tenant_id: str) -> dict[str, int | float]:
        sessions = [s for s in self._sessions.values() if s.tenant_id == tenant_id]
        completed_count = sum(1 for s in sessions if s.status == ActivityStatus.COMPLETED)
        total_activities = sum(len(s.activities) for s in sessions)
        completed_activities = sum(
            1 for s in sessions for a in s.activities if a.is_completed
        )
        call_count = sum(
            1 for s in sessions for a in s.activities if a.activity_type == ActivityType.CALL
        )
        meeting_count = sum(
            1 for s in sessions for a in s.activities if a.activity_type == ActivityType.MEETING
        )

        unique_owners = set()
        for s in sessions:
            for a in s.activities:
                if a.owner_id:
                    unique_owners.add(a.owner_id)
        owner_count = max(len(unique_owners), 1)

        return {
            "total_sessions": len(sessions),
            "completed_sessions": completed_count,
            "total_activities": total_activities,
            "completed_activities": completed_activities,
            "activities_per_rep": round(total_activities / owner_count, 1),
            "calls_total": call_count,
            "meetings_total": meeting_count,
            "completion_rate": round(completed_activities / total_activities, 2) if total_activities > 0 else 0.0,
        }
