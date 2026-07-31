from __future__ import annotations

import uuid

from .models import Signal, SignalEvent, SignalSubscription
from .repository import (
    InMemorySignalEventRepository,
    InMemorySignalRepository,
    InMemorySignalSubscriptionRepository,
)


class SignalMarketplaceService:
    def __init__(
        self,
        signal_repo: InMemorySignalRepository | None = None,
        sub_repo: InMemorySignalSubscriptionRepository | None = None,
        event_repo: InMemorySignalEventRepository | None = None,
    ):
        self.signal_repo = signal_repo or InMemorySignalRepository()
        self.sub_repo = sub_repo or InMemorySignalSubscriptionRepository()
        self.event_repo = event_repo or InMemorySignalEventRepository()

    # ── Signal Library ──

    async def list_signals(
        self, domain: str | None = None, pack_id: str | None = None
    ) -> list[Signal]:
        return await self.signal_repo.get_all(domain=domain, pack_id=pack_id)

    async def get_signal(self, signal_id: str) -> Signal | None:
        return await self.signal_repo.get_by_id(signal_id)

    async def register_signal(self, signal: Signal) -> Signal:
        existing = await self.signal_repo.get_by_id(signal.id)
        if existing is None:
            await self.signal_repo.upsert(signal)
        return signal

    async def register_signals_from_pack(self, signals: list[Signal]) -> list[Signal]:
        for s in signals:
            await self.register_signal(s)
        return signals

    # ── Subscription Management ──

    async def subscribe(
        self, signal_id: str, company_id: str, tenant_id: str, channel: str = "in-app"
    ) -> SignalSubscription:
        signal = await self.signal_repo.get_by_id(signal_id)
        if signal is None:
            raise ValueError(f"Signal {signal_id} not found")

        existing = await self.sub_repo.list_by_signal_and_company(signal_id, company_id)
        for sub in existing:
            if sub.tenant_id == tenant_id and sub.active:
                return sub

        sub = SignalSubscription(
            id=str(uuid.uuid4()),
            signal_id=signal_id,
            company_id=company_id,
            tenant_id=tenant_id,
            channel=channel,
            active=True,
        )
        return await self.sub_repo.create(sub)

    async def unsubscribe(self, sub_id: str, tenant_id: str) -> bool:
        sub = await self.sub_repo.get(sub_id)
        if sub is None or sub.tenant_id != tenant_id:
            return False
        return await self.sub_repo.delete(sub_id)

    async def list_subscriptions(self, tenant_id: str) -> list[SignalSubscription]:
        return await self.sub_repo.list_by_tenant(tenant_id)

    # ── Signal Feed ──

    async def get_feed(
        self, tenant_id: str, limit: int = 50, acknowledged: bool | None = None
    ) -> list[SignalEvent]:
        return await self.event_repo.list_by_tenant(
            tenant_id, limit=limit, acknowledged=acknowledged
        )

    async def get_company_feed(
        self, company_id: str, tenant_id: str, limit: int = 50
    ) -> list[SignalEvent]:
        return await self.event_repo.list_by_company(company_id, tenant_id, limit=limit)

    async def acknowledge(self, event_id: str, tenant_id: str) -> SignalEvent | None:
        return await self.event_repo.acknowledge(event_id, tenant_id)

    async def count_unacknowledged(self, tenant_id: str) -> int:
        return await self.event_repo.count_unacknowledged(tenant_id)

    # ── Signal Detection ──

    async def create_signal_event(
        self, signal_id: str, company_id: str, tenant_id: str, data: dict | None = None
    ) -> SignalEvent | None:
        signal = await self.signal_repo.get_by_id(signal_id)
        if signal is None:
            return None

        event = SignalEvent(
            id=str(uuid.uuid4()),
            signal_id=signal_id,
            company_id=company_id,
            tenant_id=tenant_id,
            data=data or {},
        )
        return await self.event_repo.create(event)
