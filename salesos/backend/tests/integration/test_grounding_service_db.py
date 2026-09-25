"""GroundingService (agent_runtime's AI context loader) returned no contacts
and no opportunities for every company.

- contacts query selected/ordered by `is_decision_maker`, a column contacts
  does not have;
- opportunities query read the `_deprecated` `opportunities` table with
  columns (`amount`, `probability`) it does not have, and that table has no
  writer. The canonical table is commercial_opportunities (AGENTS.md §12).

Both errors were swallowed (`except Exception: return []`), so agents were
silently grounded on empty context. Found by the EXPLAIN sweep (report 98).
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from intelligence.grounding import GroundingService
from runtime.agent_runtime import _tenant_scoped_session_factory


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_context_contains_real_contacts_and_opportunities():
    tid, cid = str(uuid.uuid4()), str(uuid.uuid4())
    async with async_session() as s:
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tid})
        await s.execute(text("INSERT INTO tenants (id, name, slug) VALUES (:i, 'G', :s)"),
                        {"i": tid, "s": f"g-{tid[:8]}"})
        await s.execute(text("INSERT INTO companies (id, tenant_id, name_ar) VALUES (:i, :t, 'شركة')"),
                        {"i": cid, "t": tid})
        await s.execute(text("INSERT INTO contacts (id, tenant_id, company_id, name, is_primary) "
                             "VALUES (:i, :t, :c, 'Primary Person', true)"),
                        {"i": str(uuid.uuid4()), "t": tid, "c": cid})
        await s.execute(text("INSERT INTO commercial_opportunities (id, tenant_id, company_id, name, value, stage) "
                             "VALUES (:i, :t, :c, 'Big Deal', 250000, 'proposal')"),
                        {"i": str(uuid.uuid4()), "t": tid, "c": cid})
        await s.execute(text("INSERT INTO company_signals (tenant_id, company_id, signal_type, title) "
                             "VALUES (:t, :c, 'hiring', 'Hiring 20 engineers')"),
                        {"t": tid, "c": cid})
        await s.execute(text("INSERT INTO activity_records (id, actor, action, entity_type, entity_id, "
                             "tenant_id, metadata) VALUES (:i, 'u', 'meeting', 'company', :c, :t, "
                             "CAST(:m AS jsonb))"),
                        {"i": uuid.uuid4().hex, "c": cid, "t": tid,
                         "m": '{"description": "Discovery call held"}'})
        await s.commit()

    svc = GroundingService(db_session_factory=_tenant_scoped_session_factory(async_session, tid))
    ctx = await svc.get_context(cid)

    assert [c["name"] for c in ctx.contacts] == ["Primary Person"]
    assert len(ctx.opportunities) == 1
    assert ctx.opportunities[0]["title"] == "Big Deal"
    assert float(ctx.opportunities[0]["amount"]) == 250000.0
    # PO decision B5: signals from company_signals, activity from activity_records.
    assert [s["title"] for s in ctx.signals] == ["Hiring 20 engineers"]
    assert [a["description"] for a in ctx.recent_activity] == ["Discovery call held"]
    block = ctx.to_prompt_block()
    assert "250000" in block and "Hiring 20 engineers" in block and "Discovery call held" in block
