"""Reader interfaces for consumed domains (ADR-012 §2).

Activity Intelligence reads from existing domains through these interfaces.
Does NOT replace existing domains — consumes them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class EmailReader(ABC):
    """Read-only access to email domain data."""

    @abstractmethod
    async def get(self, email_id: str) -> Optional[dict]: ...

    @abstractmethod
    async def list_by_company(
        self, company_id: str, tenant_id: str, limit: int = 50
    ) -> list[dict]: ...

    @abstractmethod
    async def count_by_company(
        self, company_id: str, tenant_id: str, direction: str | None = None
    ) -> int: ...

    @abstractmethod
    async def last_email(
        self, company_id: str, tenant_id: str
    ) -> Optional[dict]: ...


class MeetingReader(ABC):
    """Read-only access to meeting domain data."""

    @abstractmethod
    async def get(self, meeting_id: str) -> Optional[dict]: ...

    @abstractmethod
    async def list_by_company(
        self, company_id: str, tenant_id: str, limit: int = 50
    ) -> list[dict]: ...

    @abstractmethod
    async def count_by_company(
        self, company_id: str, tenant_id: str
    ) -> int: ...

    @abstractmethod
    async def last_meeting(
        self, company_id: str, tenant_id: str
    ) -> Optional[dict]: ...


class ActivityReader(ABC):
    """Read-only access to Activity Runtime spine."""

    @abstractmethod
    async def list_by_entity(
        self, entity_type: str, entity_id: str, tenant_id: str, limit: int = 50
    ) -> list[dict]: ...

    @abstractmethod
    async def count_since(
        self, entity_type: str, entity_id: str, tenant_id: str, since: str
    ) -> int: ...


class CompanyReader(ABC):
    """Read-only access to company domain data."""

    @abstractmethod
    async def get(self, company_id: str, tenant_id: str) -> Optional[dict]: ...

    @abstractmethod
    async def search_by_domain(
        self, domain: str, tenant_id: str
    ) -> list[dict]: ...

    @abstractmethod
    async def search_by_name(
        self, name: str, tenant_id: str, limit: int = 10
    ) -> list[dict]: ...


class ContactReader(ABC):
    """Read-only access to contact domain data."""

    @abstractmethod
    async def get(self, contact_id: str, tenant_id: str) -> Optional[dict]: ...

    @abstractmethod
    async def search_by_email(
        self, email: str, tenant_id: str
    ) -> list[dict]: ...
