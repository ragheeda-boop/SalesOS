"""EmailRepository — abstract persistence interface for Email domain."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from domains.commercial.email import Email
from domains.commercial.infrastructure.models import EmailModel


class EmailRepository(ABC):

    @abstractmethod
    async def get(self, email_id: str) -> Optional[EmailModel]: ...

    @abstractmethod
    async def list_by_opportunity(
        self, opportunity_id: str, tenant_id: str, limit: int = 20,
    ) -> list[EmailModel]: ...

    @abstractmethod
    async def save(self, email: EmailModel) -> EmailModel: ...

    @abstractmethod
    async def delete(self, email_id: str) -> bool: ...
