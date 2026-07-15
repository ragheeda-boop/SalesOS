from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_current_tenant_id

from .schemas import (
    AcknowledgeResponse,
    SignalEventResponse,
    SignalFeedResponse,
    SignalListResponse,
    SignalResponse,
    SubscribeRequest,
    SubscribeResponse,
)
from .service import SignalMarketplaceService

router = APIRouter(
    prefix="/api/v1/signals",
    tags=["Signal Marketplace"],
)

_service: SignalMarketplaceService | None = None


def get_signal_service() -> SignalMarketplaceService:
    global _service
    if _service is None:
        _service = SignalMarketplaceService()
    return _service


@router.get("", response_model=SignalListResponse)
async def list_signals(
    domain: str | None = Query(None, description="Filter by domain"),
    pack_id: str | None = Query(None, description="Filter by Knowledge Pack ID"),
    service: SignalMarketplaceService = Depends(get_signal_service),
):
    signals = await service.list_signals(domain=domain, pack_id=pack_id)
    return SignalListResponse(
        total=len(signals),
        signals=[SignalResponse(
            id=s.id, name=s.name, ar_name=s.ar_name,
            description=s.description, domain=s.domain,
            category=s.category, severity=s.severity,
            source=s.source, pack_id=s.pack_id,
            priority=s.priority, weight=s.weight,
            decay_days=s.decay_days, triggers=s.triggers,
            relevance_sectors=s.relevance_sectors,
            created_at=s.created_at,
        ) for s in signals],
    )


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: str,
    service: SignalMarketplaceService = Depends(get_signal_service),
):
    signal = await service.get_signal(signal_id)
    if signal is None:
        raise HTTPException(status_code=404, detail="Signal not found")
    return SignalResponse(
        id=signal.id, name=signal.name, ar_name=signal.ar_name,
        description=signal.description, domain=signal.domain,
        category=signal.category, severity=signal.severity,
        source=signal.source, pack_id=signal.pack_id,
        priority=signal.priority, weight=signal.weight,
        decay_days=signal.decay_days, triggers=signal.triggers,
        relevance_sectors=signal.relevance_sectors,
        created_at=signal.created_at,
    )


@router.post("/subscribe", response_model=SubscribeResponse, status_code=201)
async def subscribe(
    body: SubscribeRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    service: SignalMarketplaceService = Depends(get_signal_service),
):
    try:
        sub = await service.subscribe(
            signal_id=body.signal_id,
            company_id=body.company_id,
            tenant_id=tenant_id,
            channel=body.channel,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return SubscribeResponse(
        id=sub.id, signal_id=sub.signal_id,
        company_id=sub.company_id, tenant_id=sub.tenant_id,
        channel=sub.channel, active=sub.active,
        created_at=sub.created_at,
    )


@router.delete("/subscribe/{sub_id}")
async def unsubscribe(
    sub_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    service: SignalMarketplaceService = Depends(get_signal_service),
):
    ok = await service.unsubscribe(sub_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {"message": "Unsubscribed", "subscription_id": sub_id}


@router.get("/subscriptions", response_model=list[SubscribeResponse])
async def list_subscriptions(
    tenant_id: str = Depends(get_current_tenant_id),
    service: SignalMarketplaceService = Depends(get_signal_service),
):
    subs = await service.list_subscriptions(tenant_id)
    return [SubscribeResponse(
        id=s.id, signal_id=s.signal_id,
        company_id=s.company_id, tenant_id=s.tenant_id,
        channel=s.channel, active=s.active,
        created_at=s.created_at,
    ) for s in subs]


@router.get("/feed", response_model=SignalFeedResponse)
async def get_feed(
    limit: int = Query(50, ge=1, le=200),
    acknowledged: bool | None = Query(None),
    tenant_id: str = Depends(get_current_tenant_id),
    service: SignalMarketplaceService = Depends(get_signal_service),
):
    events = await service.get_feed(tenant_id, limit=limit, acknowledged=acknowledged)
    return SignalFeedResponse(
        total=len(events),
        events=[SignalEventResponse(
            id=e.id, signal_id=e.signal_id,
            company_id=e.company_id, tenant_id=e.tenant_id,
            data=e.data, detected_at=e.detected_at,
            acknowledged=e.acknowledged, acknowledged_at=e.acknowledged_at,
        ) for e in events],
    )


@router.post("/{event_id}/acknowledge", response_model=AcknowledgeResponse)
async def acknowledge(
    event_id: str,
    service: SignalMarketplaceService = Depends(get_signal_service),
):
    event = await service.acknowledge(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Signal event not found")
    return AcknowledgeResponse(
        id=event.id, signal_id=event.signal_id,
        company_id=event.company_id,
        acknowledged=event.acknowledged,
        acknowledged_at=event.acknowledged_at,
    )
