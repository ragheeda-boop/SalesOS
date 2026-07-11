"""InMemoryMeetingRepository — for testing without a database."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from domains.commercial.meeting import Meeting
from domains.commercial.meeting.repository import MeetingRepository
from domains.commercial.infrastructure.models import MeetingModel


class InMemoryMeetingRepository(MeetingRepository):

    def __init__(self):
        self._meetings: dict[str, MeetingModel] = {}

    async def get(self, meeting_id: str) -> Optional[MeetingModel]:
        return self._meetings.get(meeting_id)

    async def list_by_opportunity(
        self, opportunity_id: str, tenant_id: str, limit: int = 50,
    ) -> list[MeetingModel]:
        items = [
            m for m in self._meetings.values()
            if m.opportunity_id == opportunity_id and m.tenant_id == tenant_id
        ]
        items.sort(key=lambda m: m.meeting_date or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return items[:limit]

    async def save(self, meeting: MeetingModel) -> MeetingModel:
        self._meetings[meeting.id] = meeting
        return meeting

    async def delete(self, meeting_id: str) -> bool:
        if meeting_id in self._meetings:
            del self._meetings[meeting_id]
            return True
        return False

    async def get_domain(self, meeting_id: str) -> Optional[Meeting]:
        model = await self.get(meeting_id)
        if not model:
            return None
        return Meeting(
            id=model.id,
            tenant_id=model.tenant_id,
            opportunity_id=model.opportunity_id,
            title=model.title,
            date=model.meeting_date,
            duration_minutes=model.duration_minutes or 60,
            notes=model.notes,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def list_domain_by_opportunity(
        self, opportunity_id: str, tenant_id: str, limit: int = 50,
    ) -> list[Meeting]:
        models = await self.list_by_opportunity(opportunity_id, tenant_id, limit)
        return [
            Meeting(
                id=m.id, tenant_id=m.tenant_id, opportunity_id=m.opportunity_id,
                title=m.title, date=m.meeting_date,
                duration_minutes=m.duration_minutes or 60,
                notes=m.notes, status=m.status,
                created_at=m.created_at, updated_at=m.updated_at,
            )
            for m in models
        ]
