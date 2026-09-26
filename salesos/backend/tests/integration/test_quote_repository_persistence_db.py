"""PostgresQuoteRepository crashed on every real call: it read/constructed
fields that do not exist on the `Quote` domain contract.

Mechanical finding, same class as report 120 (StageEntry): the domain
contract (contracts/models.py) has `lines: list[QuoteLine]` and
`approval: ApprovalState` (with `approval.approved_by`/`approval.approved_at`
nested inside), and computes `grand_total` from `lines` -- there is no
top-level `total_value`/`sent_at`/`approved_by`/`approved_at`/`accepted_at`
on `Quote` at all. `QuoteModel` (table `commercial_quotes`, FORCE RLS)
denormalizes exactly those workflow timestamps as flat columns. The
repository read/wrote the DB-model's flat names directly against the
contract object (`quote.total_value`, `quote.sent_at`, `quote.approved_by`,
...), which do not exist -- `AttributeError` on every `save()`, and
`TypeError` on every `get()`/`get_by_opportunity()`/`list_by_tenant()`
(constructing `Quote(total_value=..., sent_at=..., ...)` with keyword
arguments the constructor does not accept).

`PostgresQuoteRepository` is wired live via app/routers/commercial.py's
`_get_pipe`-sibling `_get_quote(db)` factory
(`QuoteService(PostgresQuoteRepository(db))`) -- every real call to
`QuoteService.create_quote()`/`add_line()`/`submit_for_approval()`/
`approve()`/`send()`/`accept()` would have crashed on its first
`self._repository.save(quote)`.

A second bug: `quote.lines` (the actual line items) were never persisted
at all -- `save()` never touched `commercial_quote_lines`, so even a
hypothetically-fixed round trip would silently lose every line item.
"""

from __future__ import annotations

import uuid

import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from domains.commercial.infrastructure.postgres_repositories import (
    PostgresQuoteRepository,
)
from domains.commercial.quote.contracts.models import QuoteStatus
from domains.commercial.quote.engine.service import QuoteService


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    """Report 118 safety net: a bare host-side pytest run of this file that
    exports only DATABASE_URL silently targets the persistent local dev
    Postgres (this repo's checked-in .env sets APP_POSTGRES_PASSWORD, which
    takes precedence over DATABASE_URL for app.database.engine). Caught
    live once already for a different file; run with APP_POSTGRES_PASSWORD=""
    (or APP_DATABASE_URL_OVERRIDE) set to the intended disposable database.
    """
    async with engine.connect() as conn:
        db_name = await conn.scalar(text("SELECT current_database()"))
    assert db_name != "salesos", (
        f"REFUSING: connected to {db_name!r} — this is the persistent "
        "local dev database, not a disposable/test one. Set "
        'APP_POSTGRES_PASSWORD="" (or APP_DATABASE_URL_OVERRIDE) to point '
        "app.database.engine at an ephemeral container before running "
        "this file."
    )
    yield
    await engine.dispose()


async def _seed_tenant(session, tenant_id: str) -> None:
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Quote Test', :slug)"),
        {"id": tenant_id, "slug": f"quote-test-{tenant_id[:8]}"},
    )


async def test_quote_full_lifecycle_persists_and_reloads_correctly():
    tenant_id = str(uuid.uuid4())

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await _seed_tenant(session, tenant_id)
        await session.commit()
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )

        service = QuoteService(PostgresQuoteRepository(session))

        quote = await service.create_quote(
            tenant_id=tenant_id, title="Test Quote", created_by="seller-1"
        )
        assert quote.status == QuoteStatus.DRAFT

        await service.add_line(quote.id, "Widget A", quantity=2, unit_price=100.0)
        await service.add_line(quote.id, "Widget B", quantity=1, unit_price=50.0)

        reloaded = await service._repository.get(quote.id)
        assert reloaded is not None
        assert len(reloaded.lines) == 2
        assert reloaded.grand_total == 250.0

        await service.submit_for_approval(quote.id)
        await service.approve(quote.id, approved_by="manager-1", comments="looks good")

        approved = await service._repository.get(quote.id)
        assert approved.status == QuoteStatus.APPROVED
        assert approved.approval.approved_by == "manager-1"
        assert approved.approval.approved_at is not None
        # Lines must survive every intermediate save() untouched.
        assert len(approved.lines) == 2

        await service.send(quote.id)
        sent_row = (
            await session.execute(
                text("SELECT sent_at, total_value FROM commercial_quotes WHERE id = :id"),
                {"id": quote.id},
            )
        ).one()
        assert sent_row.sent_at is not None
        assert sent_row.total_value == 250.0

        await service.accept(quote.id)
        accepted_row = (
            await session.execute(
                text("SELECT accepted_at, status FROM commercial_quotes WHERE id = :id"),
                {"id": quote.id},
            )
        ).one()
        assert accepted_row.accepted_at is not None
        assert accepted_row.status == "accepted"

        line_count = await session.scalar(
            text("SELECT COUNT(*) FROM commercial_quote_lines WHERE quote_id = :id"),
            {"id": quote.id},
        )
        assert line_count == 2

        kpis = await service.revenue_kpis(tenant_id)
        assert kpis.total_quotes == 1
        assert kpis.accepted_quotes == 1
        assert kpis.total_quote_value == 250.0

        await session.rollback()
