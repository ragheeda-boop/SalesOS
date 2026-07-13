from __future__ import annotations

import uuid
from datetime import datetime, timezone

from .models import WebhookDelivery, WebhookSubscription


class InMemoryWebhookSubscriptionRepository:
    def __init__(self):
        self._subscriptions: dict[str, WebhookSubscription] = {}

    async def create(self, sub: WebhookSubscription) -> WebhookSubscription:
        now = datetime.now(timezone.utc)
        if sub.created_at is None:
            sub.created_at = now
        if sub.updated_at is None:
            sub.updated_at = now
        self._subscriptions[sub.id] = sub
        return sub

    async def get(self, sub_id: str) -> WebhookSubscription | None:
        return self._subscriptions.get(sub_id)

    async def list_by_tenant(self, tenant_id: str) -> list[WebhookSubscription]:
        return [s for s in self._subscriptions.values() if s.tenant_id == tenant_id]

    async def find_by_event(self, tenant_id: str, event_type: str) -> list[WebhookSubscription]:
        return [
            s for s in self._subscriptions.values()
            if s.tenant_id == tenant_id and s.is_active and event_type in s.events
        ]

    async def update(self, sub_id: str, data: dict) -> WebhookSubscription | None:
        sub = self._subscriptions.get(sub_id)
        if not sub:
            return None
        for key, value in data.items():
            if hasattr(sub, key) and value is not None:
                setattr(sub, key, value)
        sub.updated_at = datetime.now(timezone.utc)
        return sub

    async def delete(self, sub_id: str) -> bool:
        if sub_id in self._subscriptions:
            del self._subscriptions[sub_id]
            return True
        return False


class InMemoryWebhookDeliveryRepository:
    def __init__(self):
        self._deliveries: dict[str, WebhookDelivery] = {}

    async def create(self, delivery: WebhookDelivery) -> WebhookDelivery:
        self._deliveries[delivery.id] = delivery
        return delivery

    async def get(self, delivery_id: str) -> WebhookDelivery | None:
        return self._deliveries.get(delivery_id)

    async def list_by_subscription(self, subscription_id: str, limit: int = 50) -> list[WebhookDelivery]:
        result = [
            d for d in self._deliveries.values() if d.subscription_id == subscription_id
        ]
        result.sort(key=lambda d: d.created_at, reverse=True)
        return result[:limit]

    async def update(self, delivery_id: str, data: dict) -> WebhookDelivery | None:
        d = self._deliveries.get(delivery_id)
        if not d:
            return None
        for key, value in data.items():
            if hasattr(d, key) and value is not None:
                setattr(d, key, value)
        return d

    async def list_pending_retries(self) -> list[WebhookDelivery]:
        now = datetime.now(timezone.utc)
        return [
            d for d in self._deliveries.values()
            if d.status == "failed"
            and d.next_retry_at is not None
            and d.next_retry_at <= now
            and d.attempt < 3
        ]
