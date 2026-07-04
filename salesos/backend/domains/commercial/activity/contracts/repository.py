"""ActivityRepository — persistence for activity sessions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .models import Activity, ActivitySession


@dataclass
class ActivitySessionQuery:
    tenant_id: str = ""
    target_id: str = ""
    target_type: str = ""
    owner_id: str = ""
    status: str = ""
    from_date: datetime | None = None
    to_date: datetime | None = None
    page: int = 1
    page_size: int = 20


class ActivityRepository(ABC):

    @abstractmethod
    async def save_session(self, session: ActivitySession) -> ActivitySession: ...

    @abstractmethod
    async def get_session(self, session_id: str) -> ActivitySession | None: ...

    @abstractmethod
    async def query_sessions(self, query: ActivitySessionQuery) -> list[ActivitySession]: ...

    @abstractmethod
    async def count_sessions(self, query: ActivitySessionQuery) -> int: ...

    @abstractmethod
    async def get_activities_by_target(self, target_id: str, target_type: str, limit: int = 50) -> list[Activity]: ...

    @abstractmethod
    async def kpi_summary(self, tenant_id: str) -> dict[str, Any]: ...
