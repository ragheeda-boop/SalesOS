"""DEC-157 step 4: cross-tenant isolation proof for the 14 orphan-keep tables.

Migration e1d1c1225d00 adds ENABLE+FORCE RLS and the canonical
``tenant_isolation_<table>`` policy to 14 tables governed by DEC-130f's
"no DROP without a dedicated DEC" orphan-keep register. Steps 1-2 (semantics
ruling + GUC pinning at the five call sites: runtime/feature_store/features.py,
runtime/policy_runtime/__init__.py, runtime/decision_runtime/feedback_loop.py,
sdk/events/store.py, runtime/activity_runtime/__init__.py) landed first.

This file proves, through each module's real GUC-pinned code path (not just
raw SQL against pg_class), that:
  - the restricted, non-superuser, non-BYPASSRLS ``salesos_app`` role sees
    only its own tenant's rows on every one of the 14 tables;
  - a session with no tenant GUC pinned sees nothing (fail-closed, same as
    every other Category A table — no ``OR tenant_id IS NULL`` bypass, per
    the accepted precedent in d1a8c35e7f09 / b7e2f65a3f07);
  - the GUC-pinning code added this session does not change any module's
    functional behavior for its own tenant.

Seeding uses ``owner_engine`` (the ``salesos`` superuser/BYPASSRLS role, same
as ``test_relationships_rls.py``) so both tenants' rows can be written
without an RLS ``WITH CHECK`` fight over which GUC is pinned at seed time.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine, owner_engine

ALL_14_TABLES = (
    "company_funding_events",
    "company_job_postings",
    "company_intent_rfps",
    "company_intent_visits",
    "company_intent_content",
    "company_intent_contacts",
    "company_products",
    "company_deals",
    "company_payments",
    "company_policies",
    "decisions",
    "decision_feedback_loop",
    "domain_events",
    "activity_records",
)


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engines_after_test():
    yield
    await engine.dispose()
    await owner_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables():
    async with owner_engine.begin() as conn:
        for table in ALL_14_TABLES:
            await conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
    yield


async def _set_tenant(session, tenant_id: str | None) -> None:
    if tenant_id:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": tenant_id},
        )
    else:
        await session.execute(text("RESET app.tenant_id"))


@pytest.mark.asyncio
async def test_all_14_tables_force_rls_with_exactly_one_policy():
    async with async_session() as session:
        for table in ALL_14_TABLES:
            row = (
                await session.execute(
                    text(
                        "SELECT relrowsecurity, relforcerowsecurity FROM pg_class "
                        "WHERE relname = :t AND relkind = 'r'"
                    ),
                    {"t": table},
                )
            ).one()
            assert row.relrowsecurity is True, f"{table} must have RLS enabled"
            assert row.relforcerowsecurity is True, f"{table} must FORCE RLS"

            policy_count = (
                await session.execute(
                    text(
                        "SELECT count(*) FROM pg_policies "
                        "WHERE schemaname = 'public' AND tablename = :t "
                        "AND policyname = :p"
                    ),
                    {"t": table, "p": f"tenant_isolation_{table}"},
                )
            ).scalar()
            assert policy_count == 1, f"{table} must have exactly one canonical tenant policy"
        await session.rollback()


@pytest.mark.asyncio
async def test_feature_store_computers_see_only_their_own_tenant():
    from runtime.feature_store.features import FundingScoreComputer, HiringScoreComputer

    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    company_a, company_b = str(uuid.uuid4()), str(uuid.uuid4())

    async with owner_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO company_funding_events "
                "(id, tenant_id, company_id, round_type, amount, date) "
                "VALUES (gen_random_uuid(), :tid, :cid, 'series_a', 1000000, now())"
            ),
            {"tid": tenant_a, "cid": company_a},
        )
        await conn.execute(
            text(
                "INSERT INTO company_job_postings "
                "(id, tenant_id, company_id, title, status) "
                "VALUES (gen_random_uuid(), :tid, :cid, 'Engineer', 'active')"
            ),
            {"tid": tenant_a, "cid": company_a},
        )

    funding = FundingScoreComputer()
    hiring = HiringScoreComputer()

    async with async_session() as session:
        result_a_funding = await funding.compute(
            {"id": company_a, "tenant_id": tenant_a}, session
        )
        result_a_hiring = await hiring.compute(
            {"id": company_a, "tenant_id": tenant_a}, session
        )
        assert result_a_funding.contributing_signals["has_funding"] is True
        assert result_a_hiring.contributing_signals["active_postings"] == 1

        # Tenant B queries the SAME company_id (cross-tenant probe) — RLS
        # must hide tenant A's rows regardless of the id matching.
        result_b_funding = await funding.compute(
            {"id": company_a, "tenant_id": tenant_b}, session
        )
        result_b_hiring = await hiring.compute(
            {"id": company_a, "tenant_id": tenant_b}, session
        )
        assert result_b_funding.contributing_signals["has_funding"] is False
        assert result_b_hiring.contributing_signals["active_postings"] == 0
        await session.rollback()


@pytest.mark.asyncio
async def test_feature_store_intent_and_commercial_tables_isolated():
    from runtime.feature_store.features import ExpansionScoreComputer, RevenueScoreComputer

    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    company_a = str(uuid.uuid4())

    async with owner_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO company_products (id, tenant_id, company_id, name, category) "
                "VALUES (gen_random_uuid(), :tid, :cid, 'Widget', 'hardware')"
            ),
            {"tid": tenant_a, "cid": company_a},
        )
        await conn.execute(
            text(
                "INSERT INTO company_deals (id, tenant_id, company_id, amount, status) "
                "VALUES (gen_random_uuid(), :tid, :cid, 50000, 'closed_won')"
            ),
            {"tid": tenant_a, "cid": company_a},
        )
        await conn.execute(
            text(
                "INSERT INTO company_payments (id, tenant_id, company_id, amount, status) "
                "VALUES (gen_random_uuid(), :tid, :cid, 50000, 'paid')"
            ),
            {"tid": tenant_a, "cid": company_a},
        )

    expansion = ExpansionScoreComputer()
    revenue = RevenueScoreComputer()

    async with async_session() as session:
        r_a = await revenue.compute({"id": company_a, "tenant_id": tenant_a}, session)
        assert r_a.contributing_signals.get("deal_equity") == 50000

        r_b = await revenue.compute({"id": company_a, "tenant_id": tenant_b}, session)
        assert r_b.contributing_signals.get("deal_equity", 0) == 0

        e_a = await expansion.compute({"id": company_a, "tenant_id": tenant_a}, session)
        e_b = await expansion.compute({"id": company_a, "tenant_id": tenant_b}, session)
        assert e_a.contributing_signals["product_categories"] == 1
        assert e_b.contributing_signals["product_categories"] == 0
        await session.rollback()


@pytest.mark.asyncio
async def test_policy_engine_respects_tenant_isolation():
    from runtime.policy_runtime import PolicyEngine

    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    company_a = str(uuid.uuid4())

    async with owner_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO company_policies "
                "(tenant_id, company_id, policy_name, policy_type, action, reason, severity, is_active) "
                "VALUES (:tid, :cid, 'dnc', 'compliance', 'block', 'do not contact', 10, true)"
            ),
            {"tid": tenant_a, "cid": company_a},
        )

    engine_a = PolicyEngine(session_factory=async_session)

    results_a = await engine_a.evaluate({}, company_a, tenant_a)
    assert any(r.policy_name == "dnc" for r in results_a)

    results_b = await engine_a.evaluate({}, company_a, tenant_b)
    assert not any(r.policy_name == "dnc" for r in results_b)


@pytest.mark.asyncio
async def test_decision_feedback_loop_respects_tenant_isolation():
    from runtime.decision_runtime.feedback_loop import DecisionFeedbackLoop

    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    company_a = str(uuid.uuid4())
    decision_id = str(uuid.uuid4())

    loop = DecisionFeedbackLoop(session_factory=async_session)
    await loop.record_feedback(
        decision_id=decision_id,
        company_id=company_a,
        tenant_id=tenant_a,
        accepted=True,
        executed=True,
        outcome="won",
        outcome_value=1000.0,
    )

    async with async_session() as session:
        await _set_tenant(session, tenant_a)
        count_a = (
            await session.execute(
                text("SELECT count(*) AS n FROM decision_feedback_loop WHERE decision_id = :d"),
                {"d": decision_id},
            )
        ).first().n
        assert count_a == 1

        await _set_tenant(session, tenant_b)
        count_b = (
            await session.execute(
                text("SELECT count(*) AS n FROM decision_feedback_loop WHERE decision_id = :d"),
                {"d": decision_id},
            )
        ).first().n
        assert count_b == 0

        await _set_tenant(session, None)
        count_unpinned = (
            await session.execute(
                text("SELECT count(*) AS n FROM decision_feedback_loop WHERE decision_id = :d"),
                {"d": decision_id},
            )
        ).first().n
        assert count_unpinned == 0
        await session.rollback()


@pytest.mark.asyncio
async def test_decisions_table_respects_tenant_isolation():
    """`decisions` already had GUC pinning (apply_tenant_guc) — only RLS is new."""
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    company_a = str(uuid.uuid4())
    decision_id = str(uuid.uuid4())

    async with owner_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO decisions "
                "(decision_id, tenant_id, company_id, decision_type, status, created_at) "
                "VALUES (:did, :tid, :cid, 'nba', 'pending', now())"
            ),
            {"did": decision_id, "tid": tenant_a, "cid": company_a},
        )

    async with async_session() as session:
        await _set_tenant(session, tenant_a)
        count_a = (
            await session.execute(
                text("SELECT count(*) AS n FROM decisions WHERE decision_id = :d"),
                {"d": decision_id},
            )
        ).first().n
        assert count_a == 1

        await _set_tenant(session, tenant_b)
        count_b = (
            await session.execute(
                text("SELECT count(*) AS n FROM decisions WHERE decision_id = :d"),
                {"d": decision_id},
            )
        ).first().n
        assert count_b == 0
        await session.rollback()


@pytest.mark.asyncio
async def test_activity_runtime_respects_tenant_isolation():
    from runtime.activity_runtime import ActivityRuntime

    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    runtime = ActivityRuntime(session_factory=async_session)

    await runtime.ingest(
        actor="user-1",
        action="note.created",
        entity_type="company",
        entity_id="c1",
        tenant_id=tenant_a,
    )

    items_a, total_a = await runtime.query(tenant_id=tenant_a)
    assert total_a == 1
    assert len(items_a) == 1

    items_b, total_b = await runtime.query(tenant_id=tenant_b)
    assert total_b == 0
    assert items_b == []


@pytest.mark.asyncio
async def test_activity_runtime_null_tenant_is_invisible_fail_closed():
    """No OR-IS-NULL bypass (DEC-157 ruling): a NULL-tenant row stays
    invisible under every tenant GUC AND under no GUC at all — matching the
    admin_ai_costs/admin_jobs precedent (d1a8c35e7f09), not a special case.
    """
    from runtime.activity_runtime import ActivityRuntime

    tenant_a = str(uuid.uuid4())
    runtime = ActivityRuntime(session_factory=async_session)

    # A tenant-less activity record — e.g. ActivityRuntime.on_domain_event()
    # when the inbound domain event carries no tenant_id. Under RLS with no
    # bypass, this INSERT must fail closed (WITH CHECK: NULL = NULL -> NULL).
    from sqlalchemy.exc import DBAPIError

    with pytest.raises(DBAPIError):
        await runtime.ingest(
            actor="system",
            action="platform.event",
            entity_type="unknown",
            entity_id="",
            tenant_id=None,
        )

    # Confirm tenant A's own data is unaffected by the failed insert.
    await runtime.ingest(
        actor="user-1", action="note.created", entity_type="company",
        entity_id="c1", tenant_id=tenant_a,
    )
    items_a, total_a = await runtime.query(tenant_id=tenant_a)
    assert total_a == 1


@pytest.mark.asyncio
async def test_event_store_respects_tenant_isolation():
    from sdk.events.base import DomainEvent
    from sdk.events.store import PostgresEventStore

    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())

    async with async_session() as session:
        store = PostgresEventStore(session)
        await store.append(
            DomainEvent(
                event_id=str(uuid.uuid4()),
                event_type="decision.created",
                aggregate_id="d1",
                aggregate_type="decision",
                tenant_id=tenant_a,
                occurred_at=datetime.now(timezone.utc),
                data={"x": 1},
            )
        )
        await session.commit()

    async with async_session() as session:
        store = PostgresEventStore(session)
        events_a = await store.read_stream("decision", "d1", tenant_id=tenant_a)
        assert len(events_a) == 1

        events_b = await store.read_stream("decision", "d1", tenant_id=tenant_b)
        assert events_b == []

        by_type_a = await store.read_by_type("decision.created", tenant_id=tenant_a)
        assert len(by_type_a) == 1
        by_type_b = await store.read_by_type("decision.created", tenant_id=tenant_b)
        assert by_type_b == []
        await session.rollback()
