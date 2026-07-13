from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_current_tenant_id

from .schemas import (
    WebhookDeliveryResponse,
    WebhookSubscriptionCreate,
    WebhookSubscriptionResponse,
    WebhookSubscriptionUpdate,
)
from .service import WebhookService

router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["Webhooks"],
    dependencies=[Depends(get_current_tenant_id)],
)

_service: WebhookService | None = None


def get_webhook_service() -> WebhookService:
    global _service
    if _service is None:
        _service = WebhookService()
    return _service


@router.get("/subscriptions", response_model=list[WebhookSubscriptionResponse])
async def list_subscriptions(
    tenant_id: str = Depends(get_current_tenant_id),
    service: WebhookService = Depends(get_webhook_service),
):
    subs = await service.list_subscriptions(tenant_id)
    return [WebhookSubscriptionResponse(
        id=s.id, tenant_id=s.tenant_id, url=s.url,
        events=s.events, is_active=s.is_active,
        created_at=s.created_at, updated_at=s.updated_at,
    ) for s in subs]


@router.post("/subscriptions", response_model=WebhookSubscriptionResponse, status_code=201)
async def create_subscription(
    body: WebhookSubscriptionCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    service: WebhookService = Depends(get_webhook_service),
):
    try:
        body.validate_events()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    sub = await service.create_subscription(
        tenant_id=tenant_id,
        url=body.url,
        events=body.events,
        secret=body.secret,
    )
    return WebhookSubscriptionResponse(
        id=sub.id, tenant_id=sub.tenant_id, url=sub.url,
        events=sub.events, is_active=sub.is_active,
        created_at=sub.created_at, updated_at=sub.updated_at,
    )


@router.get("/subscriptions/{sub_id}", response_model=WebhookSubscriptionResponse)
async def get_subscription(
    sub_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    service: WebhookService = Depends(get_webhook_service),
):
    sub = await service.get_subscription(sub_id)
    if not sub or sub.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return WebhookSubscriptionResponse(
        id=sub.id, tenant_id=sub.tenant_id, url=sub.url,
        events=sub.events, is_active=sub.is_active,
        created_at=sub.created_at, updated_at=sub.updated_at,
    )


@router.patch("/subscriptions/{sub_id}", response_model=WebhookSubscriptionResponse)
async def update_subscription(
    sub_id: str,
    body: WebhookSubscriptionUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    service: WebhookService = Depends(get_webhook_service),
):
    existing = await service.get_subscription(sub_id)
    if not existing or existing.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Subscription not found")

    data = body.model_dump(exclude_none=True)
    sub = await service.update_subscription(sub_id, data)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return WebhookSubscriptionResponse(
        id=sub.id, tenant_id=sub.tenant_id, url=sub.url,
        events=sub.events, is_active=sub.is_active,
        created_at=sub.created_at, updated_at=sub.updated_at,
    )


@router.delete("/subscriptions/{sub_id}")
async def delete_subscription(
    sub_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    service: WebhookService = Depends(get_webhook_service),
):
    sub = await service.get_subscription(sub_id)
    if not sub or sub.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Subscription not found")
    await service.delete_subscription(sub_id)
    return {"message": "Subscription deleted", "subscription_id": sub_id}


@router.get("/subscriptions/{sub_id}/deliveries", response_model=list[WebhookDeliveryResponse])
async def get_delivery_logs(
    sub_id: str,
    limit: int = Query(50, ge=1, le=200),
    tenant_id: str = Depends(get_current_tenant_id),
    service: WebhookService = Depends(get_webhook_service),
):
    sub = await service.get_subscription(sub_id)
    if not sub or sub.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Subscription not found")

    deliveries = await service.get_delivery_logs(sub_id, limit=limit)
    return [WebhookDeliveryResponse(
        id=d.id, subscription_id=d.subscription_id,
        event_type=d.event_type, payload=d.payload,
        status=d.status, response_code=d.response_code,
        response_body=d.response_body, attempt=d.attempt,
        next_retry_at=d.next_retry_at, created_at=d.created_at,
    ) for d in deliveries]


@router.post("/deliveries/{delivery_id}/retry")
async def retry_delivery(
    delivery_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    service: WebhookService = Depends(get_webhook_service),
):
    from .models import WebhookDelivery
    delivery = await service.retry_delivery(delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found or not retryable")
    return WebhookDeliveryResponse(
        id=delivery.id, subscription_id=delivery.subscription_id,
        event_type=delivery.event_type, payload=delivery.payload,
        status=delivery.status, response_code=delivery.response_code,
        response_body=delivery.response_body, attempt=delivery.attempt,
        next_retry_at=delivery.next_retry_at, created_at=delivery.created_at,
    )
