"""upsert_signals() had 2 independent bugs — one broke every real call
with extra signal fields, the other broke the exact "persist then read
back on the same request" pattern its one real caller uses.

Mechanical findings, `app/modules/company/signal_persistence.py` —
genuinely LIVE: called from `app/modules/company/service.py`'s Company 360
view (`upsert_signals()` then `read_signals()` on the SAME
request-injected session, "Read back from DB for lifecycle-enriched
view") and from `app/modules/signal_marketplace/runtime_bridge.py` (its
own standalone session).

1. **`str(metadata)` is not valid JSON.** `company_signals.metadata` is
   `jsonb`; the code passed `str(metadata)` (Python dict repr, single-
   quoted keys) as the bind value. Every real signal with any field
   beyond type/severity/title/description/source/confidence_score (i.e.
   any signal with a genuinely non-empty `metadata` payload) failed the
   INSERT with an invalid-JSON error, silently caught by the per-signal
   `except Exception` and logged as `upsert_failed` — `persisted` stayed
   `0`. Reproduced directly before any fix: a signal dict with one extra
   field always failed to persist. Fixed with `json.dumps(metadata)` and
   an explicit `CAST(:meta AS jsonb)`.
2. **`upsert_signals()` calls `db.commit()` on a session it does not
   own**, and `apply_tenant_guc()` pins `app.tenant_id` transaction-locally
   (`is_local=true`, DEC-085) — a commit ends that transaction and clears
   the GUC. `company/service.py`'s Company 360 view reuses the SAME
   request-scoped session for `read_signals()` immediately afterward to
   build its "lifecycle-enriched" response; without re-pinning, that read
   is silently RLS-blocked (`company_signals` has FORCE RLS) and always
   returned `[]` — signals a request had just written were invisible to
   that same request's own follow-up read. Reproduced directly: after
   fixing bug 1 alone, `read_signals()` on the same session still
   returned `[]` immediately after a successful `upsert_signals()`. Fixed
   by calling `apply_tenant_guc(db, tenant_id)` again immediately after
   each internal `db.commit()` (present in all 4 of this module's
   mutating functions).
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from app.modules.company.signal_persistence import (
    acknowledge_signal,
    read_signals,
    upsert_signals,
)


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


async def _seed(tenant_id: str, company_id: str) -> None:
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Signal Persist Test', :slug)"),
            {"id": tenant_id, "slug": f"sp-test-{tenant_id[:8]}"},
        )
        await session.execute(
            text("INSERT INTO companies (id, tenant_id, name_ar, is_active) VALUES (:id, :tid, 'شركة', true)"),
            {"id": company_id, "tid": tenant_id},
        )
        await session.commit()


@pytest.mark.asyncio
async def test_upsert_then_read_on_the_same_session_sees_the_persisted_signal():
    """Reproduces company/service.py's exact call pattern: upsert, then
    read back on the SAME session in the SAME logical request."""
    tenant_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    await _seed(tenant_id, company_id)

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )

        count = await upsert_signals(
            session, tenant_id=tenant_id, company_id=company_id,
            signals=[{
                "type": "growth", "severity": "high", "title": "Growth signal",
                "extra_field": "extra_value",
            }],
        )
        assert count == 1

        persisted = await read_signals(session, tenant_id=tenant_id, company_id=company_id)
        assert len(persisted) == 1
        assert persisted[0]["signal_type"] == "growth"
        assert persisted[0]["metadata"] == {"extra_field": "extra_value"}


@pytest.mark.asyncio
async def test_upsert_with_metadata_does_not_silently_fail():
    tenant_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    await _seed(tenant_id, company_id)

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        count = await upsert_signals(
            session, tenant_id=tenant_id, company_id=company_id,
            signals=[
                {"type": "a", "severity": "info", "title": "A", "custom": 1},
                {"type": "b", "severity": "info", "title": "B", "custom": {"nested": True}},
            ],
        )
        assert count == 2


@pytest.mark.asyncio
async def test_acknowledge_then_read_on_the_same_session_sees_the_update():
    tenant_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    await _seed(tenant_id, company_id)

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await upsert_signals(
            session, tenant_id=tenant_id, company_id=company_id,
            signals=[{"type": "risk", "severity": "high", "title": "Risk"}],
        )
        rows = await read_signals(session, tenant_id=tenant_id, company_id=company_id)
        signal_id = str(rows[0]["id"])

        ok = await acknowledge_signal(session, tenant_id=tenant_id, signal_id=signal_id)
        assert ok is True

        after = await read_signals(session, tenant_id=tenant_id, company_id=company_id)
        assert after[0]["status"] == "acknowledged"
