"""Postgres implementations of signal marketplace repositories (C.1)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .db_models import SignalCatalogModel, SignalEventModel, SignalSubscriptionModel
from .models import Signal, SignalEvent, SignalSubscription
from .repository import SignalEventRepository, SignalRepository, SignalSubscriptionRepository


def _signal_from_row(row: SignalCatalogModel) -> Signal:
    return Signal(
        id=row.id,
        name=row.name,
        ar_name=row.ar_name or "",
        description=row.description or "",
        domain=row.domain or "",
        category=row.category or "",
        severity=row.severity or "info",
        source=row.source or "",
        pack_id=row.pack_id or "",
        priority=row.priority or "medium",
        weight=float(row.weight or 0.5),
        decay_days=int(row.decay_days or 90),
        triggers=list(row.triggers or []),
        relevance_sectors=list(row.relevance_sectors or []),
        created_at=row.created_at,
    )


def _sub_from_row(row: SignalSubscriptionModel) -> SignalSubscription:
    return SignalSubscription(
        id=row.id,
        signal_id=row.signal_id,
        company_id=row.company_id,
        tenant_id=row.tenant_id,
        channel=row.channel or "in-app",
        active=bool(row.active),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _event_from_row(row: SignalEventModel) -> SignalEvent:
    return SignalEvent(
        id=row.id,
        signal_id=row.signal_id,
        company_id=row.company_id,
        tenant_id=row.tenant_id,
        data=dict(row.data or {}),
        detected_at=row.detected_at,
        acknowledged=bool(row.acknowledged),
        acknowledged_at=row.acknowledged_at,
    )


class PostgresSignalRepository(SignalRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_all(self, domain: str | None = None, pack_id: str | None = None) -> list[Signal]:
        q = select(SignalCatalogModel)
        if domain:
            q = q.where(SignalCatalogModel.domain == domain)
        if pack_id:
            q = q.where(SignalCatalogModel.pack_id == pack_id)
        result = await self._session.execute(q.order_by(SignalCatalogModel.created_at.desc()))
        return [_signal_from_row(r) for r in result.scalars().all()]

    async def get_by_id(self, signal_id: str) -> Signal | None:
        row = await self._session.get(SignalCatalogModel, signal_id)
        return _signal_from_row(row) if row else None

    async def upsert(self, signal: Signal) -> None:
        row = await self._session.get(SignalCatalogModel, signal.id)
        if row is None:
            row = SignalCatalogModel(id=signal.id)
            self._session.add(row)
        row.name = signal.name
        row.ar_name = signal.ar_name
        row.description = signal.description
        row.domain = signal.domain
        row.category = signal.category
        row.severity = signal.severity
        row.source = signal.source
        row.pack_id = signal.pack_id
        row.priority = signal.priority
        row.weight = signal.weight
        row.decay_days = signal.decay_days
        row.triggers = list(signal.triggers or [])
        row.relevance_sectors = list(signal.relevance_sectors or [])
        await self._session.flush()

    async def delete(self, signal_id: str) -> bool:
        row = await self._session.get(SignalCatalogModel, signal_id)
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True


class PostgresSignalSubscriptionRepository(SignalSubscriptionRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, sub: SignalSubscription) -> SignalSubscription:
        row = SignalSubscriptionModel(
            id=sub.id,
            signal_id=sub.signal_id,
            company_id=sub.company_id,
            tenant_id=sub.tenant_id,
            channel=sub.channel,
            active=sub.active,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
        )
        self._session.add(row)
        await self._session.flush()
        return _sub_from_row(row)

    async def get(self, sub_id: str) -> SignalSubscription | None:
        row = await self._session.get(SignalSubscriptionModel, sub_id)
        return _sub_from_row(row) if row else None

    async def list_by_tenant(self, tenant_id: str) -> list[SignalSubscription]:
        result = await self._session.execute(
            select(SignalSubscriptionModel)
            .where(SignalSubscriptionModel.tenant_id == tenant_id)
            .order_by(SignalSubscriptionModel.created_at.desc())
        )
        return [_sub_from_row(r) for r in result.scalars().all()]

    async def list_by_signal_and_company(
        self, signal_id: str, company_id: str, tenant_id: str
    ) -> list[SignalSubscription]:
        result = await self._session.execute(
            select(SignalSubscriptionModel).where(
                SignalSubscriptionModel.signal_id == signal_id,
                SignalSubscriptionModel.company_id == company_id,
                SignalSubscriptionModel.tenant_id == tenant_id,
            )
        )
        return [_sub_from_row(r) for r in result.scalars().all()]

    async def delete(self, sub_id: str) -> bool:
        row = await self._session.get(SignalSubscriptionModel, sub_id)
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True

    async def find_active_by_signal(
        self, signal_id: str, tenant_id: str
    ) -> list[SignalSubscription]:
        result = await self._session.execute(
            select(SignalSubscriptionModel).where(
                SignalSubscriptionModel.signal_id == signal_id,
                SignalSubscriptionModel.tenant_id == tenant_id,
                SignalSubscriptionModel.active.is_(True),
            )
        )
        return [_sub_from_row(r) for r in result.scalars().all()]


class PostgresSignalEventRepository(SignalEventRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, event: SignalEvent) -> SignalEvent:
        row = SignalEventModel(
            id=event.id,
            signal_id=event.signal_id,
            company_id=event.company_id,
            tenant_id=event.tenant_id,
            data=event.data or {},
            detected_at=event.detected_at,
            acknowledged=event.acknowledged,
            acknowledged_at=event.acknowledged_at,
        )
        self._session.add(row)
        await self._session.flush()
        return _event_from_row(row)

    async def get(self, event_id: str) -> SignalEvent | None:
        row = await self._session.get(SignalEventModel, event_id)
        return _event_from_row(row) if row else None

    async def list_by_tenant(
        self, tenant_id: str, limit: int = 50, acknowledged: bool | None = None
    ) -> list[SignalEvent]:
        q = select(SignalEventModel).where(SignalEventModel.tenant_id == tenant_id)
        if acknowledged is not None:
            q = q.where(SignalEventModel.acknowledged.is_(acknowledged))
        result = await self._session.execute(
            q.order_by(SignalEventModel.detected_at.desc()).limit(limit)
        )
        return [_event_from_row(r) for r in result.scalars().all()]

    async def list_by_company(
        self, company_id: str, tenant_id: str, limit: int = 50
    ) -> list[SignalEvent]:
        result = await self._session.execute(
            select(SignalEventModel)
            .where(
                SignalEventModel.company_id == company_id,
                SignalEventModel.tenant_id == tenant_id,
            )
            .order_by(SignalEventModel.detected_at.desc())
            .limit(limit)
        )
        return [_event_from_row(r) for r in result.scalars().all()]

    async def acknowledge(self, event_id: str, tenant_id: str) -> SignalEvent | None:
        result = await self._session.execute(
            select(SignalEventModel).where(
                SignalEventModel.id == event_id,
                SignalEventModel.tenant_id == tenant_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.acknowledged = True
        row.acknowledged_at = datetime.now(UTC)
        await self._session.flush()
        return _event_from_row(row)

    async def count_unacknowledged(self, tenant_id: str) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(SignalEventModel)
            .where(
                SignalEventModel.tenant_id == tenant_id,
                SignalEventModel.acknowledged.is_(False),
            )
        )
        return int(result.scalar() or 0)
