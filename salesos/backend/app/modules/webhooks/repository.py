from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import Boolean, DateTime, Integer, String, Text, select, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from sdk.database import Base

from .models import WebhookDelivery, WebhookSubscription


class WebhookSubscriptionRepository(Protocol):
    async def create(self, sub: WebhookSubscription) -> WebhookSubscription: ...
    async def get(self, sub_id: str, tenant_id: str = "") -> WebhookSubscription | None: ...
    async def list_by_tenant(self, tenant_id: str) -> list[WebhookSubscription]: ...
    async def find_by_event(self, tenant_id: str, event_type: str) -> list[WebhookSubscription]: ...
    async def update(self, sub_id: str, data: dict, tenant_id: str = "") -> WebhookSubscription | None: ...
    async def delete(self, sub_id: str, tenant_id: str = "") -> bool: ...


class WebhookDeliveryRepository(Protocol):
    async def create(self, delivery: WebhookDelivery) -> WebhookDelivery: ...
    async def get(self, delivery_id: str) -> WebhookDelivery | None: ...
    async def list_by_subscription(self, subscription_id: str, limit: int = 50) -> list[WebhookDelivery]: ...
    async def update(self, delivery_id: str, data: dict) -> WebhookDelivery | None: ...
    async def list_pending_retries(self) -> list[WebhookDelivery]: ...


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

    async def get(self, sub_id: str, tenant_id: str = "") -> WebhookSubscription | None:
        sub = self._subscriptions.get(sub_id)
        if sub and tenant_id and sub.tenant_id != tenant_id:
            return None
        return sub

    async def list_by_tenant(self, tenant_id: str) -> list[WebhookSubscription]:
        return [s for s in self._subscriptions.values() if s.tenant_id == tenant_id]

    async def find_by_event(self, tenant_id: str, event_type: str) -> list[WebhookSubscription]:
        return [
            s for s in self._subscriptions.values()
            if s.tenant_id == tenant_id and s.is_active and event_type in s.events
        ]

    async def update(self, sub_id: str, data: dict, tenant_id: str = "") -> WebhookSubscription | None:
        sub = self._subscriptions.get(sub_id)
        if not sub:
            return None
        if tenant_id and sub.tenant_id != tenant_id:
            return None
        for key, value in data.items():
            if hasattr(sub, key) and value is not None:
                setattr(sub, key, value)
        sub.updated_at = datetime.now(timezone.utc)
        return sub

    async def delete(self, sub_id: str, tenant_id: str = "") -> bool:
        sub = self._subscriptions.get(sub_id)
        if sub and tenant_id and sub.tenant_id != tenant_id:
            return False
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


class WebhookSubscriptionModel(Base):
    __tablename__ = "webhook_subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    secret: Mapped[str] = mapped_column(Text, nullable=False)
    events: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class WebhookDeliveryModel(Base):
    __tablename__ = "webhook_deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    subscription_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pending'"))
    response_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


def _sub_from_row(row: WebhookSubscriptionModel) -> WebhookSubscription:
    return WebhookSubscription(
        id=row.id,
        tenant_id=row.tenant_id,
        url=row.url,
        secret=row.secret,
        events=list(row.events or []),
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _delivery_from_row(row: WebhookDeliveryModel) -> WebhookDelivery:
    return WebhookDelivery(
        id=row.id,
        subscription_id=row.subscription_id,
        event_type=row.event_type,
        payload=dict(row.payload or {}),
        status=row.status,
        response_code=row.response_code,
        response_body=row.response_body,
        attempt=row.attempt,
        next_retry_at=row.next_retry_at,
        created_at=row.created_at,
    )


class PostgresWebhookSubscriptionRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, sub: WebhookSubscription) -> WebhookSubscription:
        now = datetime.now(timezone.utc)
        row = WebhookSubscriptionModel(
            id=sub.id or str(uuid.uuid4()),
            tenant_id=sub.tenant_id,
            url=sub.url,
            secret=sub.secret,
            events=sub.events,
            is_active=sub.is_active,
            created_at=sub.created_at or now,
            updated_at=sub.updated_at or now,
        )
        self._session.add(row)
        await self._session.flush()
        return _sub_from_row(row)

    async def get(self, sub_id: str, tenant_id: str = "") -> WebhookSubscription | None:
        q = select(WebhookSubscriptionModel).where(WebhookSubscriptionModel.id == sub_id)
        if tenant_id:
            q = q.where(WebhookSubscriptionModel.tenant_id == tenant_id)
        result = await self._session.execute(q)
        row = result.scalar_one_or_none()
        return _sub_from_row(row) if row else None

    async def list_by_tenant(self, tenant_id: str) -> list[WebhookSubscription]:
        result = await self._session.execute(
            select(WebhookSubscriptionModel)
            .where(WebhookSubscriptionModel.tenant_id == tenant_id)
            .order_by(WebhookSubscriptionModel.created_at.desc())
        )
        return [_sub_from_row(r) for r in result.scalars().all()]

    async def find_by_event(self, tenant_id: str, event_type: str) -> list[WebhookSubscription]:
        result = await self._session.execute(
            select(WebhookSubscriptionModel).where(
                WebhookSubscriptionModel.tenant_id == tenant_id,
                WebhookSubscriptionModel.is_active.is_(True),
                WebhookSubscriptionModel.events.contains([event_type]),
            )
        )
        return [_sub_from_row(r) for r in result.scalars().all()]

    async def update(self, sub_id: str, data: dict, tenant_id: str = "") -> WebhookSubscription | None:
        q = select(WebhookSubscriptionModel).where(WebhookSubscriptionModel.id == sub_id)
        if tenant_id:
            q = q.where(WebhookSubscriptionModel.tenant_id == tenant_id)
        result = await self._session.execute(q)
        row = result.scalar_one_or_none()
        if not row:
            return None
        for key in ("url", "secret", "events", "is_active"):
            if key in data and data[key] is not None:
                setattr(row, key, data[key])
        row.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return _sub_from_row(row)

    async def delete(self, sub_id: str, tenant_id: str = "") -> bool:
        q = select(WebhookSubscriptionModel).where(WebhookSubscriptionModel.id == sub_id)
        if tenant_id:
            q = q.where(WebhookSubscriptionModel.tenant_id == tenant_id)
        result = await self._session.execute(q)
        row = result.scalar_one_or_none()
        if not row:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True


class PostgresWebhookDeliveryRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, delivery: WebhookDelivery) -> WebhookDelivery:
        row = WebhookDeliveryModel(
            id=delivery.id or str(uuid.uuid4()),
            subscription_id=delivery.subscription_id,
            event_type=delivery.event_type,
            payload=delivery.payload,
            status=delivery.status,
            response_code=delivery.response_code,
            response_body=delivery.response_body,
            attempt=delivery.attempt,
            next_retry_at=delivery.next_retry_at,
            created_at=delivery.created_at or datetime.now(timezone.utc),
        )
        self._session.add(row)
        await self._session.flush()
        return _delivery_from_row(row)

    async def get(self, delivery_id: str) -> WebhookDelivery | None:
        row = await self._session.get(WebhookDeliveryModel, delivery_id)
        return _delivery_from_row(row) if row else None

    async def list_by_subscription(self, subscription_id: str, limit: int = 50) -> list[WebhookDelivery]:
        result = await self._session.execute(
            select(WebhookDeliveryModel)
            .where(WebhookDeliveryModel.subscription_id == subscription_id)
            .order_by(WebhookDeliveryModel.created_at.desc())
            .limit(limit)
        )
        return [_delivery_from_row(r) for r in result.scalars().all()]

    async def update(self, delivery_id: str, data: dict) -> WebhookDelivery | None:
        row = await self._session.get(WebhookDeliveryModel, delivery_id)
        if not row:
            return None
        for key in ("status", "response_code", "response_body", "attempt", "next_retry_at", "payload"):
            if key in data and data[key] is not None:
                setattr(row, key, data[key])
        await self._session.flush()
        return _delivery_from_row(row)

    async def list_pending_retries(self) -> list[WebhookDelivery]:
        now = datetime.now(timezone.utc)
        result = await self._session.execute(
            select(WebhookDeliveryModel).where(
                WebhookDeliveryModel.status == "failed",
                WebhookDeliveryModel.next_retry_at.is_not(None),
                WebhookDeliveryModel.next_retry_at <= now,
                WebhookDeliveryModel.attempt < 3,
            )
        )
        return [_delivery_from_row(r) for r in result.scalars().all()]
