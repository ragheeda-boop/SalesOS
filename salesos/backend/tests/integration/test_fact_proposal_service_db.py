"""PostgreSQL integration proof for review-only fact proposal persistence.

The test pins its URL to salesos_test and wraps all fixture rows in a rolled
back transaction. It intentionally avoids the shared create_all/drop_all test
fixture because salesos_test also contains Master Data review datasets.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.common.middleware import TenantContextMiddleware
from app.config import settings
from app.database import apply_tenant_guc
from app.dependencies import (
    get_current_tenant_id,
    get_current_user_id,
    get_current_user_role,
    get_db_session,
)
from app.modules.api_keys.middleware import ApiKeyMiddleware
from app.modules.api_keys.models import ApiKey
from app.modules.api_keys.service import _hash_key
from app.modules.company.models import Company
from app.modules.facts.models import CanonicalFact, CanonicalFactEvent, EvidenceRecord, FactEvidence
from app.modules.facts.router import router as facts_router
from app.modules.facts.service import FactPolicyRejected, FactProposalService
from app.modules.identity.models import Tenant, User
from domains.commercial.evidence.contracts.models import (
    ConfidenceLevel,
    EvidenceBand,
    EvidenceItem,
    EvidenceKind,
    EvidenceSource,
    EvidenceType,
)

CITED_CLAIM_SCORE = 0.4
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_CONFLICT = 409
_INTEGRATION_API_KEY = "sos_" + "a" * 64
_OVERPRIVILEGED_INTEGRATION_API_KEY = "sos_" + "b" * 64


def _fact_api_app(session: AsyncSession, context: dict[str, str]) -> FastAPI:
    app = FastAPI()
    app.include_router(facts_router, prefix="/api/v1")
    app.dependency_overrides[get_current_tenant_id] = lambda: context["tenant_id"]
    app.dependency_overrides[get_current_user_id] = lambda: context["user_id"]
    app.dependency_overrides[get_current_user_role] = lambda: "admin"
    app.dependency_overrides[get_db_session] = lambda: session
    for route in facts_router.routes:
        for dependency in route.dependant.dependencies:
            if dependency.call.__name__ in {"_rate_limit", "_require_permission"}:
                app.dependency_overrides[dependency.call] = lambda: None
    return app


async def _api_request(
    app: FastAPI,
    method: str,
    path: str,
    *,
    json: dict | None = None,
    headers: dict[str, str] | None = None,
):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        return await client.request(method, path, json=json, headers=headers)


class _ScopedApiKeySession:
    """RLS-scoped session factory used by the real API-key middleware test."""

    def __init__(self, connection):
        self.session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

    async def __aenter__(self):
        await apply_tenant_guc(self.session)
        return self.session

    async def __aexit__(self, *_args):
        await self.session.close()
        return False


def _fact_api_app_with_real_auth(
    session: AsyncSession,
    *,
    connection,
) -> FastAPI:
    """Use signed access tokens, database roles, and request tenant context."""
    app = FastAPI()
    # Add in reverse order because Starlette runs the last-added middleware first.
    app.add_middleware(ApiKeyMiddleware)
    app.add_middleware(TenantContextMiddleware)
    app.state.db_session_factory = lambda: _ScopedApiKeySession(connection)
    app.include_router(facts_router, prefix="/api/v1")

    async def scoped_session():
        await apply_tenant_guc(session)
        yield session

    app.dependency_overrides[get_db_session] = scoped_session
    for route in facts_router.routes:
        for dependency in route.dependant.dependencies:
            if dependency.call.__name__ == "_rate_limit":
                app.dependency_overrides[dependency.call] = lambda: None
    return app


@pytest.mark.asyncio
async def test_fact_proposal_round_trip_is_tenant_scoped_and_never_updates_company() -> None:  # noqa: PLR0915
    test_url = make_url(settings.app_database_url).set(database="salesos_test")
    engine = create_async_engine(test_url, pool_pre_ping=True, connect_args={"command_timeout": 10})
    async with engine.connect() as connection:
        database_name = await connection.scalar(text("SELECT current_database()"))
        assert database_name == "salesos_test"
        role_flags = await connection.execute(
            text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")
        )
        assert role_flags.one() == (False, False)
        outer = connection.get_transaction()
        assert outer is not None
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            tenant = Tenant(name="Fact Recorder Test", slug=f"fact-recorder-{uuid.uuid4()}")
            session.add(tenant)
            await session.flush()

            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant.id)},
            )
            company = Company(tenant_id=tenant.id, name_ar="Fact Recorder Integration Test")
            session.add(company)
            await session.flush()
            api_context = {"tenant_id": str(tenant.id), "user_id": "verified-reviewer-1"}
            api_app = _fact_api_app(session, api_context)

            evidence = EvidenceItem(
                id=f"integration:{uuid.uuid4()}",
                evidence_type=EvidenceType.MARKET_SIGNAL,
                source=EvidenceSource(
                    "registry", "official_record", "test-record-1", "Test Registry"
                ),
                description="Test-only official source for a temporary company.",
                confidence=0.01,
                confidence_level=ConfidenceLevel.HIGH,
                evidence_kind=EvidenceKind.OFFICIAL_REGISTRY,
                data={"city": "Riyadh"},
                recorded_at=datetime.now(UTC),
            )
            service = FactProposalService(session)
            kwargs = {
                "tenant_id": tenant.id,
                "subject_type": "company",
                "subject_id": company.id,
                "field_name": "city",
                "proposed_value": "Riyadh",
                "evidence": [evidence],
                "idempotency_token": f"integration:{uuid.uuid4()}",
                "actor_type": "agent",
                "actor_id": "integration-test",
            }
            first = await service.propose(**kwargs)
            retry = await service.propose(**kwargs)
            assert first.status == "PROPOSED" and first.created is True
            assert retry.fact_id == first.fact_id and retry.created is False
            proposal_list = await _api_request(api_app, "GET", "/api/v1/facts/proposals")
            assert proposal_list.status_code == HTTP_OK
            assert any(item["id"] == str(first.fact_id) for item in proposal_list.json()["items"])

            stored_company = await session.scalar(select(Company).where(Company.id == company.id))
            assert stored_company is not None
            assert stored_company.city is None  # Proposing must not mutate canonical CRM data.
            assert (
                await session.scalar(
                    select(CanonicalFact.id).where(CanonicalFact.id == first.fact_id)
                )
                == first.fact_id
            )
            assert (
                await session.scalar(
                    select(FactEvidence.fact_id).where(FactEvidence.fact_id == first.fact_id)
                )
                == first.fact_id
            )
            assert (
                await session.scalar(
                    select(CanonicalFactEvent.id).where(
                        CanonicalFactEvent.fact_id == first.fact_id,
                        CanonicalFactEvent.event_type == "PROPOSED",
                    )
                )
                is not None
            )
            assert (
                await session.scalar(
                    select(EvidenceRecord.id).where(EvidenceRecord.tenant_id == tenant.id)
                )
                is not None
            )

            approved_response = await _api_request(
                api_app,
                "POST",
                f"/api/v1/facts/{first.fact_id}/decision",
                json={
                    "decision": "approve",
                    "reason": "Confirmed against the authoritative company record.",
                },
            )
            approval_retry = await _api_request(
                api_app,
                "POST",
                f"/api/v1/facts/{first.fact_id}/decision",
                json={
                    "decision": "approve",
                    "reason": "Confirmed against the authoritative company record.",
                },
            )
            assert approved_response.status_code == HTTP_OK
            assert approved_response.json()["status"] == "APPROVED"
            assert approved_response.json()["changed"] is True
            assert approved_response.json()["crm_applied"] is False
            assert (
                approval_retry.status_code == HTTP_OK and approval_retry.json()["changed"] is False
            )
            conflict = await _api_request(
                api_app,
                "POST",
                f"/api/v1/facts/{first.fact_id}/decision",
                json={
                    "decision": "reject",
                    "reason": "A conflicting retry must not reverse a decision.",
                },
            )
            assert conflict.status_code == HTTP_CONFLICT
            assert (
                await session.scalar(
                    select(func.count())
                    .select_from(CanonicalFactEvent)
                    .where(
                        CanonicalFactEvent.fact_id == first.fact_id,
                        CanonicalFactEvent.event_type == "REVIEW_DECIDED",
                    )
                )
                == 1
            )

            # Approval is a recorded review decision only. The CRM value remains unchanged.
            stored_company = await session.scalar(select(Company).where(Company.id == company.id))
            assert stored_company is not None and stored_company.city is None

            dismissed_evidence = EvidenceItem(
                id=f"integration:{uuid.uuid4()}",
                evidence_type=EvidenceType.MARKET_SIGNAL,
                source=EvidenceSource(
                    "registry", "official_record", "test-record-2", "Test Registry"
                ),
                description="Test-only official source for a temporary company in Jeddah.",
                confidence=0.01,
                confidence_level=ConfidenceLevel.HIGH,
                evidence_kind=EvidenceKind.OFFICIAL_REGISTRY,
                data={"city": "Jeddah"},
                recorded_at=datetime.now(UTC),
            )
            api_context["user_id"] = "verified-proposer-2"
            second_response = await _api_request(
                api_app,
                "POST",
                "/api/v1/facts/proposals",
                json={
                    "subject_type": "company",
                    "subject_id": str(company.id),
                    "field_name": "city",
                    "proposed_value": "Jeddah",
                    "evidence": [
                        {
                            "id": dismissed_evidence.id,
                            "evidence_type": dismissed_evidence.evidence_type.value,
                            "source": {
                                "source_domain": dismissed_evidence.source.source_domain,
                                "source_type": dismissed_evidence.source.source_type,
                                "source_id": dismissed_evidence.source.source_id,
                                "source_name": dismissed_evidence.source.source_name,
                            },
                            "description": dismissed_evidence.description,
                            "confidence": dismissed_evidence.confidence,
                            "confidence_level": dismissed_evidence.confidence_level.value,
                            "evidence_kind": dismissed_evidence.evidence_kind.value,
                            "data": dismissed_evidence.data,
                            "recorded_at": dismissed_evidence.recorded_at.isoformat(),
                        }
                    ],
                    "idempotency_token": f"integration:{uuid.uuid4()}",
                },
            )
            assert second_response.status_code == HTTP_OK
            second_fact_id = second_response.json()["id"]
            stored_second = await session.get(CanonicalFact, uuid.UUID(second_fact_id))
            assert stored_second is not None
            assert stored_second.actor_type == "human"
            assert stored_second.actor_id == "verified-proposer-2"
            assert stored_second.score == CITED_CLAIM_SCORE
            assert stored_second.evidence_band == EvidenceBand.POSSIBLE.value
            assert (
                stored_second.evidence_snapshot[0]["evidence_kind"]
                == EvidenceKind.CITED_CLAIM.value
            )
            assert (
                stored_second.evidence_snapshot[0]["confidence_level"]
                == ConfidenceLevel.UNKNOWN.value
            )

            api_context["user_id"] = "verified-reviewer-1"
            dismissal_response = await _api_request(
                api_app,
                "POST",
                f"/api/v1/facts/{second_fact_id}/decision",
                json={"decision": "dismiss", "reason": "The proposed value is not current."},
            )
            assert dismissal_response.status_code == HTTP_OK
            assert dismissal_response.json()["status"] == "DISMISSED"
            re_proposal = await _api_request(
                api_app,
                "POST",
                "/api/v1/facts/proposals",
                json={
                    "subject_type": "company",
                    "subject_id": str(company.id),
                    "field_name": "city",
                    "proposed_value": "Jeddah",
                    "evidence": [
                        {
                            "id": dismissed_evidence.id,
                            "evidence_type": dismissed_evidence.evidence_type.value,
                            "source": {
                                "source_domain": dismissed_evidence.source.source_domain,
                                "source_type": dismissed_evidence.source.source_type,
                                "source_id": dismissed_evidence.source.source_id,
                                "source_name": dismissed_evidence.source.source_name,
                            },
                            "description": dismissed_evidence.description,
                            "confidence": dismissed_evidence.confidence,
                            "confidence_level": dismissed_evidence.confidence_level.value,
                            "evidence_kind": dismissed_evidence.evidence_kind.value,
                            "data": dismissed_evidence.data,
                            "recorded_at": dismissed_evidence.recorded_at.isoformat(),
                        }
                    ],
                    "idempotency_token": f"dismissed:{uuid.uuid4()}",
                },
            )
            assert re_proposal.status_code == HTTP_CONFLICT

            other_tenant = Tenant(name="Other Fact Tenant", slug=f"fact-other-{uuid.uuid4()}")
            session.add(other_tenant)
            await session.flush()
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(other_tenant.id)},
            )
            with pytest.raises(FactPolicyRejected, match="authenticated database tenant"):
                await service.propose(
                    **{**kwargs, "idempotency_token": f"wrong-scope:{uuid.uuid4()}"}
                )
            with pytest.raises(FactPolicyRejected, match="authenticated tenant"):
                await service.propose(
                    **{
                        **kwargs,
                        "tenant_id": other_tenant.id,
                        "idempotency_token": f"cross-tenant:{uuid.uuid4()}",
                    }
                )
        finally:
            await session.close()
            await outer.rollback()
    await engine.dispose()


@pytest.mark.asyncio
async def test_fact_review_api_uses_signed_jwt_rbac_and_tenant_rls(  # noqa: PLR0915
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Exercise the actual auth, permission, tenant, and review dependencies."""
    from app.modules.identity import jwks
    from app.modules.identity.service import create_access_token

    # Generate an isolated test keypair. Never load or write the application's
    # normal JWKS key files from this integration proof.
    monkeypatch.setattr(jwks, "_RSA_KEY_DIR", str(tmp_path))
    monkeypatch.setattr(jwks, "_RSA_PRIVATE_PATH", str(tmp_path / "rsa_private.pem"))
    monkeypatch.setattr(jwks, "_RSA_PUBLIC_PATH", str(tmp_path / "rsa_public.pem"))
    monkeypatch.setattr(jwks, "_private_key", None)
    monkeypatch.setattr(jwks, "_public_key", None)
    monkeypatch.setattr(jwks, "_jwks_cache", None)

    test_url = make_url(settings.app_database_url).set(database="salesos_test")
    engine = create_async_engine(test_url, pool_pre_ping=True, connect_args={"command_timeout": 10})
    async with engine.connect() as connection:
        assert await connection.scalar(text("SELECT current_database()")) == "salesos_test"
        role_flags = await connection.execute(
            text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")
        )
        assert role_flags.one() == (False, False)
        outer = connection.get_transaction()
        assert outer is not None
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            tenant_a = Tenant(name="JWT Fact Tenant A", slug=f"jwt-fact-a-{uuid.uuid4()}")
            tenant_b = Tenant(name="JWT Fact Tenant B", slug=f"jwt-fact-b-{uuid.uuid4()}")
            session.add_all([tenant_a, tenant_b])
            await session.flush()

            admin_a = User(
                tenant_id=tenant_a.id,
                email=f"fact-admin-a-{uuid.uuid4().hex[:8]}@test.invalid",
                password_hash="unused-integration-hash",
                full_name="Fact Admin A",
                role="admin",
                is_active=True,
            )
            admin_a_reviewer = User(
                tenant_id=tenant_a.id,
                email=f"fact-reviewer-a-{uuid.uuid4().hex[:8]}@test.invalid",
                password_hash="unused-integration-hash",
                full_name="Fact Reviewer A",
                role="admin",
                is_active=True,
            )
            regular_a = User(
                tenant_id=tenant_a.id,
                email=f"fact-user-a-{uuid.uuid4().hex[:8]}@test.invalid",
                password_hash="unused-integration-hash",
                full_name="Fact User A",
                role="user",
                is_active=True,
            )
            service_a = User(
                tenant_id=tenant_a.id,
                email=f"fact-agent-reach-service-{uuid.uuid4().hex[:8]}@test.invalid",
                password_hash="unused-integration-hash",
                full_name="Agent Reach Service A",
                role="agent_reach_service",
                is_active=True,
            )
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_a.id)},
            )
            company_a = Company(tenant_id=tenant_a.id, name_ar="JWT Fact Company A")
            session.add_all([admin_a, admin_a_reviewer, regular_a, service_a, company_a])
            await session.flush()
            session.add(
                ApiKey(
                    id="minder-integration-key-id",
                    tenant_id=tenant_a.id,
                    user_id=service_a.id,
                    name="Minder integration fixture",
                    key_prefix=_INTEGRATION_API_KEY[:10],
                    key_hash=_hash_key(_INTEGRATION_API_KEY),
                    scopes="agent_reach:read,master-data-review:create",
                    is_revoked=False,
                )
            )
            session.add(
                ApiKey(
                    id="minder-overprivileged-key-id",
                    tenant_id=tenant_a.id,
                    user_id=service_a.id,
                    name="Minder overprivileged fixture",
                    key_prefix=_OVERPRIVILEGED_INTEGRATION_API_KEY[:10],
                    key_hash=_hash_key(_OVERPRIVILEGED_INTEGRATION_API_KEY),
                    scopes="agent_reach:read,master-data-review:create,company:delete",
                    is_revoked=False,
                )
            )
            await session.flush()

            admin_b = User(
                tenant_id=tenant_b.id,
                email=f"fact-admin-b-{uuid.uuid4().hex[:8]}@test.invalid",
                password_hash="unused-integration-hash",
                full_name="Fact Admin B",
                role="admin",
                is_active=True,
            )
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_b.id)},
            )
            company_b = Company(tenant_id=tenant_b.id, name_ar="JWT Fact Company B")
            session.add_all([admin_b, company_b])
            await session.flush()

            proposal_evidence = EvidenceItem(
                id=f"jwt-integration:{uuid.uuid4()}",
                evidence_type=EvidenceType.MARKET_SIGNAL,
                source=EvidenceSource(
                    "registry", "official_record", "jwt-test-record", "Test Registry"
                ),
                description="Temporary evidence for authenticated Fact Review integration.",
                confidence=0.9,
                confidence_level=ConfidenceLevel.HIGH,
                evidence_kind=EvidenceKind.OFFICIAL_REGISTRY,
                data={"city": "Riyadh"},
                recorded_at=datetime.now(UTC),
            )
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_a.id)},
            )
            fact_a = await FactProposalService(session).propose(
                tenant_id=tenant_a.id,
                subject_type="company",
                subject_id=company_a.id,
                field_name="city",
                proposed_value="Riyadh",
                evidence=[proposal_evidence],
                idempotency_token=f"jwt-a:{uuid.uuid4()}",
                actor_type="agent",
                actor_id="jwt-integration-producer",
            )
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_b.id)},
            )
            fact_b = await FactProposalService(session).propose(
                tenant_id=tenant_b.id,
                subject_type="company",
                subject_id=company_b.id,
                field_name="city",
                proposed_value="Jeddah",
                evidence=[proposal_evidence],
                idempotency_token=f"jwt-b:{uuid.uuid4()}",
                actor_type="agent",
                actor_id="jwt-integration-producer",
            )

            app = _fact_api_app_with_real_auth(
                session,
                connection=connection,
            )
            service_token_headers = {
                "Authorization": "Bearer "
                f"{create_access_token(str(service_a.id), str(tenant_a.id))}",
                "X-Tenant-Id": str(tenant_a.id),
            }
            headers_a = {
                "Authorization": "Bearer "
                f"{create_access_token(str(admin_a.id), str(tenant_a.id))}",
                "X-Tenant-Id": str(tenant_a.id),
            }
            headers_a_reviewer = {
                "Authorization": "Bearer "
                f"{create_access_token(str(admin_a_reviewer.id), str(tenant_a.id))}",
                "X-Tenant-Id": str(tenant_a.id),
            }
            headers_regular_a = {
                "Authorization": "Bearer "
                f"{create_access_token(str(regular_a.id), str(tenant_a.id))}",
                "X-Tenant-Id": str(tenant_a.id),
            }
            headers_b = {
                "Authorization": "Bearer "
                f"{create_access_token(str(admin_b.id), str(tenant_b.id))}",
                "X-Tenant-Id": str(tenant_b.id),
            }

            agent_evidence_id = uuid.uuid4()
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_a.id)},
            )
            await session.execute(
                text(
                    """
                    INSERT INTO agent_evidence
                        (id, tenant_id, company_name, evidence_type, channel, source_url,
                         title, summary, raw_data, confidence, fingerprint, collected_at,
                         expires_at, metadata)
                    VALUES
                        (:id, :tenant_id, :company_name, 'web_search', 'web',
                         'https://www.example.com/company', 'Company location',
                             'The public company page lists Jeddah as its location and reports 42 employees.',
                         CAST(:raw_data AS jsonb), 0.95, :fingerprint, :collected_at,
                         NULL, CAST('{}' AS jsonb))
                    """
                ),
                {
                    "id": str(agent_evidence_id),
                    "tenant_id": str(tenant_a.id),
                    "company_name": company_a.name_ar,
                    "raw_data": '{"private_fixture_payload":"must not be copied"}',
                    "fingerprint": uuid.uuid4().hex + uuid.uuid4().hex,
                    "collected_at": datetime.now(UTC),
                },
            )

            unauthenticated = await _api_request(app, "GET", "/api/v1/facts/proposals")
            assert unauthenticated.status_code == HTTP_UNAUTHORIZED
            denied_read = await _api_request(
                app, "GET", "/api/v1/facts/proposals", headers=headers_regular_a
            )
            assert denied_read.status_code == HTTP_FORBIDDEN
            denied_create = await _api_request(
                app,
                "POST",
                "/api/v1/facts/proposals",
                headers=headers_regular_a,
                json={"subject_type": "company"},
            )
            assert denied_create.status_code == HTTP_FORBIDDEN
            denied_agent_reach = await _api_request(
                app,
                "POST",
                "/api/v1/facts/proposals/from-agent-reach",
                headers=headers_regular_a,
                json={
                    "company_id": str(company_a.id),
                    "evidence_id": str(agent_evidence_id),
                    "field_name": "city",
                    "proposed_value": "Jeddah",
                },
            )
            assert denied_agent_reach.status_code == HTTP_FORBIDDEN
            mismatched_tenant = await _api_request(
                app,
                "GET",
                "/api/v1/facts/proposals",
                headers={**headers_a, "X-Tenant-Id": str(tenant_b.id)},
            )
            assert mismatched_tenant.status_code == HTTP_FORBIDDEN

            list_a = await _api_request(app, "GET", "/api/v1/facts/proposals", headers=headers_a)
            list_b = await _api_request(app, "GET", "/api/v1/facts/proposals", headers=headers_b)
            assert list_a.status_code == list_b.status_code == HTTP_OK
            ids_a = {item["id"] for item in list_a.json()["items"]}
            ids_b = {item["id"] for item in list_b.json()["items"]}
            assert ids_a == {str(fact_a.fact_id)}
            assert ids_b == {str(fact_b.fact_id)}
            assert ids_a.isdisjoint(ids_b)

            agent_proposal = await _api_request(
                app,
                "POST",
                "/api/v1/facts/proposals/from-agent-reach",
                headers=headers_a,
                json={
                    "company_id": str(company_a.id),
                    "evidence_id": str(agent_evidence_id),
                    "field_name": "city",
                    "proposed_value": "Jeddah",
                },
            )
            assert agent_proposal.status_code == HTTP_OK
            assert agent_proposal.json()["crm_applied"] is False
            agent_fact_id = uuid.UUID(agent_proposal.json()["id"])
            agent_fact = await session.get(CanonicalFact, agent_fact_id)
            assert agent_fact is not None
            assert agent_fact.actor_type == "human" and agent_fact.actor_id == str(admin_a.id)
            assert agent_fact.evidence_snapshot[0]["evidence_kind"] == EvidenceKind.CITED_CLAIM.value
            assert (
                agent_fact.evidence_snapshot[0]["confidence_level"]
                == ConfidenceLevel.UNKNOWN.value
            )
            assert "private_fixture_payload" not in str(agent_fact.evidence_snapshot)

            service_jwt_denied = await _api_request(
                app,
                "POST",
                "/api/v1/facts/proposals/from-agent-reach",
                headers=service_token_headers,
                json={
                    "company_id": str(company_a.id),
                    "evidence_id": str(agent_evidence_id),
                    "field_name": "website",
                    "proposed_value": "https://service-principal.invalid",
                },
            )
            assert service_jwt_denied.status_code == HTTP_FORBIDDEN

            service_human_route_denied = await _api_request(
                app,
                "POST",
                "/api/v1/facts/proposals",
                headers=service_token_headers,
                json={
                    "subject_type": "company",
                    "subject_id": str(company_a.id),
                    "field_name": "website",
                    "proposed_value": "https://service-human-route.invalid",
                    "evidence": [
                        {
                            "id": f"service-human-route:{uuid.uuid4()}",
                            "evidence_type": "market_signal",
                            "source": {
                                "source_domain": "agent_reach",
                                "source_type": "public_web_web",
                                "source_id": str(agent_evidence_id),
                                "source_name": "example.com",
                            },
                            "description": "A test-only service role claim.",
                            "confidence": 0.4,
                            "confidence_level": "unknown",
                            "evidence_kind": "web.cited_claim",
                            "data": {},
                            "recorded_at": datetime.now(UTC).isoformat(),
                        }
                    ],
                    "idempotency_token": f"service-human-route:{uuid.uuid4()}",
                },
            )
            assert service_human_route_denied.status_code == HTTP_FORBIDDEN

            wrong_tenant_key = await _api_request(
                app,
                "POST",
                "/api/v1/facts/proposals/from-agent-reach",
                headers={
                    "X-API-Key": _INTEGRATION_API_KEY,
                    "X-Tenant-Id": str(tenant_b.id),
                },
                json={
                    "company_id": str(company_a.id),
                    "evidence_id": str(agent_evidence_id),
                    "field_name": "website",
                    "proposed_value": "https://cross-tenant.invalid",
                },
            )
            # The key is valid, but the requested tenant differs from the
            # key's bound tenant.  This is an authenticated authorization
            # failure (403), not an invalid-credential response (401).
            assert wrong_tenant_key.status_code == HTTP_FORBIDDEN

            overprivileged_key = await _api_request(
                app,
                "POST",
                "/api/v1/facts/proposals/from-agent-reach",
                headers={
                    "X-API-Key": _OVERPRIVILEGED_INTEGRATION_API_KEY,
                    "X-Tenant-Id": str(tenant_a.id),
                },
                json={
                    "company_id": str(company_a.id),
                    "evidence_id": str(agent_evidence_id),
                    "field_name": "website",
                    "proposed_value": "https://overprivileged.invalid",
                },
            )
            assert overprivileged_key.status_code == HTTP_FORBIDDEN

            service_proposal = await _api_request(
                app,
                "POST",
                "/api/v1/facts/proposals/from-agent-reach",
                headers={
                    "X-API-Key": _INTEGRATION_API_KEY,
                    "X-Tenant-Id": str(tenant_a.id),
                },
                json={
                    "company_id": str(company_a.id),
                    "evidence_id": str(agent_evidence_id),
                    "field_name": "employees_count",
                    "proposed_value": 42,
                },
            )
            assert service_proposal.status_code == HTTP_OK, service_proposal.text
            assert service_proposal.json()["crm_applied"] is False
            service_fact = await session.get(CanonicalFact, uuid.UUID(service_proposal.json()["id"]))
            assert service_fact is not None
            assert service_fact.actor_type == "agent"
            assert service_fact.actor_id == (
                f"agent_reach_service:{service_a.id}:api_key:minder-integration-key-id"
            )

            agent_self_review = await _api_request(
                app,
                "POST",
                f"/api/v1/facts/{agent_fact_id}/decision",
                headers=headers_a,
                json={"decision": "approve", "reason": "Proposer cannot review own item."},
            )
            assert agent_self_review.status_code == HTTP_CONFLICT
            agent_independent_review = await _api_request(
                app,
                "POST",
                f"/api/v1/facts/{agent_fact_id}/decision",
                headers=headers_a_reviewer,
                json={"decision": "approve", "reason": "Independent source review."},
            )
            assert agent_independent_review.status_code == HTTP_OK
            assert agent_independent_review.json()["crm_applied"] is False

            api_proposal = await _api_request(
                app,
                "POST",
                "/api/v1/facts/proposals",
                headers=headers_a,
                json={
                    "subject_type": "company",
                    "subject_id": str(company_a.id),
                    "field_name": "city",
                    "proposed_value": "Dammam",
                    "evidence": [
                        {
                            "id": proposal_evidence.id,
                            "evidence_type": proposal_evidence.evidence_type.value,
                            "source": {
                                "source_domain": proposal_evidence.source.source_domain,
                                "source_type": proposal_evidence.source.source_type,
                                "source_id": proposal_evidence.source.source_id,
                                "source_name": proposal_evidence.source.source_name,
                            },
                            "description": proposal_evidence.description,
                            "confidence": proposal_evidence.confidence,
                            "confidence_level": proposal_evidence.confidence_level.value,
                            "evidence_kind": proposal_evidence.evidence_kind.value,
                            "data": {"city": "Dammam"},
                            "recorded_at": proposal_evidence.recorded_at.isoformat(),
                        }
                    ],
                    "idempotency_token": f"jwt-api:{uuid.uuid4()}",
                },
            )
            assert api_proposal.status_code == HTTP_OK
            assert api_proposal.json()["crm_applied"] is False
            api_fact_id = uuid.UUID(api_proposal.json()["id"])
            api_fact = await session.get(CanonicalFact, api_fact_id)
            assert api_fact is not None
            assert api_fact.actor_type == "human" and api_fact.actor_id == str(admin_a.id)
            assert api_fact.evidence_snapshot[0]["evidence_kind"] == EvidenceKind.CITED_CLAIM.value
            assert (
                api_fact.evidence_snapshot[0]["confidence_level"] == ConfidenceLevel.UNKNOWN.value
            )

            self_review = await _api_request(
                app,
                "POST",
                f"/api/v1/facts/{api_fact_id}/decision",
                headers=headers_a,
                json={"decision": "approve", "reason": "Must be reviewed independently."},
            )
            assert self_review.status_code == HTTP_CONFLICT
            independent_review = await _api_request(
                app,
                "POST",
                f"/api/v1/facts/{api_fact_id}/decision",
                headers=headers_a_reviewer,
                json={"decision": "approve", "reason": "Independent reviewer verified it."},
            )
            assert independent_review.status_code == HTTP_OK
            assert independent_review.json()["crm_applied"] is False

            review = await _api_request(
                app,
                "POST",
                f"/api/v1/facts/{fact_a.fact_id}/decision",
                headers=headers_a,
                json={"decision": "reject", "reason": "Integration review proof."},
            )
            assert review.status_code == HTTP_OK and review.json()["status"] == "REJECTED"
            assert review.json()["crm_applied"] is False
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_a.id)},
            )
            stored_company = await session.scalar(select(Company).where(Company.id == company_a.id))
            assert stored_company is not None and stored_company.city is None
        finally:
            await session.close()
            await outer.rollback()
    await engine.dispose()
