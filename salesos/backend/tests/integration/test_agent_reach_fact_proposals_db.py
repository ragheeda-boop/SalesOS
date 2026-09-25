"""Agent Reach evidence enters the Fact ledger only as tenant-scoped proposals."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import settings
from app.modules.agent_reach.fact_proposals import AgentReachFactProposalBridge
from app.modules.company.models import Company
from app.modules.facts.models import CanonicalFact, EvidenceRecord, FactEvidence
from app.modules.facts.service import FactPolicyRejected
from app.modules.identity.models import Tenant
from domains.commercial.evidence.contracts.models import EvidenceKind


@pytest.mark.asyncio
async def test_agent_reach_evidence_becomes_idempotent_tenant_proposal_only():
    test_url = make_url(settings.app_database_url).set(database="salesos_test")
    engine = create_async_engine(test_url, pool_pre_ping=True, connect_args={"command_timeout": 10})
    async with engine.connect() as connection:
        outer = await connection.begin()
        assert await connection.scalar(text("SELECT current_database()")) == "salesos_test"
        role = await connection.execute(
            text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")
        )
        assert role.one() == (False, False)
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        tenant_a_id = uuid.uuid4()
        tenant_b_id = uuid.uuid4()
        evidence_a_id = uuid.uuid4()
        evidence_b_id = uuid.uuid4()
        wrong_company_evidence_id = uuid.uuid4()
        stale_evidence_id = uuid.uuid4()
        try:
            tenant_a = Tenant(id=tenant_a_id, name="Agent Reach Fact A", slug=f"ar-fact-a-{uuid.uuid4()}")
            tenant_b = Tenant(id=tenant_b_id, name="Agent Reach Fact B", slug=f"ar-fact-b-{uuid.uuid4()}")
            session.add_all([tenant_a, tenant_b])
            await session.flush()

            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_a_id)},
            )
            company_a = Company(tenant_id=tenant_a_id, name_ar="Agent Reach Fact Company A")
            session.add(company_a)
            await session.flush()

            async def insert_agent_evidence(
                *,
                tenant_id: uuid.UUID,
                evidence_id: uuid.UUID,
                company_name: str,
                expired: bool = False,
                source_url: str = "https://www.example.com/company",
            ):
                await session.execute(
                    text(
                        """
                        INSERT INTO agent_evidence
                            (id, tenant_id, company_name, evidence_type, channel, source_url,
                             title, summary, raw_data, confidence, fingerprint, collected_at,
                             expires_at, metadata)
                        VALUES
                            (CAST(:id AS uuid), :tenant_id, :company_name, 'web_search', 'web',
                             :source_url, 'Company location',
                             'The public company page lists Riyadh as its location.',
                             CAST(:raw_data AS jsonb), 0.95, :fingerprint, :collected_at,
                             :expires_at, CAST(:metadata AS jsonb))
                        """
                    ),
                    {
                        "id": str(evidence_id),
                        "tenant_id": str(tenant_id),
                        "company_name": company_name,
                        "source_url": source_url,
                        "raw_data": '{"private_fixture_payload":"must not be copied"}',
                        "fingerprint": uuid.uuid4().hex + uuid.uuid4().hex,
                        "collected_at": datetime.now(UTC),
                        "expires_at": datetime.now(UTC) - timedelta(days=1) if expired else None,
                        "metadata": "{}",
                    },
                )

            await insert_agent_evidence(
                tenant_id=tenant_a_id,
                evidence_id=evidence_a_id,
                company_name=company_a.name_ar,
            )
            await insert_agent_evidence(
                tenant_id=tenant_a_id,
                evidence_id=wrong_company_evidence_id,
                company_name="Unrelated company name",
            )
            await insert_agent_evidence(
                tenant_id=tenant_a_id,
                evidence_id=stale_evidence_id,
                company_name=company_a.name_ar,
                expired=True,
                source_url="https://www.example.com/company/stale",
            )

            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_b_id)},
            )
            company_b = Company(tenant_id=tenant_b_id, name_ar="Agent Reach Fact Company B")
            session.add(company_b)
            await session.flush()
            await insert_agent_evidence(
                tenant_id=tenant_b_id,
                evidence_id=evidence_b_id,
                company_name=company_b.name_ar,
            )

            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_a_id)},
            )
            bridge = AgentReachFactProposalBridge(session)
            first = await bridge.propose_from_evidence(
                tenant_id=tenant_a_id,
                company_id=company_a.id,
                evidence_id=evidence_a_id,
                field_name="city",
                proposed_value="Riyadh",
            )
            retry = await bridge.propose_from_evidence(
                tenant_id=tenant_a_id,
                company_id=company_a.id,
                evidence_id=evidence_a_id,
                field_name="city",
                proposed_value="Riyadh",
            )
            assert first.status == retry.status == "PROPOSED"
            assert first.created is True and retry.created is False
            assert first.fact_id == retry.fact_id

            with pytest.raises(FactPolicyRejected, match="does not contain"):
                await bridge.propose_from_evidence(
                    tenant_id=tenant_a_id,
                    company_id=company_a.id,
                    evidence_id=evidence_a_id,
                    field_name="city",
                    proposed_value="Jeddah",
                )

            fact = await session.get(CanonicalFact, first.fact_id)
            assert fact is not None
            assert fact.actor_type == "agent"
            assert fact.actor_id == f"agent_reach:evidence:{evidence_a_id}"
            assert fact.evidence_snapshot[0]["evidence_kind"] == EvidenceKind.CITED_CLAIM.value
            assert fact.evidence_snapshot[0]["confidence_level"] == "unknown"
            assert "private_fixture_payload" not in str(fact.evidence_snapshot)
            assert "utm_" not in str(fact.evidence_snapshot)

            evidence_link = await session.scalar(
                select(FactEvidence).where(FactEvidence.fact_id == first.fact_id)
            )
            assert evidence_link is not None
            evidence_record = await session.get(EvidenceRecord, evidence_link.evidence_id)
            assert evidence_record is not None
            assert evidence_record.evidence_kind == EvidenceKind.CITED_CLAIM.value
            assert evidence_record.data["source_url"] == "https://www.example.com/company"

            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_a_id)},
            )
            with pytest.raises(FactPolicyRejected, match="not found in the authenticated tenant"):
                await bridge.propose_from_evidence(
                    tenant_id=tenant_a_id,
                    company_id=company_a.id,
                    evidence_id=evidence_b_id,
                    field_name="city",
                    proposed_value="Jeddah",
                )

            stored_company = await session.scalar(select(Company).where(Company.id == company_a.id))
            assert stored_company is not None and stored_company.city is None

            with pytest.raises(FactPolicyRejected, match="does not exactly match"):
                await bridge.propose_from_evidence(
                    tenant_id=tenant_a_id,
                    company_id=company_a.id,
                    evidence_id=wrong_company_evidence_id,
                    field_name="city",
                    proposed_value="Riyadh",
                )

            with pytest.raises(FactPolicyRejected, match="not found in the authenticated tenant"):
                await bridge.propose_from_evidence(
                    tenant_id=tenant_a_id,
                    company_id=company_a.id,
                    evidence_id=stale_evidence_id,
                    field_name="city",
                    proposed_value="Riyadh",
                )
        finally:
            await session.close()
            if outer.is_active:
                await outer.rollback()
    await engine.dispose()
