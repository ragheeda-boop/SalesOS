"""app.state.nba_engine was read in 3 places -- app/application/dashboard/
router.py:176 and runtime/nba_engine/api/router.py:81,104 (the live,
mounted GET /opportunities/{id}/nba and POST .../nba/refresh endpoints,
the exact router report 135 already fixed 3 internal NBAEngine bugs in:
GUC pinning, a nonexistent activity_records.description column, and
unserialized JSON) -- but NEVER SET anywhere in the entire codebase,
confirmed via repo-wide grep for `app.state.nba_engine =`. Neither of
NBAEngine's only 2 construction sites (mcp_server/salesos_client.py, an
unrelated standalone MCP client script; and
runtime/nba_engine/subscribers/register_subscribers(), which is itself
never called from the live app either) ever touches app.state.

This means report 135's fix, while correct and necessary, was never
actually reachable through the real REST API: both endpoints' first
statement is `engine = getattr(request.app.state, "nba_engine", None)`,
immediately followed by `if not engine: raise HTTPException(503, ...)` --
so every real call has always 503'd before ever reaching the (now
internally-correct) NBAEngine code, exactly the same shape as report
148's app.state.approval_service finding.

Fixed by adding _init_approval()-style wiring: a new
_init_nba_engine() in app/boot/startup.py (Phase 3, alongside
_init_policy_engine/_init_recommendation_engine, since it needs Phase 1's
feature_store/event_runtime already set), passing the already-wired
app.state.feature_store/event_runtime through to a real NBAEngine.

This test proves the fix end to end against a real, fully-migrated,
RLS-enforced disposable database: an NBAEngine wired exactly the way
_init_nba_engine's code wires it, retrieved via the exact getattr
pattern the router uses, genuinely computes an NBA for a real seeded
opportunity -- the actual defect this fix closes. The background
event-subscriber wiring gap (runtime/nba_engine/subscribers/
register_subscribers() also never called) is a separate, distinct
feature (auto-recompute-on-event vs. this on-demand path) and is
disclosed, not fixed, here -- the REST API does not depend on it.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.boot.startup import _init_nba_engine
from app.database import engine
from runtime.nba_engine import NBAEngine


class _StubLogger:
    def info(self, *a, **k):
        pass

    def exception(self, *a, **k):
        pass


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    async with engine.connect() as conn:
        db_name = await conn.scalar(text("SELECT current_database()"))
    assert db_name != "salesos", (
        f"REFUSING: connected to {db_name!r} — this is the persistent "
        "local dev database, not a disposable/test one."
    )
    yield
    await engine.dispose()


async def _seed_tenant_and_opportunity(tenant_id: str, opportunity_id: str, company_id: str) -> None:
    from app.database import async_session

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'NBA Wiring Test', :slug)"),
            {"id": tenant_id, "slug": f"nba-wiring-{tenant_id[:8]}"},
        )
        await session.execute(
            text(
                """
                INSERT INTO commercial_opportunities
                    (id, tenant_id, company_id, name, stage)
                VALUES (:id, :tid, :cid, :name, 'prospecting')
                """
            ),
            {"id": opportunity_id, "tid": tenant_id, "cid": company_id, "name": "Wired Deal Co"},
        )
        await session.commit()


@pytest.mark.asyncio
async def test_init_nba_engine_wires_a_real_working_engine():
    """_init_nba_engine() must set app.state.nba_engine to a real,
    working NBAEngine — not leave it unset (the original defect)."""
    fake_app = SimpleNamespace(state=SimpleNamespace())

    await _init_nba_engine(fake_app, _StubLogger())

    engine_obj = getattr(fake_app.state, "nba_engine", None)
    assert engine_obj is not None, "nba_engine was never set — the original bug"
    assert isinstance(engine_obj, NBAEngine)


@pytest.mark.asyncio
async def test_router_lookup_pattern_finds_the_wired_engine_and_computes_a_real_nba():
    """Reproduces runtime/nba_engine/api/router.py's exact
    getattr(request.app.state, "nba_engine", None) lookup, then exercises
    the same call the live GET /opportunities/{id}/nba endpoint makes."""
    fake_app = SimpleNamespace(state=SimpleNamespace())
    await _init_nba_engine(fake_app, _StubLogger())

    fake_request = SimpleNamespace(app=fake_app)
    nba_engine = getattr(fake_request.app.state, "nba_engine", None)
    assert nba_engine is not None, "the exact router lookup pattern found nothing"

    tenant_id = str(uuid.uuid4())
    opportunity_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    await _seed_tenant_and_opportunity(tenant_id, opportunity_id, company_id)

    nba = await nba_engine.get_or_compute(opportunity_id, tenant_id)

    assert nba is not None, (
        "engine.get_or_compute() returned nothing for a genuinely seeded "
        "opportunity through the wired instance"
    )
    assert nba.opportunity_id == opportunity_id
