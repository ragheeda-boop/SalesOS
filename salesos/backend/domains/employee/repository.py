from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from .models import EmployeeSignal, EmployeeScore


class EmployeeSignalRepository(ABC):
    @property
    def db(self):
        return None

    @abstractmethod
    async def save(self, signal: EmployeeSignal) -> EmployeeSignal:
        ...

    @abstractmethod
    async def save_many(self, signals: list[EmployeeSignal]) -> list[EmployeeSignal]:
        ...

    @abstractmethod
    async def get_by_employee(
        self, employee_id: str, tenant_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
        source: str | None = None,
        signal_type: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[EmployeeSignal], int, str | None]:
        ...

    @abstractmethod
    async def get_summary(
        self, employee_id: str, tenant_id: str,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    async def save_score(self, score: EmployeeScore) -> EmployeeScore:
        ...

    @abstractmethod
    async def get_latest_score(
        self, employee_id: str, tenant_id: str,
    ) -> EmployeeScore | None:
        ...

    @abstractmethod
    async def delete_by_employee(
        self, employee_id: str, tenant_id: str,
    ) -> int:
        ...
