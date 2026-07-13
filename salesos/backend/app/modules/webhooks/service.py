from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta, timezone

import httpx

from .models import WebhookDelivery, WebhookSubscription
from .repository import (
    InMemoryWebhookDeliveryRepository,
    InMemoryWebhookSubscriptionRepository,
)

RETRY_DELAYS = [10, 60, 300]  # seconds: attempt 0→10s, 1→60s, 2→300s


def _sign_payload(payload: dict, secret: str) -> str:
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hmac.new(
        secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


class WebhookService:
    def __init__(
        self,
        subscription_repo: InMemoryWebhookSubscriptionRepository | None = None,
        delivery_repo: InMemoryWebhookDeliveryRepository | None = None,
    ):
        self.subscription_repo = subscription_repo or InMemoryWebhookSubscriptionRepository()
        self.delivery_repo = delivery_repo or InMemoryWebhookDeliveryRepository()

    async def create_subscription(
        self, tenant_id: str, url: str, events: list[str], secret: str
    ) -> WebhookSubscription:
        sub = WebhookSubscription(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            url=url,
            secret=secret,
            events=events,
        )
        return await self.subscription_repo.create(sub)

    async def update_subscription(
        self, sub_id: str, data: dict
    ) -> WebhookSubscription | None:
        return await self.subscription_repo.update(sub_id, data)

    async def delete_subscription(self, sub_id: str) -> bool:
        return await self.subscription_repo.delete(sub_id)

    async def get_subscription(self, sub_id: str) -> WebhookSubscription | None:
        return await self.subscription_repo.get(sub_id)

    async def list_subscriptions(self, tenant_id: str) -> list[WebhookSubscription]:
        return await self.subscription_repo.list_by_tenant(tenant_id)

    async def get_delivery_logs(
        self, sub_id: str, limit: int = 50
    ) -> list[WebhookDelivery]:
        return await self.delivery_repo.list_by_subscription(sub_id, limit=limit)

    async def dispatch_event(self, event_type: str, payload: dict, tenant_id: str) -> list[WebhookDelivery]:
        subscriptions = await self.subscription_repo.find_by_event(tenant_id, event_type)
        deliveries: list[WebhookDelivery] = []

        for sub in subscriptions:
            delivery = WebhookDelivery(
                id=str(uuid.uuid4()),
                subscription_id=sub.id,
                event_type=event_type,
                payload=payload,
                status="pending",
                attempt=0,
            )
            await self.delivery_repo.create(delivery)
            await self._attempt_delivery(delivery, sub)
            deliveries.append(delivery)

        return deliveries

    async def _attempt_delivery(self, delivery: WebhookDelivery, sub: WebhookSubscription) -> None:
        delivery.attempt += 1
        signature = _sign_payload(delivery.payload, sub.secret)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    sub.url,
                    json=delivery.payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Signature": signature,
                        "X-Webhook-Event": delivery.event_type,
                    },
                )
                delivery.status = "success" if resp.is_success else "failed"
                delivery.response_code = resp.status_code
                delivery.response_body = resp.text[:2000]
        except Exception as e:
            delivery.status = "failed"
            delivery.response_code = None
            delivery.response_body = str(e)[:2000]

        if delivery.status == "failed" and delivery.attempt < 3:
            delay = RETRY_DELAYS[delivery.attempt - 1] if delivery.attempt - 1 < len(RETRY_DELAYS) else 300
            delivery.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
        else:
            delivery.next_retry_at = None

        await self.delivery_repo.update(delivery.id, {
            "status": delivery.status,
            "response_code": delivery.response_code,
            "response_body": delivery.response_body,
            "attempt": delivery.attempt,
            "next_retry_at": delivery.next_retry_at,
        })

    async def retry_delivery(self, delivery_id: str) -> WebhookDelivery | None:
        delivery = await self.delivery_repo.get(delivery_id)
        if not delivery or delivery.status != "failed":
            return None

        sub = await self.subscription_repo.get(delivery.subscription_id)
        if not sub:
            return None

        delivery.status = "pending"
        await self._attempt_delivery(delivery, sub)
        return delivery

    async def process_retries(self) -> int:
        pending = await self.delivery_repo.list_pending_retries()
        count = 0
        for delivery in pending:
            sub = await self.subscription_repo.get(delivery.subscription_id)
            if sub:
                delivery.status = "pending"
                await self._attempt_delivery(delivery, sub)
                count += 1
        return count
