"""Live tenant/RLS persistence proof for Agent Reach (salesos_test only)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.modules.agent_reach.models import (
    EvidenceItem,
    Signal,
    SignalConfidence,
    SignalType,
)
from app.modules.agent_reach.persistence import PostgresEvidenceStore


@pytest.mark.asyncio
async def test_agent_reach_evidence_and_signals_are_tenant_persisted_and_cleaned():
    configured_url = make_url(settings.app_database_url)
    if configured_url.database not in {"salesos", "salesos_test"}:
        pytest.skip("Agent Reach persistence integration targets salesos_test only")

    test_url = configured_url.set(database="salesos_test")
    if test_url.database != "salesos_test":
        pytest.skip("Refusing to connect outside salesos_test")

    engine = create_async_engine(test_url)
    try:
        async with engine.connect() as connection:
            database, is_superuser, bypass_rls = (
                await connection.execute(
                    text(
                        """
                        SELECT current_database(), r.rolsuper, r.rolbypassrls
                        FROM pg_roles r WHERE r.rolname = current_user
                        """
                    )
                )
            ).one()
            assert database == "salesos_test"
            assert is_superuser is False
            assert bypass_rls is False

            tables = set(
                (
                    await connection.execute(
                        text(
                            """
                            SELECT table_name FROM information_schema.tables
                            WHERE table_schema = 'public'
                              AND table_name IN ('agent_evidence', 'agent_signals')
                            """
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert tables == {"agent_evidence", "agent_signals"}

        factory = async_sessionmaker(engine, expire_on_commit=False)
        store = PostgresEvidenceStore(factory)
        tenant_id = str(uuid.uuid4())
        company_name = f"Codex Agent Reach persistence probe {uuid.uuid4()}"
        cleanup_verified = False
        try:
            item = EvidenceItem(
                company_name=company_name,
                source_url="https://example.com/codex-agent-reach-probe",
                title="Hiring update",
                summary="A test-only hiring announcement",
            )
            first = await store.save_evidence(tenant_id, item)
            duplicate = await store.save_evidence(tenant_id, item)
            signal = Signal(
                company_name=company_name,
                signal_type=SignalType.HIRING,
                confidence=SignalConfidence.MEDIUM,
                title="Hiring activity detected for persistence probe",
                source_urls=[item.source_url],
                evidence_ids=[first.evidence_id],
            )

            assert first.inserted is True
            assert duplicate.inserted is False
            assert duplicate.evidence_id == first.evidence_id
            assert await store.add_signal(tenant_id, signal) is True

            evidence_rows = await store.get_evidence(tenant_id, company_name)
            signal_rows = await store.get_signals(tenant_id, company_name)
            assert len(evidence_rows) == 1
            assert len(signal_rows) == 1
            assert signal_rows[0].evidence_ids == [first.evidence_id]
        finally:
            await store.clear(tenant_id, company_name)
            cleanup_verified = (
                await store.get_evidence(tenant_id, company_name) == []
                and await store.get_signals(tenant_id, company_name) == []
            )
        assert cleanup_verified, "synthetic Agent Reach probe rows were not fully removed"
    finally:
        await engine.dispose()
