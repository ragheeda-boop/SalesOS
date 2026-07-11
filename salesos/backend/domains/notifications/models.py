from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Notification:
    id: str
    tenant_id: str
    user_id: str
    type: str  # workflow | nba | report | alert
    title: str
    body: str
    data: dict[str, Any] = field(default_factory=dict)
    read: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class NotificationRepository:
    async def create(self, notification: Notification) -> Notification:
        raise NotImplementedError

    async def get(self, notification_id: str, tenant_id: str) -> Notification | None:
        raise NotImplementedError

    async def list_by_user(self, tenant_id: str, user_id: str, limit: int = 50) -> list[Notification]:
        raise NotImplementedError

    async def mark_read(self, notification_id: str, tenant_id: str, user_id: str) -> bool:
        raise NotImplementedError

    async def mark_all_read(self, tenant_id: str, user_id: str) -> int:
        raise NotImplementedError

    async def count_unread(self, tenant_id: str, user_id: str) -> int:
        raise NotImplementedError


class InMemoryNotificationRepository(NotificationRepository):
    def __init__(self) -> None:
        self._store: dict[str, Notification] = {}

    async def create(self, notification: Notification) -> Notification:
        self._store[notification.id] = notification
        return notification

    async def get(self, notification_id: str, tenant_id: str) -> Notification | None:
        n = self._store.get(notification_id)
        if n and n.tenant_id == tenant_id:
            return n
        return None

    async def list_by_user(self, tenant_id: str, user_id: str, limit: int = 50) -> list[Notification]:
        result = [
            n for n in self._store.values()
            if n.tenant_id == tenant_id and n.user_id == user_id
        ]
        result.sort(key=lambda n: n.created_at, reverse=True)
        return result[:limit]

    async def mark_read(self, notification_id: str, tenant_id: str, user_id: str) -> bool:
        n = self._store.get(notification_id)
        if n and n.tenant_id == tenant_id and n.user_id == user_id:
            n.read = True
            return True
        return False

    async def mark_all_read(self, tenant_id: str, user_id: str) -> int:
        count = 0
        for n in self._store.values():
            if n.tenant_id == tenant_id and n.user_id == user_id and not n.read:
                n.read = True
                count += 1
        return count

    async def count_unread(self, tenant_id: str, user_id: str) -> int:
        return sum(
            1 for n in self._store.values()
            if n.tenant_id == tenant_id and n.user_id == user_id and not n.read
        )
