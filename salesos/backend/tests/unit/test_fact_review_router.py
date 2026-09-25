"""HTTP contract tests for the authenticated FactRecorder review API."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import ValidationError

import app.modules.facts.router as facts_api
from app.dependencies import (
    get_current_tenant_id,
    get_current_user_id,
    get_current_user_role,
    get_db_session,
    verify_token,
)
from app.modules.facts.router import (
    AgentReachProposalActor,
    FactProposalRequest,
    get_agent_reach_proposal_actor,
    router,
)
from domains.commercial.evidence.contracts.models import ConfidenceLevel, EvidenceKind
from sdk.permissions import PermissionAction, PermissionRegistry, Role

TENANT = uuid.UUID("ab09529e-3e80-413b-af35-d06bf70471cd")
FACT = uuid.UUID("9d564718-f301-40b8-9b42-8fd48fd75c8a")
REVIEWER = "verified-reviewer-42"
PAGE_LIMIT = 20


class Result:
    def __init__(self, value: Any = None, rows: list[Any] | None = None):
        self.value = value
        self.rows = rows or []

    def scalar_one_or_none(self):
        return self.value

    def scalars(self):
        return self

    def all(self):
        return self.rows


class FakeSession:
    def __init__(self, results: list[Result]):
        self.results = list(results)
        self.added: list[Any] = []

    async def execute(self, _statement):
        assert self.results, "unexpected database query"
        return self.results.pop(0)

    def add(self, instance):
        self.added.append(instance)


def client_for(session: FakeSession, *, role: str = "admin") -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1", dependencies=[Depends(verify_token)])
    app.dependency_overrides[verify_token] = lambda: {"sub": REVIEWER, "tenant_id": str(TENANT)}
    app.dependency_overrides[get_current_user_id] = lambda: REVIEWER
    app.dependency_overrides[get_current_user_role] = lambda: role
    app.dependency_overrides[get_current_tenant_id] = lambda: str(TENANT)
    app.dependency_overrides[get_db_session] = lambda: session
    app.dependency_overrides[get_agent_reach_proposal_actor] = lambda: AgentReachProposalActor(
        str(TENANT), REVIEWER, "human"
    )
    for dependency in router.dependencies:
        app.dependency_overrides[dependency.dependency] = lambda: None
    for route in router.routes:
        for dependency in route.dependant.dependencies:
            if dependency.call not in {
                get_current_user_id,
                get_current_user_role,
                get_current_tenant_id,
                get_db_session,
                get_agent_reach_proposal_actor,
            }:
                app.dependency_overrides[dependency.call] = lambda: None
    return TestClient(app)


def test_pending_proposal_list_is_paginated_and_contains_evidence():
    fact = SimpleNamespace(
        id=FACT,
        subject_type="company",
        subject_id=uuid.uuid4(),
        field_name="city",
        proposed_value="Riyadh",
        value_hash="a" * 64,
        status="PROPOSED",
        evidence_band="verified",
        score=0.98,
        decision_reason="proposal_only:verified_primary_evidence",
        actor_type="agent",
        actor_id="agent-run-1",
        evidence_snapshot=[{"source": {"source_name": "Registry"}}],
        created_at=datetime.now(UTC),
        reviewer_id=None,
        reviewed_at=None,
    )
    session = FakeSession([Result(str(TENANT)), Result(rows=[fact])])
    with client_for(session) as client:
        response = client.get(f"/api/v1/facts/proposals?limit={PAGE_LIMIT}&offset=0")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["limit"] == PAGE_LIMIT and body["offset"] == 0
    assert body["items"][0]["id"] == str(FACT)
    assert body["items"][0]["evidence_snapshot"][0]["source"]["source_name"] == "Registry"


def test_manual_proposal_endpoint_uses_jwt_actor_and_rejects_spoofed_identity(monkeypatch):
    recorded: dict[str, Any] = {}

    class ProposalServiceDouble:
        def __init__(self, _session):
            pass

        async def propose(self, **kwargs):
            recorded.update(kwargs)
            return SimpleNamespace(fact_id=FACT, status="PROPOSED", created=True)

    monkeypatch.setattr(facts_api, "FactProposalService", ProposalServiceDouble)
    payload = {
        "subject_type": "company",
        "subject_id": str(uuid.uuid4()),
        "field_name": "city",
        "proposed_value": "Riyadh",
        "evidence": [
            {
                "id": "manual:registry:1",
                "evidence_type": "market_signal",
                "source": {
                    "source_domain": "registry",
                    "source_type": "official_record",
                    "source_id": "1",
                    "source_name": "Registry",
                },
                "description": "Company registry lists the city.",
                "confidence": 0.95,
                "confidence_level": "high",
                "evidence_kind": "source.official_registry",
                "data": {"city": "Riyadh"},
                "recorded_at": "2026-09-21T12:00:00Z",
            }
        ],
        "idempotency_token": "human-proposal-1",
    }
    with client_for(FakeSession([])) as client:
        response = client.post("/api/v1/facts/proposals", json=payload)
        spoofed = client.post(
            "/api/v1/facts/proposals",
            json=payload | {"actor_id": "forged-reviewer", "actor_type": "agent"},
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "id": str(FACT),
        "status": "PROPOSED",
        "created": True,
        "crm_applied": False,
    }
    assert recorded["tenant_id"] == str(TENANT)
    assert recorded["actor_type"] == "human" and recorded["actor_id"] == REVIEWER
    assert recorded["evidence"][0].evidence_kind is EvidenceKind.CITED_CLAIM
    assert recorded["evidence"][0].confidence_level is ConfidenceLevel.UNKNOWN
    assert spoofed.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_agent_reach_proposal_endpoint_uses_verified_actor_and_is_proposal_only(monkeypatch):
    recorded: dict[str, Any] = {}

    class BridgeDouble:
        def __init__(self, _session):
            pass

        async def propose_from_evidence(self, **kwargs):
            recorded.update(kwargs)
            return SimpleNamespace(fact_id=FACT, status="PROPOSED", created=True)

    monkeypatch.setattr(facts_api, "AgentReachFactProposalBridge", BridgeDouble)
    payload = {
        "company_id": str(uuid.uuid4()),
        "evidence_id": str(uuid.uuid4()),
        "field_name": "city",
        "proposed_value": "Riyadh",
    }
    with client_for(FakeSession([])) as client:
        response = client.post("/api/v1/facts/proposals/from-agent-reach", json=payload)
        spoofed = client.post(
            "/api/v1/facts/proposals/from-agent-reach",
            json=payload | {"requested_by": "forged-reviewer"},
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "id": str(FACT),
        "status": "PROPOSED",
        "created": True,
        "crm_applied": False,
    }
    assert recorded["tenant_id"] == str(TENANT)
    assert recorded["requested_by"] == REVIEWER
    assert recorded["company_id"] == uuid.UUID(payload["company_id"])
    assert recorded["evidence_id"] == uuid.UUID(payload["evidence_id"])
    assert spoofed.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_service_principal_jwt_cannot_use_human_proposal_endpoint():
    payload = {
        "subject_type": "company",
        "subject_id": str(uuid.uuid4()),
        "field_name": "city",
        "proposed_value": "Riyadh",
        "evidence": [
            {
                "id": "manual:service-role:1",
                "evidence_type": "market_signal",
                "source": {
                    "source_domain": "example.com",
                    "source_type": "public_page",
                    "source_id": "1",
                    "source_name": "Example",
                },
                "description": "A test-only cited claim.",
                "confidence": 0.2,
                "confidence_level": "unknown",
                "evidence_kind": "web.cited_claim",
                "data": {},
                "recorded_at": "2026-09-21T12:00:00Z",
            }
        ],
        "idempotency_token": "service-jwt-must-not-be-human",
    }
    with client_for(FakeSession([]), role="agent_reach_service") as client:
        response = client.post("/api/v1/facts/proposals", json=payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "scoped evidence proposal route" in response.json()["detail"]


def test_proposal_request_contract_rejects_client_supplied_actor():
    with pytest.raises(ValidationError):
        FactProposalRequest.model_validate(
            {
                "subject_type": "company",
                "subject_id": str(uuid.uuid4()),
                "field_name": "city",
                "proposed_value": "Riyadh",
                "evidence": [],
                "idempotency_token": "token",
                "actor_id": "spoofed",
            }
        )


def test_decision_endpoint_uses_verified_user_and_reports_no_crm_apply():
    fact = SimpleNamespace(
        id=FACT,
        status="PROPOSED",
        actor_type="agent",
        actor_id="agent-run-1",
        reviewer_id=None,
        reviewed_at=None,
    )
    session = FakeSession([Result(str(TENANT)), Result(fact)])
    with client_for(session) as client:
        response = client.post(
            f"/api/v1/facts/{FACT}/decision",
            json={"decision": "approve", "reason": "Checked source and subject."},
        )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "APPROVED" and body["changed"] is True
    assert body["crm_applied"] is False
    assert fact.reviewer_id == REVIEWER
    assert len(session.added) == 1 and session.added[0].actor_id == REVIEWER


def test_review_routes_are_registered_with_read_and_update_permissions():
    routes = {(route.path, method): route for route in router.routes for method in route.methods}
    expected = {
        ("/facts/proposals", "GET"): PermissionAction.READ,
        ("/facts/proposals", "POST"): PermissionAction.CREATE,
        ("/facts/{fact_id}/decision", "POST"): PermissionAction.UPDATE,
    }
    assert expected.keys() <= routes.keys()
    for route_key, action in expected.items():
        permissions = [
            dependency.call
            for dependency in routes[route_key].dependant.dependencies
            if dependency.call.__name__ == "_require_permission"
        ]
        assert len(permissions) == 1
        captured = [
            cell.cell_contents
            for dependency in permissions
            for cell in (dependency.__closure__ or [])
        ]
        assert action in captured and "master-data-review" in captured

    service_route = routes[("/facts/proposals/from-agent-reach", "POST")]
    assert any(
        dependency.call is get_agent_reach_proposal_actor
        for dependency in service_route.dependant.dependencies
    )


@pytest.mark.asyncio
async def test_agent_reach_service_principal_requires_exact_scopes_and_service_role():
    from starlette.requests import Request

    PermissionRegistry.register_role(
        Role(
            "agent_reach_service",
            permissions=set(PermissionRegistry.default_roles()["agent_reach_service"]),
        )
    )
    user_id = uuid.uuid4()
    scopes = ["agent_reach:read", "master-data-review:create"]
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/facts/proposals/from-agent-reach",
        "headers": [],
        "state": {
            "api_key_authenticated": True,
            "api_key_id": "minder-key-1",
            "api_key_user_id": str(user_id),
            "api_key_tenant_id": str(TENANT),
            "api_key_scopes": scopes,
        },
    }

    class AuthSession:
        async def scalar(self, _statement):
            return SimpleNamespace(
                id=user_id,
                tenant_id=TENANT,
                role="agent_reach_service",
                is_active=True,
                deleted_at=None,
            )

    actor = await get_agent_reach_proposal_actor(
        request=Request(scope),
        authorization=None,
        x_api_key="sos_test-key",
        x_tenant_id=str(TENANT),
        db=AuthSession(),
    )
    assert actor == AgentReachProposalActor(
        str(TENANT), f"agent_reach_service:{user_id}:api_key:minder-key-1", "agent"
    )

    scope["state"]["api_key_scopes"] = scopes + ["company:delete"]
    with pytest.raises(HTTPException) as denied_scopes:
        await get_agent_reach_proposal_actor(
            request=Request(scope),
            authorization=None,
            x_api_key="sos_test-key",
            x_tenant_id=str(TENANT),
            db=AuthSession(),
        )
    assert getattr(denied_scopes.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_agent_reach_service_principal_requires_tenant_header():
    from starlette.requests import Request

    PermissionRegistry.register_role(
        Role(
            "agent_reach_service",
            permissions=set(PermissionRegistry.default_roles()["agent_reach_service"]),
        )
    )
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/facts/proposals/from-agent-reach",
            "headers": [],
            "state": {
                "api_key_authenticated": True,
                "api_key_id": "minder-key-1",
                "api_key_user_id": str(uuid.uuid4()),
                "api_key_tenant_id": str(TENANT),
                "api_key_scopes": ["agent_reach:read", "master-data-review:create"],
            },
        }
    )

    class UnusedSession:
        async def scalar(self, _statement):
            pytest.fail("tenant mismatch must fail before user lookup")

    with pytest.raises(HTTPException) as denied_tenant:
        await get_agent_reach_proposal_actor(
            request=request,
            authorization=None,
            x_api_key="sos_test-key",
            x_tenant_id=None,
            db=UnusedSession(),
        )
    assert getattr(denied_tenant.value, "status_code", None) == 403
