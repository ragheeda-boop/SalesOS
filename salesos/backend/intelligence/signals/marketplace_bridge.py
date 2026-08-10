"""Signal Marketplace Bridge — canonical signal ingestion path.

Connects the SignalMarketplaceService (DB-backed, REST API) to the
intelligence SignalEngine (in-memory, recommendation-generating).

Maps marketplace Signal/SignalEvent objects to intelligence BuyingSignals.
Ensures exactly one canonical path from signal detection to intelligence consumption.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from app.modules.signal_marketplace.models import Signal, SignalEvent
from app.modules.signal_marketplace.service import SignalMarketplaceService
from intelligence.signals import (
    BuyingSignal,
    Priority,
    SignalEngine,
)
from intelligence.business_objects import SignalType

logger = logging.getLogger(__name__)

_DOMAIN_TO_SIGNAL_TYPE: dict[str, SignalType] = {
    "funding": SignalType.FUNDING,
    "hiring": SignalType.HIRING,
    "expansion": SignalType.EXPANSION,
    "contract": SignalType.CONTRACT,
    "project": SignalType.PROJECT,
    "news": SignalType.NEWS,
    "partnership": SignalType.PARTNERSHIP,
    "merger": SignalType.MERGER,
    "leadership": SignalType.LEADERSHIP,
    "tender": SignalType.TENDER,
    "competitor": SignalType.COMPETITOR_MOVE,
    "regulatory": SignalType.REGULATORY,
}


def _map_priority(priority: str) -> Priority:
    p = priority.lower()
    if p in ("critical", "high"):
        return Priority.HIGH
    if p == "medium":
        return Priority.MEDIUM
    return Priority.LOW


def _resolve_signal_type(signal: Signal) -> SignalType:
    domain = (signal.domain or "").lower()
    category = (signal.category or "").lower()
    for key, st in _DOMAIN_TO_SIGNAL_TYPE.items():
        if key in domain or key in category:
            return st
    return SignalType.NEWS


class SignalMarketplaceBridge:
    """Bridge: SignalMarketplace ←→ SignalEngine.

    When a signal event is created in the marketplace, this bridge
    maps it to a BuyingSignal and feeds it into the SignalEngine
    for recommendation generation.

    Design: Pass-through adapter. Does not replace SignalEngine.
    Does not create a fifth signal system.
    """

    def __init__(
        self,
        marketplace_service: SignalMarketplaceService,
        signal_engine: SignalEngine,
    ):
        self._marketplace = marketplace_service
        self._engine = signal_engine

    async def ingest_event(self, event: SignalEvent) -> BuyingSignal | None:
        signal = await self._marketplace.get_signal(event.signal_id)
        if signal is None:
            logger.warning(
                "SignalBridge: unknown signal_id=%s for event=%s",
                event.signal_id,
                event.id,
            )
            return None

        signal_type = _resolve_signal_type(signal)
        priority = _map_priority(signal.priority)
        intensity = signal.weight

        buying_signal = self._engine.ingest_signal(
            company_id=event.company_id,
            signal_type=signal_type,
            title=signal.name,
            description=signal.description or "",
            source=f"signal_marketplace:{signal.source or signal.pack_id}",
            intensity=intensity,
            metadata={
                "marketplace_signal_id": signal.id,
                "marketplace_event_id": event.id,
                "domain": signal.domain,
                "category": signal.category,
                "tenant_id": event.tenant_id,
                "event_data": event.data,
            },
        )
        logger.info(
            "SignalBridge: ingested signal_type=%s company=%s intensity=%.2f",
            signal_type.value,
            event.company_id,
            intensity,
        )
        return buying_signal

    async def ingest_pending_events(
        self,
        tenant_id: str,
        limit: int = 100,
    ) -> list[BuyingSignal]:
        """Feed all unacknowledged marketplace events into SignalEngine."""
        events = await self._marketplace.get_feed(
            tenant_id,
            limit=limit,
            acknowledged=False,
        )
        results: list[BuyingSignal] = []
        for event in events:
            bs = await self.ingest_event(event)
            if bs:
                results.append(bs)
        return results


def create_bridge(
    marketplace_service: SignalMarketplaceService,
    signal_engine: SignalEngine,
) -> SignalMarketplaceBridge:
    return SignalMarketplaceBridge(marketplace_service, signal_engine)
