from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.webhooks.models import WebhookDelivery, WebhookSubscription
from app.modules.webhooks.repository import (
    InMemoryWebhookDeliveryRepository,
    InMemoryWebhookSubscriptionRepository,
)
from app.modules.webhooks.service import WebhookService, _sign_payload


@pytest.fixture
def sub_repo():
    return InMemoryWebhookSubscriptionRepository()


@pytest.fixture
def delivery_repo():
    return InMemoryWebhookDeliveryRepository()


@pytest.fixture
def service(sub_repo, delivery_repo):
    return WebhookService(subscription_repo=sub_repo, delivery_repo=delivery_repo)


@pytest.fixture
def sample_sub():
    return WebhookSubscription(
        id=str(uuid.uuid4()),
        tenant_id="tenant-1",
        url="https://example.com/webhook",
        secret="test-secret-key-12345678",
        events=["company.created", "company.updated"],
    )


# ── Subscription CRUD Tests ──

class TestCreateSubscription:
    @pytest.mark.asyncio
    async def test_create_subscription(self, service):
        sub = await service.create_subscription(
            tenant_id="tenant-1",
            url="https://example.com/webhook",
            events=["company.created"],
            secret="test-secret-12345678",
        )
        assert sub.id is not None
        assert sub.tenant_id == "tenant-1"
        assert sub.url == "https://example.com/webhook"
        assert sub.events == ["company.created"]
        assert sub.is_active is True

    @pytest.mark.asyncio
    async def test_create_subscription_multiple_events(self, service):
        sub = await service.create_subscription(
            tenant_id="tenant-1",
            url="https://example.com/webhook",
            events=["company.created", "company.updated", "opportunity.won"],
            secret="test-secret-12345678",
        )
        assert len(sub.events) == 3
        assert "opportunity.won" in sub.events


class TestListSubscriptions:
    @pytest.mark.asyncio
    async def test_list_subscriptions(self, service):
        await service.create_subscription("tenant-1", "https://a.com", ["company.created"], "secret-12345678")
        await service.create_subscription("tenant-1", "https://b.com", ["company.updated"], "secret-12345678")
        subs = await service.list_subscriptions("tenant-1")
        assert len(subs) == 2

    @pytest.mark.asyncio
    async def test_list_subscriptions_empty(self, service):
        subs = await service.list_subscriptions("tenant-1")
        assert subs == []

    @pytest.mark.asyncio
    async def test_list_subscriptions_tenant_isolation(self, service):
        await service.create_subscription("tenant-1", "https://a.com", ["company.created"], "secret-12345678")
        await service.create_subscription("tenant-2", "https://b.com", ["company.created"], "secret-12345678")
        subs = await service.list_subscriptions("tenant-1")
        assert len(subs) == 1


class TestDeleteSubscription:
    @pytest.mark.asyncio
    async def test_delete_subscription(self, service):
        sub = await service.create_subscription("tenant-1", "https://a.com", ["company.created"], "secret-12345678")
        ok = await service.delete_subscription(sub.id)
        assert ok is True
        assert await service.get_subscription(sub.id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_subscription(self, service):
        ok = await service.delete_subscription("nonexistent")
        assert ok is False


class TestUpdateSubscription:
    @pytest.mark.asyncio
    async def test_update_subscription_events(self, service):
        sub = await service.create_subscription("tenant-1", "https://a.com", ["company.created"], "secret-12345678")
        updated = await service.update_subscription(sub.id, {"events": ["company.created", "company.updated"]})
        assert updated is not None
        assert "company.updated" in updated.events

    @pytest.mark.asyncio
    async def test_update_subscription_deactivate(self, service):
        sub = await service.create_subscription("tenant-1", "https://a.com", ["company.created"], "secret-12345678")
        updated = await service.update_subscription(sub.id, {"is_active": False})
        assert updated is not None
        assert updated.is_active is False

    @pytest.mark.asyncio
    async def test_update_subscription_nonexistent(self, service):
        updated = await service.update_subscription("nonexistent", {"is_active": False})
        assert updated is None


# ── Signature Tests ──

class TestSignature:
    def test_sign_payload_consistent(self):
        payload = {"event": "company.created", "data": {"id": "123"}}
        s1 = _sign_payload(payload, "secret-key")
        s2 = _sign_payload(payload, "secret-key")
        assert s1 == s2

    def test_sign_payload_different_secret(self):
        payload = {"event": "company.created"}
        s1 = _sign_payload(payload, "secret-1")
        s2 = _sign_payload(payload, "secret-2")
        assert s1 != s2

    def test_sign_payload_hmac_sha256(self):
        payload = {"test": "value"}
        secret = "my-secret-key"
        sig = _sign_payload(payload, secret)
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        expected = hmac.new(
            secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        assert sig == expected


# ── Dispatch & Delivery Tests ──

class TestDispatchEvent:
    @pytest.mark.asyncio
    async def test_dispatch_event_no_subscribers(self, service):
        deliveries = await service.dispatch_event("company.created", {"id": "1"}, "tenant-1")
        assert deliveries == []

    @pytest.mark.asyncio
    async def test_dispatch_event_delivery_created(self, service):
        await service.create_subscription("tenant-1", "https://example.com/hook", ["company.created"], "secret-12345678")
        deliveries = await service.dispatch_event("company.created", {"id": "1"}, "tenant-1")
        assert len(deliveries) == 1
        assert deliveries[0].event_type == "company.created"
        assert deliveries[0].payload == {"id": "1"}

    @pytest.mark.asyncio
    async def test_dispatch_event_multiple_subscribers(self, service):
        await service.create_subscription("tenant-1", "https://a.com/hook", ["company.created"], "secret-1")
        await service.create_subscription("tenant-1", "https://b.com/hook", ["company.created"], "secret-2")
        deliveries = await service.dispatch_event("company.created", {"id": "1"}, "tenant-1")
        assert len(deliveries) == 2

    @pytest.mark.asyncio
    async def test_dispatch_event_tenant_isolation(self, service):
        await service.create_subscription("tenant-1", "https://a.com/hook", ["company.created"], "secret-1")
        await service.create_subscription("tenant-2", "https://b.com/hook", ["company.created"], "secret-2")
        deliveries = await service.dispatch_event("company.created", {"id": "1"}, "tenant-1")
        assert len(deliveries) == 1

    @pytest.mark.asyncio
    async def test_dispatch_event_inactive_skipped(self, service):
        sub = await service.create_subscription("tenant-1", "https://a.com/hook", ["company.created"], "secret-1")
        await service.update_subscription(sub.id, {"is_active": False})
        deliveries = await service.dispatch_event("company.created", {"id": "1"}, "tenant-1")
        assert deliveries == []

    @pytest.mark.asyncio
    async def test_dispatch_event_wrong_event_skipped(self, service):
        await service.create_subscription("tenant-1", "https://a.com/hook", ["company.updated"], "secret-1")
        deliveries = await service.dispatch_event("company.created", {"id": "1"}, "tenant-1")
        assert deliveries == []


class TestDeliveryAttempt:
    @pytest.mark.asyncio
    async def test_delivery_success(self, service):
        await service.create_subscription("tenant-1", "https://example.com/hook", ["company.created"], "secret-1")

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.is_success = True
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_instance

            deliveries = await service.dispatch_event("company.created", {"id": "1"}, "tenant-1")

        assert len(deliveries) == 1
        assert deliveries[0].status == "success"
        assert deliveries[0].response_code == 200
        assert deliveries[0].attempt == 1

    @pytest.mark.asyncio
    async def test_delivery_failure_schedules_retry(self, service):
        await service.create_subscription("tenant-1", "https://example.com/hook", ["company.created"], "secret-1")

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.side_effect = Exception("Connection refused")

            deliveries = await service.dispatch_event("company.created", {"id": "1"}, "tenant-1")

        assert len(deliveries) == 1
        assert deliveries[0].status == "failed"
        assert deliveries[0].attempt == 1
        assert deliveries[0].next_retry_at is not None

    @pytest.mark.asyncio
    async def test_delivery_signature_header(self, service):
        sub = await service.create_subscription("tenant-1", "https://example.com/hook", ["company.created"], "my-secret")

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.is_success = True
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_instance

            await service.dispatch_event("company.created", {"id": "1"}, "tenant-1")

            call_kwargs = mock_instance.post.call_args[1]
            headers = call_kwargs.get("headers", {})
            assert "X-Webhook-Signature" in headers
            expected_sig = _sign_payload({"id": "1"}, "my-secret")
            assert headers["X-Webhook-Signature"] == expected_sig
            assert headers["X-Webhook-Event"] == "company.created"


class TestRetry:
    @pytest.mark.asyncio
    async def test_retry_failed_delivery(self, service):
        await service.create_subscription("tenant-1", "https://example.com/hook", ["company.created"], "secret-1")

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.side_effect = Exception("Connection refused")
            deliveries = await service.dispatch_event("company.created", {"id": "1"}, "tenant-1")

        delivery_id = deliveries[0].id

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.is_success = True
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_instance

            retried = await service.retry_delivery(delivery_id)

        assert retried is not None
        assert retried.status == "success"
        assert retried.attempt == 2

    @pytest.mark.asyncio
    async def test_retry_successful_delivery_fails(self, service):
        await service.create_subscription("tenant-1", "https://example.com/hook", ["company.created"], "secret-1")

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.is_success = True
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_instance

            deliveries = await service.dispatch_event("company.created", {"id": "1"}, "tenant-1")

        retried = await service.retry_delivery(deliveries[0].id)
        assert retried is None

    @pytest.mark.asyncio
    async def test_retry_nonexistent_delivery(self, service):
        retried = await service.retry_delivery("nonexistent")
        assert retried is None


class TestDeliveryLogs:
    @pytest.mark.asyncio
    async def test_get_delivery_logs(self, service):
        sub = await service.create_subscription("tenant-1", "https://example.com/hook", ["company.created"], "secret-1")

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.side_effect = Exception("fail")
            await service.dispatch_event("company.created", {"id": "1"}, "tenant-1")

        logs = await service.get_delivery_logs(sub.id)
        assert len(logs) == 1
        assert logs[0].event_type == "company.created"

    @pytest.mark.asyncio
    async def test_get_delivery_logs_limit(self, service):
        sub = await service.create_subscription("tenant-1", "https://example.com/hook", ["company.created"], "secret-1")

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.side_effect = Exception("fail")
            for i in range(5):
                await service.dispatch_event("company.created", {"id": str(i)}, "tenant-1")

        logs = await service.get_delivery_logs(sub.id, limit=2)
        assert len(logs) == 2


# ── Repository-level Tests ──

class TestSubscriptionRepository:
    @pytest.mark.asyncio
    async def test_find_by_event(self, sub_repo, sample_sub):
        await sub_repo.create(sample_sub)
        found = await sub_repo.find_by_event("tenant-1", "company.created")
        assert len(found) == 1
        assert found[0].id == sample_sub.id

    @pytest.mark.asyncio
    async def test_find_by_event_inactive_skipped(self, sub_repo, sample_sub):
        sample_sub.is_active = False
        await sub_repo.create(sample_sub)
        found = await sub_repo.find_by_event("tenant-1", "company.created")
        assert found == []

    @pytest.mark.asyncio
    async def test_find_by_event_wrong_tenant(self, sub_repo, sample_sub):
        await sub_repo.create(sample_sub)
        found = await sub_repo.find_by_event("tenant-2", "company.created")
        assert found == []

    @pytest.mark.asyncio
    async def test_find_by_event_wrong_event(self, sub_repo, sample_sub):
        await sub_repo.create(sample_sub)
        found = await sub_repo.find_by_event("tenant-1", "opportunity.won")
        assert found == []

    @pytest.mark.asyncio
    async def test_list_by_tenant(self, sub_repo, sample_sub):
        await sub_repo.create(sample_sub)
        subs = await sub_repo.list_by_tenant("tenant-1")
        assert len(subs) == 1

    @pytest.mark.asyncio
    async def test_list_by_tenant_isolation(self, sub_repo, sample_sub):
        await sub_repo.create(sample_sub)
        subs = await sub_repo.list_by_tenant("tenant-2")
        assert subs == []

    @pytest.mark.asyncio
    async def test_delete_existing(self, sub_repo, sample_sub):
        await sub_repo.create(sample_sub)
        ok = await sub_repo.delete(sample_sub.id)
        assert ok is True
        assert await sub_repo.get(sample_sub.id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, sub_repo):
        ok = await sub_repo.delete("nonexistent")
        assert ok is False


class TestDeliveryRepository:
    @pytest.mark.asyncio
    async def test_list_by_subscription(self, delivery_repo):
        d1 = WebhookDelivery(id="d-1", subscription_id="s-1", event_type="company.created", payload={})
        d2 = WebhookDelivery(id="d-2", subscription_id="s-1", event_type="company.updated", payload={})
        d3 = WebhookDelivery(id="d-3", subscription_id="s-2", event_type="company.created", payload={})
        await delivery_repo.create(d1)
        await delivery_repo.create(d2)
        await delivery_repo.create(d3)
        logs = await delivery_repo.list_by_subscription("s-1")
        assert len(logs) == 2

    @pytest.mark.asyncio
    async def test_list_pending_retries(self, delivery_repo):
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        retryable = WebhookDelivery(
            id="d-1", subscription_id="s-1", event_type="company.created",
            payload={}, status="failed", attempt=1,
            next_retry_at=now - timedelta(seconds=10),
        )
        not_yet = WebhookDelivery(
            id="d-2", subscription_id="s-1", event_type="company.created",
            payload={}, status="failed", attempt=1,
            next_retry_at=now + timedelta(hours=1),
        )
        maxed = WebhookDelivery(
            id="d-3", subscription_id="s-1", event_type="company.created",
            payload={}, status="failed", attempt=3,
            next_retry_at=now - timedelta(seconds=10),
        )
        await delivery_repo.create(retryable)
        await delivery_repo.create(not_yet)
        await delivery_repo.create(maxed)
        pending = await delivery_repo.list_pending_retries()
        assert len(pending) == 1
        assert pending[0].id == "d-1"


# ── All supported events test ──

class TestSupportedEvents:
    @pytest.mark.asyncio
    async def test_all_events_dispatched(self, service):
        events = [
            "company.created", "company.updated",
            "opportunity.created", "opportunity.stage_changed", "opportunity.won", "opportunity.lost",
            "decision.evaluated",
            "pipeline.updated",
            "search.performed",
            "workflow.completed",
            "employee.updated",
        ]
        await service.create_subscription("tenant-1", "https://example.com/hook", events, "secret-1")

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.is_success = True
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_instance

            for event in events:
                deliveries = await service.dispatch_event(event, {"source": "test"}, "tenant-1")
                assert len(deliveries) == 1
                assert deliveries[0].status == "success"
