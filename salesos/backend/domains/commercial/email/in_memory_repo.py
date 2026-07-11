"""InMemoryEmailRepository — for testing without a database."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from domains.commercial.email.repository import EmailRepository
from domains.commercial.infrastructure.models import EmailModel


class InMemoryEmailRepository(EmailRepository):

    def __init__(self):
        self._emails: dict[str, EmailModel] = {}

    async def get(self, email_id: str) -> Optional[EmailModel]:
        return self._emails.get(email_id)

    async def list_by_opportunity(
        self, opportunity_id: str, tenant_id: str, limit: int = 20,
    ) -> list[EmailModel]:
        items = [
            m for m in self._emails.values()
            if m.opportunity_id == opportunity_id and m.tenant_id == tenant_id
        ]
        items.sort(key=lambda m: m.sent_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return items[:limit]

    async def save(self, email: EmailModel) -> EmailModel:
        self._emails[email.id] = email
        return email

    async def delete(self, email_id: str) -> bool:
        if email_id in self._emails:
            del self._emails[email_id]
            return True
        return False
