from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from .models import Signal, SignalEvent, SignalSubscription


class SignalRepository:
    async def get_all(self, domain: str | None = None, pack_id: str | None = None) -> list[Signal]:
        raise NotImplementedError

    async def get_by_id(self, signal_id: str) -> Signal | None:
        raise NotImplementedError

    async def upsert(self, signal: Signal) -> None:
        raise NotImplementedError

    async def delete(self, signal_id: str) -> bool:
        raise NotImplementedError


class SignalSubscriptionRepository:
    async def create(self, sub: SignalSubscription) -> SignalSubscription:
        raise NotImplementedError

    async def get(self, sub_id: str) -> SignalSubscription | None:
        raise NotImplementedError

    async def list_by_tenant(self, tenant_id: str) -> list[SignalSubscription]:
        raise NotImplementedError

    async def list_by_signal_and_company(self, signal_id: str, company_id: str) -> list[SignalSubscription]:
        raise NotImplementedError

    async def delete(self, sub_id: str) -> bool:
        raise NotImplementedError

    async def find_active_by_signal(self, signal_id: str, tenant_id: str) -> list[SignalSubscription]:
        raise NotImplementedError


class SignalEventRepository:
    async def create(self, event: SignalEvent) -> SignalEvent:
        raise NotImplementedError

    async def get(self, event_id: str) -> SignalEvent | None:
        raise NotImplementedError

    async def list_by_tenant(self, tenant_id: str, limit: int = 50, acknowledged: bool | None = None) -> list[SignalEvent]:
        raise NotImplementedError

    async def list_by_company(self, company_id: str, tenant_id: str, limit: int = 50) -> list[SignalEvent]:
        raise NotImplementedError

    async def acknowledge(self, event_id: str) -> SignalEvent | None:
        raise NotImplementedError

    async def count_unacknowledged(self, tenant_id: str) -> int:
        raise NotImplementedError


class InMemorySignalRepository(SignalRepository):
    def __init__(self):
        self._store: dict[str, Signal] = {}

    async def get_all(self, domain: str | None = None, pack_id: str | None = None) -> list[Signal]:
        results = list(self._store.values())
        if domain:
            results = [s for s in results if s.domain == domain]
        if pack_id:
            results = [s for s in results if s.pack_id == pack_id]
        return results

    async def get_by_id(self, signal_id: str) -> Signal | None:
        return self._store.get(signal_id)

    async def upsert(self, signal: Signal) -> None:
        self._store[signal.id] = signal

    async def delete(self, signal_id: str) -> bool:
        if signal_id in self._store:
            del self._store[signal_id]
            return True
        return False


class InMemorySignalSubscriptionRepository(SignalSubscriptionRepository):
    def __init__(self):
        self._store: dict[str, SignalSubscription] = {}

    async def create(self, sub: SignalSubscription) -> SignalSubscription:
        self._store[sub.id] = sub
        return sub

    async def get(self, sub_id: str) -> SignalSubscription | None:
        return self._store.get(sub_id)

    async def list_by_tenant(self, tenant_id: str) -> list[SignalSubscription]:
        return [s for s in self._store.values() if s.tenant_id == tenant_id]

    async def list_by_signal_and_company(self, signal_id: str, company_id: str) -> list[SignalSubscription]:
        return [s for s in self._store.values() if s.signal_id == signal_id and s.company_id == company_id]

    async def delete(self, sub_id: str) -> bool:
        if sub_id in self._store:
            del self._store[sub_id]
            return True
        return False

    async def find_active_by_signal(self, signal_id: str, tenant_id: str) -> list[SignalSubscription]:
        return [s for s in self._store.values() if s.signal_id == signal_id and s.tenant_id == tenant_id and s.active]


class InMemorySignalEventRepository(SignalEventRepository):
    def __init__(self):
        self._store: dict[str, SignalEvent] = {}

    async def create(self, event: SignalEvent) -> SignalEvent:
        self._store[event.id] = event
        return event

    async def get(self, event_id: str) -> SignalEvent | None:
        return self._store.get(event_id)

    async def list_by_tenant(self, tenant_id: str, limit: int = 50, acknowledged: bool | None = None) -> list[SignalEvent]:
        results = [e for e in self._store.values() if e.tenant_id == tenant_id]
        if acknowledged is not None:
            results = [e for e in results if e.acknowledged == acknowledged]
        results.sort(key=lambda e: e.detected_at, reverse=True)
        return results[:limit]

    async def list_by_company(self, company_id: str, tenant_id: str, limit: int = 50) -> list[SignalEvent]:
        results = [e for e in self._store.values() if e.company_id == company_id and e.tenant_id == tenant_id]
        results.sort(key=lambda e: e.detected_at, reverse=True)
        return results[:limit]

    async def acknowledge(self, event_id: str) -> SignalEvent | None:
        event = self._store.get(event_id)
        if event is None:
            return None
        event.acknowledged = True
        event.acknowledged_at = datetime.now(timezone.utc)
        return event

    async def count_unacknowledged(self, tenant_id: str) -> int:
        return len([e for e in self._store.values() if e.tenant_id == tenant_id and not e.acknowledged])
