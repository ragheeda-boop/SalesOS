"""PostgresForecastRepository silently dropped ForecastLine.metadata on
every round trip, and kpis() returned an ad-hoc look-alike object with
the wrong field names instead of the real ForecastKPIs dataclass.

Unlike reports 120-122 (StageEntry/Quote/Proposal), save()/get()/
_to_domain()'s core field mapping for ForecastSnapshot itself was
already correct when checked (matching report 123's Contract finding
that not every class in this file shares the crash-bug pattern). The
two real bugs here:

- `ForecastLine.metadata` (populated by the real forecasting engine
  with rep_id/region/product -- see domains/revenue/forecast/engine.py)
  was never included in save()'s JSON serialization nor reconstructed
  in _to_domain(). `ForecastSnapshot.by_dimension()` -- a real method
  that filters lines by this metadata -- silently returns [] for any
  forecast reloaded through this repository, even though the engine
  populated real metadata when the forecast was first created. Live and
  reachable: `ForecastService.finalize()`/`get_latest()`/`list_snapshots()`
  all round-trip through `_to_domain()`, and `commercial_forecast_snapshots.
  lines` is a schema-flexible JSON column, so this needed no migration
  to fix.
- `kpis()` built a dynamically-created `type("ForecastKPIs", (), {...})()`
  object -- not an instance of the real `ForecastKPIs` dataclass at all
  -- with field names (`total_expected`/`total_weighted`/`confidence`/
  `risk`) that match none of the real dataclass's fields
  (`total_snapshots`/`latest_expected_revenue`/`latest_weighted_revenue`/
  `latest_confidence`/`forecast_accuracy`/`forecast_bias`). Zero live
  callers and zero prior test coverage (confirmed via grep) -- fixed for
  parity with the in-memory reference repository, same precedent as
  reports 121/122/123's zero-caller kpis fixes.
"""

from __future__ import annotations

import uuid

import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from domains.commercial.infrastructure.postgres_repositories import (
    PostgresForecastRepository,
)
from domains.revenue.forecast.engine import CommercialInput
from domains.revenue.forecast.repo import ForecastKPIs
from domains.revenue.forecast.service import ForecastService


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    """Report 118/121 safety net."""
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
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Forecast Test', :slug)"),
        {"id": tenant_id, "slug": f"forecast-test-{tenant_id[:8]}"},
    )


async def test_line_metadata_round_trips_and_by_dimension_finds_it_after_reload():
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

        service = ForecastService(PostgresForecastRepository(session))
        inputs = [
            CommercialInput(
                opportunity_id="opp-1", opportunity_value=100000, opportunity_probability=0.5,
                rep_id="rep-42",
            )
        ]
        created = await service.create_forecast(tenant_id=tenant_id, inputs=inputs)
        # Sanity: the engine really did populate metadata before any save.
        assert created.lines
        assert created.lines[0].metadata.get("rep_id") == "rep-42"

        reloaded = await service.get(created.id)
        assert reloaded is not None
        assert reloaded.lines
        # This is the actual bug: metadata must survive the round trip for
        # by_dimension() to find anything.
        assert reloaded.lines[0].metadata.get("rep_id") == "rep-42"
        assert len(reloaded.by_dimension("rep_id", "rep-42")) == len(reloaded.lines)

        await session.rollback()


async def test_kpis_returns_the_real_dataclass_with_correct_fields():
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

        service = ForecastService(PostgresForecastRepository(session))
        inputs = [
            CommercialInput(opportunity_id="opp-a", opportunity_value=50000, opportunity_probability=0.6)
        ]
        await service.create_forecast(tenant_id=tenant_id, inputs=inputs)
        latest = await service.create_forecast(tenant_id=tenant_id, inputs=inputs)

        kpis = await service.kpis(tenant_id)
        assert isinstance(kpis, ForecastKPIs)
        assert kpis.total_snapshots == 2
        assert kpis.latest_expected_revenue == latest.total_expected_revenue
        assert kpis.latest_weighted_revenue == latest.total_weighted_revenue
        assert kpis.latest_confidence == latest.overall_confidence

        await session.rollback()
