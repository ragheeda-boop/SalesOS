"""MeetingRepository — abstract persistence interface for Meeting domain."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from domains.commercial.meeting import Meeting
from domains.commercial.infrastructure.models import MeetingModel


class MeetingRepository(ABC):

    @abstractmethod
    async def get(self, meeting_id: str) -> Optional[MeetingModel]: ...

    @abstractmethod
    async def list_by_opportunity(
        self, opportunity_id: str, tenant_id: str, limit: int = 50,
    ) -> list[MeetingModel]: ...

    @abstractmethod
    async def save(self, meeting: MeetingModel) -> MeetingModel: ...

    @abstractmethod
    async def delete(self, meeting_id: str) -> bool: ...

    @abstractmethod
    async def get_domain(self, meeting_id: str) -> Optional[Meeting]: ...

    @abstractmethod
    async def list_domain_by_opportunity(
        self, opportunity_id: str, tenant_id: str, limit: int = 50,
    ) -> list[Meeting]: ...
