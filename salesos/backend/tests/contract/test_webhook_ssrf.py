"""HTTP regression for Phase 0 criterion 1.2 / GA-P0-SEC-02 / PROD-W2-002.

Webhook outbound URL allowlist must reject SSRF targets (localhost, link-local
metadata, RFC1918) at the ASGI boundary for:

1. Integration Hub subscriptions — ``POST /api/v1/webhooks/subscriptions``
2. Workflow webhook endpoints — ``POST /api/v1/webhooks`` (historical finding)

Does not modify get_db() / set_config (DEC-085).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_current_tenant_id, get_db_session, require_permission, verify_token
from app.main import app
from app.modules.webhooks.repository import (
    InMemoryWebhookDeliveryRepository,
    InMemoryWebhookSubscriptionRepository,
)
from app.modules.webhooks.router import get_webhook_service
from app.modules.webhooks.service import WebhookService
from domains.workflow.engine import WorkflowEngine
from domains.workflow.repository import InMemoryWorkflowRepository
from domains.workflow.service import WorkflowService

TENANT = "ssrf-tenant-a"
USER = "ssrf-user-a"
SECRET = "ssrf-regression-secret-16"


# Classic SSRF targets the allowlist must block (criterion 1.2 evidence).
_SSRF_TARGETS = (
    "http://example.com/hook",
    "https://localhost/hook",
    "https://127.0.0.1/hook",
    "https://10.0.0.5/hook",
    "https://192.168.1.10/hook",
    "https://172.16.0.1/hook",
    "https://169.254.169.254/latest/meta-data/",
    "https://metadata.google.internal/computeMetadata/v1/",
    "https://[::1]/hook",
    "https://[fe80::1]/hook",
)


@asynccontextmanager
async def _hub_client(svc: WebhookService) -> AsyncIterator[AsyncClient]:
    async def override_verify_token() -> dict[str, str]:
        return {"sub": USER, "tenant_id": TENANT}

    async def override_tenant() -> str:
        return TENANT

    app.dependency_overrides[verify_token] = override_verify_token
    app.dependency_overrides[get_current_tenant_id] = override_tenant
    app.dependency_overrides[get_webhook_service] = lambda: svc

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(verify_token, None)
        app.dependency_overrides.pop(get_current_tenant_id, None)
        app.dependency_overrides.pop(get_webhook_service, None)


@pytest_asyncio.fixture
async def webhook_svc() -> WebhookService:
    # Literal IP / hostname checks do not need live DNS.
    return WebhookService(
        subscription_repo=InMemoryWebhookSubscriptionRepository(),
        delivery_repo=InMemoryWebhookDeliveryRepository(),
        resolve_dns=False,
    )


@pytest.fixture
def wf_app() -> FastAPI:
    """Isolated workflow router app (Integration Hub workflow webhook caller)."""
    repo = InMemoryWorkflowRepository()
    engine = WorkflowEngine(repository=repo)
    svc = WorkflowService(repository=repo, engine=engine)

    application = FastAPI()

    async def _fake_tenant_id() -> str:
        return TENANT

    async def _fake_token() -> dict:
        return {"sub": USER, "tenant_id": TENANT}

    async def _allow() -> bool:
        return True

    import app.routers.workflows as wr

    application.dependency_overrides[get_current_tenant_id] = _fake_tenant_id
    application.dependency_overrides[verify_token] = _fake_token
    application.dependency_overrides[require_permission] = _allow
    application.dependency_overrides[wr._get_service] = lambda: svc
    application.include_router(wr.router, prefix="/api/v1")

    def _override_auth_deps(dependant) -> None:
        for dependency in getattr(dependant, "dependencies", []) or []:
            call = dependency.call
            if call is None:
                continue
            name = getattr(call, "__name__", "")
            if name in ("_require_permission", "require_permission"):
                application.dependency_overrides[call] = _allow
            elif name == "verify_token" or call is verify_token:
                application.dependency_overrides[call] = _fake_token
            elif name in ("get_db_session", "get_db") or call is get_db_session:
                pass
            _override_auth_deps(dependency)

    for route in wr.router.routes:
        dependant = getattr(route, "dependant", None)
        if dependant is not None:
            _override_auth_deps(dependant)

    return application


@pytest.mark.contract
@pytest.mark.asyncio
@pytest.mark.parametrize("url", _SSRF_TARGETS)
async def test_hub_subscription_rejects_ssrf_targets(
    webhook_svc: WebhookService, url: str
) -> None:
    """GA-P0-SEC-02: Integration Hub subscription create must return 400."""
    async with _hub_client(webhook_svc) as client:
        resp = await client.post(
            "/api/v1/webhooks/subscriptions",
            json={
                "url": url,
                "events": ["company.created"],
                "secret": SECRET,
            },
        )
    assert resp.status_code == 400, f"{url} -> {resp.status_code} {resp.text}"
    detail = resp.json().get("detail", "")
    assert isinstance(detail, str) and len(detail) > 0


@pytest.mark.contract
@pytest.mark.asyncio
async def test_hub_subscription_allows_public_https(webhook_svc: WebhookService) -> None:
    async with _hub_client(webhook_svc) as client:
        with patch(
            "socket.getaddrinfo",
            return_value=[(None, None, None, None, ("93.184.216.34", 443))],
        ):
            # resolve_dns=False on fixture — public hostname passes host checks.
            resp = await client.post(
                "/api/v1/webhooks/subscriptions",
                json={
                    "url": "https://example.com/hook",
                    "events": ["company.created"],
                    "secret": SECRET,
                },
            )
    assert resp.status_code == 201, resp.text
    assert resp.json()["url"].startswith("https://example.com")


@pytest.mark.contract
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    (
        "http://evil.example/hook",
        "https://localhost:8443/hook",
        "https://127.0.0.1/hook",
        "https://10.1.2.3/hook",
        "https://169.254.169.254/latest/meta-data/",
        "https://192.168.0.50/hook",
    ),
)
async def test_workflow_webhook_rejects_ssrf_targets(wf_app: FastAPI, url: str) -> None:
    """Historical workflows.py SSRF surface must return 400 (not 500)."""
    transport = ASGITransport(app=wf_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/webhooks",
            json={"url": url, "name": "SSRF Probe", "auth_type": "none"},
            headers={"Authorization": "Bearer test", "X-Tenant-Id": TENANT},
        )
    assert resp.status_code == 400, f"{url} -> {resp.status_code} {resp.text}"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_hub_rejects_dns_rebinding_to_private(webhook_svc: WebhookService) -> None:
    """DNS that resolves to RFC1918 must be blocked even for public hostnames."""
    svc = WebhookService(
        subscription_repo=InMemoryWebhookSubscriptionRepository(),
        delivery_repo=InMemoryWebhookDeliveryRepository(),
        resolve_dns=True,
    )
    async with _hub_client(svc) as client:
        with patch(
            "socket.getaddrinfo",
            return_value=[(None, None, None, None, ("10.9.8.7", 443))],
        ):
            resp = await client.post(
                "/api/v1/webhooks/subscriptions",
                json={
                    "url": "https://evil-rebind.example/hook",
                    "events": ["company.created"],
                    "secret": SECRET,
                },
            )
    assert resp.status_code == 400, resp.text
