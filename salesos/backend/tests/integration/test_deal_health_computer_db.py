"""DealHealthComputer must query real tables/columns with compatible types.

Mechanical finding, same class as reports 67/71/72: the signal-detection
join `JOIN commercial_opportunities o ON o.company_id = s.company_id`
compares `commercial_opportunities.company_id` (`varchar(36)`) directly
against `company_signals.company_id` (`uuid`) with no cast — Postgres
rejects this: `UndefinedFunctionError: operator does not exist: character
varying = uuid`. A second, independent bug in the same file: the timeline-
pressure calculation used `datetime.now(timezone.utc).date()` instead of
`date.today()` for a date-only "today" comparison against
`expected_close_date` (a plain `Date` column) — the same UTC/local
calendar-boundary bug fixed elsewhere this session
(`app/modules/signal_actions/actions.py`,
`app/modules/company/repositories.py`).

Not currently reachable in production: `DealHealthComputer` is defined and
has its own (fully mocked) unit test file, but is not registered in
`app/boot/startup.py::_init_feature_store`'s `FeatureStore(computers=[...])`
list alongside the other 7 computers — confirmed via a repo-wide grep with
zero results outside its own definition and test file. This DB-integration
test proves the fix is correct ahead of any future wiring decision; it does
not itself register or activate this computer.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from runtime.nba_engine.engine.risk.deal_health import DealHealthComputer


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_deal_health_signal_join_reads_real_tables():
    tenant_id = str(uuid.uuid4())
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Deal Health Test', :slug)"),
            {"id": tenant_id, "slug": f"dh-test-{tenant_id[:8]}"},
        )
        company_id = str(uuid.uuid4())
        await session.execute(
            text(
                "INSERT INTO companies (id, tenant_id, name_ar, status) "
                "VALUES (:id, :tid, 'شركة اختبار صحة الصفقة', 'active')"
            ),
            {"id": company_id, "tid": tenant_id},
        )
        opp_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        close_date = date.today() + timedelta(days=10)
        await session.execute(
            text(
                "INSERT INTO commercial_opportunities "
                "(id, tenant_id, company_id, name, stage, value, probability, "
                " status, expected_close_date, created_at, updated_at) "
                "VALUES (:id, :tid, :cid, 'Deal 1', 'negotiation', 100000, 0.6, "
                " 'open', :close_date, :now, :now)"
            ),
            {
                "id": opp_id,
                "tid": tenant_id,
                "cid": company_id,
                "close_date": close_date,
                "now": now,
            },
        )
        await session.execute(
            text(
                "INSERT INTO company_signals "
                "(id, tenant_id, company_id, signal_type, title, severity, "
                " source, status, first_seen_at, last_seen_at) "
                "VALUES (:id, :tid, :cid, 'hiring', 'New job postings', 'info', "
                " 'heuristic', 'active', :now, :now)"
            ),
            {"id": str(uuid.uuid4()), "tid": tenant_id, "cid": company_id, "now": now},
        )
        await session.commit()
        # GUC is transaction-local; commit() ended the transaction it was
        # pinned in, so it must be re-pinned before the next statement.
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )

        computer = DealHealthComputer()
        result = await computer.compute(
            {
                "id": opp_id,
                "tenant_id": tenant_id,
                "expected_close_date": close_date,
            },
            session,
        )

        # signal_count must be 1 (the join found the seeded signal) — the old
        # bug raised UndefinedFunctionError before this line was ever reached.
        assert result.contributing_signals["signal_count"] == 1
        # A deal closing 10 days out (well inside the <30-day tier) must
        # score a moderate, non-zero timeline_risk. If the date basis were
        # UTC instead of local (only observably different on a
        # positive-UTC-offset host, not this UTC-only container), the tier
        # boundaries would shift by up to a day — this assertion targets the
        # tier, not the exact day count, since this ephemeral container's own
        # clock is UTC.
        assert result.contributing_signals["timeline_risk"] == 0.2
        await session.rollback()
