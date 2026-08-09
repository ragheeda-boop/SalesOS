"""OpportunityContact contract — domain model and repository interface for opportunity↔contact relationships."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class OpportunityContact:
    """Domain model for an opportunity-to-contact association."""

    id: UUID
    tenant_id: UUID
    opportunity_id: str
    contact_id: UUID
    role: str | None = None
    is_primary: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class OpportunityContactQuery:
    """Structured query for filtering opportunity-contact associations."""

    tenant_id: str = ""
    opportunity_id: str = ""
    contact_id: str = ""
    page: int = 1
    page_size: int = 20


@dataclass
class OpportunityContactResult:
    items: list[OpportunityContact] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class OpportunityContactRepository(ABC):

    @abstractmethod
    async def create(self, oc: OpportunityContact) -> OpportunityContact: ...

    @abstractmethod
    async def get(self, oc_id: UUID) -> OpportunityContact | None: ...

    @abstractmethod
    async def get_by_opportunity(
        self, opportunity_id: str, tenant_id: str,
    ) -> list[OpportunityContact]: ...

    @abstractmethod
    async def get_by_contact(
        self, contact_id: UUID, tenant_id: str,
    ) -> list[OpportunityContact]: ...

    @abstractmethod
    async def query(self, query: OpportunityContactQuery) -> OpportunityContactResult: ...

    @abstractmethod
    async def delete(self, oc_id: UUID) -> bool: ...

    @abstractmethod
    async def delete_by_opportunity(self, opportunity_id: str) -> int: ...
