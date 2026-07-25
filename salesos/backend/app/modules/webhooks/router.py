from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import safe_error_detail
from app.dependencies import (
    get_current_tenant_id,
    get_db_session,
    verify_token,
)

from .repository import (
    PostgresWebhookDeliveryRepository,
    PostgresWebhookSubscriptionRepository,
)
from .schemas import (
    WebhookDeliveryResponse,
    WebhookSubscriptionCreate,
    WebhookSubscriptionResponse,
    WebhookSubscriptionUpdate,
)
from .service import WebhookService
from .url_safety import UnsafeWebhookURLError

router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["Webhooks"],
    dependencies=[Depends(verify_token), Depends(get_current_tenant_id)],
)


def get_webhook_service(db: AsyncSession = Depends(get_db_session)) -> WebhookService:
    """Prefer Postgres persistence for production multi-replica safety."""
    return WebhookService(
        subscription_repo=PostgresWebhookSubscriptionRepository(db),
        delivery_repo=PostgresWebhookDeliveryRepository(db),
    )


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
        raise HTTPException(status_code=400, detail=safe_error_detail(e, "Invalid webhook events"))

    try:
        sub = await service.create_subscription(
            tenant_id=tenant_id,
            url=body.url,
            events=body.events,
            secret=body.secret,
        )
    except UnsafeWebhookURLError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
    try:
        sub = await service.update_subscription(sub_id, data)
    except UnsafeWebhookURLError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
    delivery = await service.delivery_repo.get(delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found or not retryable")
    sub = await service.get_subscription(delivery.subscription_id)
    if not sub or sub.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Delivery not found or not retryable")

    retried = await service.retry_delivery(delivery_id)
    if not retried:
        raise HTTPException(status_code=404, detail="Delivery not found or not retryable")
    return WebhookDeliveryResponse(
        id=retried.id, subscription_id=retried.subscription_id,
        event_type=retried.event_type, payload=retried.payload,
        status=retried.status, response_code=retried.response_code,
        response_body=retried.response_body, attempt=retried.attempt,
        next_retry_at=retried.next_retry_at, created_at=retried.created_at,
    )
