"""HTTP regression for Phase 0 criterion 1.1 / GA-P0-SEC-01.

Decision Center by-ID routes must return 404 when the authenticated tenant
does not own the decision — never leak another tenant's decision, audit, or
feedback. Service/repo filters already cover this; this file proves the
router + auth dependency chain enforces it end-to-end over ASGI.

Does not modify get_db() / set_config (DEC-085).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.dependencies import verify_token
from app.main import app
from domains.decision_center.repository import InMemoryDecisionCenterRepository
from domains.decision_center.service import DecisionCenterService

TENANT_A = "idor-tenant-a"
TENANT_B = "idor-tenant-b"
USER_A = "idor-user-a"
USER_B = "idor-user-b"


@asynccontextmanager
async def _client_as(tenant_id: str, user_id: str, svc: DecisionCenterService) -> AsyncIterator[AsyncClient]:
    async def override_verify_token() -> dict[str, str]:
        return {"sub": user_id, "tenant_id": tenant_id}

    previous_dc = getattr(app.state, "decision_center_service", None)
    app.state.decision_center_service = svc
    app.dependency_overrides[verify_token] = override_verify_token

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(verify_token, None)
        if previous_dc is None:
            if hasattr(app.state, "decision_center_service"):
                delattr(app.state, "decision_center_service")
        else:
            app.state.decision_center_service = previous_dc


@pytest_asyncio.fixture
async def dc_service() -> DecisionCenterService:
    return DecisionCenterService(repository=InMemoryDecisionCenterRepository())


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_decision_cross_tenant_returns_404(dc_service: DecisionCenterService) -> None:
    """GA-P0-SEC-01: tenant B cannot GET tenant A's decision by ID."""
    decision = await dc_service.create_decision(
        domain="pipeline",
        decision_type="deal_scoring",
        entity_id="co-idor-1",
        entity_type="company",
        decision="pursue",
        confidence=0.91,
        reasoning="secret-victim-reasoning",
        provider="rule_engine",
        tenant_id=TENANT_A,
    )

    async with _client_as(TENANT_A, USER_A, dc_service) as client_a:
        own = await client_a.get(f"/api/v1/decisions/{decision.id}")
        assert own.status_code == 200, own.text
        assert own.json()["reasoning"] == "secret-victim-reasoning"

    async with _client_as(TENANT_B, USER_B, dc_service) as client_b:
        leaked = await client_b.get(f"/api/v1/decisions/{decision.id}")
        assert leaked.status_code == 404, leaked.text
        assert "secret-victim-reasoning" not in leaked.text


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_audit_and_feedback_cross_tenant_returns_404(
    dc_service: DecisionCenterService,
) -> None:
    decision = await dc_service.create_decision(
        domain="pipeline",
        decision_type="deal_scoring",
        entity_id="co-idor-2",
        entity_type="company",
        decision="pursue",
        confidence=0.88,
        reasoning="audit-secret",
        provider="rule_engine",
        tenant_id=TENANT_A,
    )
    await dc_service.create_audit(
        decision_id=decision.id,
        input_context={"secret": True},
        reasoning_steps=[{"step": 1, "description": "private"}],
        confidence_breakdown={"intent": 0.9},
        provider_used="rule_engine",
        alternatives_considered=[],
        tenant_id=TENANT_A,
    )
    await dc_service.submit_feedback(decision.id, "up", TENANT_A, comment="keep-private")

    async with _client_as(TENANT_B, USER_B, dc_service) as client_b:
        audit = await client_b.get(f"/api/v1/decisions/{decision.id}/audit")
        assert audit.status_code == 404, audit.text
        assert "private" not in audit.text

        feedback_get = await client_b.get(f"/api/v1/decisions/{decision.id}/feedback")
        assert feedback_get.status_code == 200, feedback_get.text
        assert feedback_get.json() == []

        feedback_post = await client_b.post(
            f"/api/v1/decisions/{decision.id}/feedback",
            json={"rating": "down", "comment": "attacker"},
        )
        assert feedback_post.status_code == 404, feedback_post.text


@pytest.mark.contract
@pytest.mark.asyncio
async def test_list_decisions_excludes_other_tenant(dc_service: DecisionCenterService) -> None:
    await dc_service.create_decision(
        domain="pipeline",
        decision_type="deal_scoring",
        entity_id="co-a",
        entity_type="company",
        decision="pursue",
        confidence=0.7,
        reasoning="tenant-a-only",
        provider="rule_engine",
        tenant_id=TENANT_A,
    )

    async with _client_as(TENANT_B, USER_B, dc_service) as client_b:
        resp = await client_b.get("/api/v1/decisions")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []
        assert "tenant-a-only" not in resp.text
