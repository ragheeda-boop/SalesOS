"""CrmConnector/ErpConnector/MarketFeedConnector.store() had 3 independent bugs,
all confirmed by direct SQL reproduction against the real schema before any fix:

Mechanical findings, `runtime/knowledge_graph_runtime/connectors.py` — this is
dead code (confirmed via repo-wide grep: `CrmConnector`/`ErpConnector`/
`MarketFeedConnector` are referenced only by this module's own
`runtime/knowledge_graph_runtime/tests.py`, which never exercises `store()`'s
real SQL — only `transform`/`authenticate`/`_mock_fetch`/`sync`-without-auth),
fixed ahead of any future wiring decision, same posture as reports 73/74:

1. **`source` column does not exist on `companies`** — confirmed via `\\d
   companies` and a direct INSERT attempt:
   `ERROR: column "source" of relation "companies" does not exist`. All 3
   connectors' `store()` INSERTs referenced it. Fixed by using the model's
   actual `source_ids` JSONB column instead (a JSON array containing the
   connector type).
2. **External source ids bound directly to the `uuid` `id` primary key** —
   `record.source_id` values like `"crm-001"` are not valid uuids, confirmed
   via a direct INSERT attempt: `ERROR: invalid input syntax for type uuid:
   "crm-001"`. Fixed by deriving a deterministic `uuid5` from
   `(tenant_id, connector_type, source_id)` — preserves the file's intended
   idempotent `ON CONFLICT (id) DO UPDATE` upsert semantics (same external id
   always maps to the same row) without a schema change.
3. **No tenant GUC pinning anywhere in `store()`** — `companies` has RLS +
   FORCE RLS; every real write would have failed its `WITH CHECK` even after
   fixing bugs 1 and 2. `apply_tenant_guc()` added to all 3 `store()` methods.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from runtime.knowledge_graph_runtime.connectors import (
    ConnectorRecord,
    ConnectorType,
    CrmConnector,
    ErpConnector,
    MarketFeedConnector,
)


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


async def _seed_tenant(tenant_id: str) -> None:
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Connector Test', :slug)"),
            {"id": tenant_id, "slug": f"conn-test-{tenant_id[:8]}"},
        )
        await session.commit()


@pytest.mark.asyncio
async def test_crm_connector_store_persists_and_is_idempotent_and_tenant_scoped():
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    await _seed_tenant(tenant_a)
    await _seed_tenant(tenant_b)

    connector = CrmConnector(session_factory=async_session, config={}, logger=None)
    record = ConnectorRecord(
        source_type=ConnectorType.CRM,
        source_id="crm-001",
        raw_data={"name": "ACME Corp", "city": "Riyadh"},
    )
    transformed = connector.transform([record])

    stored = await connector.store(transformed, tenant_a)
    assert stored == 1
    assert record.status != "failed"

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_a}
        )
        result = await session.execute(
            text("SELECT name_en, city, source_ids FROM companies WHERE tenant_id = :t"),
            {"t": tenant_a},
        )
        rows = result.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "ACME Corp"
        assert rows[0][2] == ["crm"]

        # Fail-closed: tenant B must never see tenant A's synced company.
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_b}
        )
        result_b = await session.execute(text("SELECT COUNT(*) FROM companies"))
        assert result_b.scalar() == 0

    # Re-sync the same external id: must upsert the same row, not duplicate.
    record2 = ConnectorRecord(
        source_type=ConnectorType.CRM,
        source_id="crm-001",
        raw_data={"name": "ACME Corp Updated", "city": "Jeddah"},
    )
    transformed2 = connector.transform([record2])
    stored2 = await connector.store(transformed2, tenant_a)
    assert stored2 == 1

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_a}
        )
        result = await session.execute(
            text("SELECT name_en, city FROM companies WHERE tenant_id = :t"),
            {"t": tenant_a},
        )
        rows = result.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "ACME Corp Updated"
        assert rows[0][1] == "Jeddah"


@pytest.mark.asyncio
async def test_erp_and_market_feed_connectors_store_persists():
    tenant_id = str(uuid.uuid4())
    await _seed_tenant(tenant_id)

    erp = ErpConnector(session_factory=async_session, config={}, logger=None)
    erp_record = ConnectorRecord(
        source_type=ConnectorType.ERP,
        source_id="erp-001",
        raw_data={"company_name": "TechCorp", "order_total": 50000, "currency": "SAR"},
    )
    stored = await erp.store(erp.transform([erp_record]), tenant_id)
    assert stored == 1
    assert erp_record.status != "failed"

    market = MarketFeedConnector(session_factory=async_session, config={}, logger=None)
    market_record = ConnectorRecord(
        source_type=ConnectorType.MARKET_FEED,
        source_id="mkt-001",
        raw_data={"name": "Saudi Aramco", "sector": "Energy", "market_cap": 7e12},
    )
    stored2 = await market.store(market.transform([market_record]), tenant_id)
    assert stored2 == 1
    assert market_record.status != "failed"

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        result = await session.execute(
            text("SELECT COUNT(*) FROM companies WHERE tenant_id = :t"), {"t": tenant_id}
        )
        assert result.scalar() == 2
