"""AttributionEngine had a real SQL injection, no tenant GUC pinning at all,
and never committed its writes.

Mechanical findings, `runtime/attribution/__init__.py` (never instantiated
anywhere in production — confirmed via repo-wide grep; this proves the fix
ahead of any future wiring decision):

1. **SQL injection, confirmed exploitable**: `attribute_email()`'s
   explicit_reference/contact_match/company_match/domain_match steps built
   raw SQL via Python f-string interpolation of `opp_ref` (extracted via
   regex from the raw, fully attacker-controlled email subject/body —
   anyone who can get an email delivered to a synced mailbox controls this
   text), `related_contact_ids`/`related_company_ids` (from synced email
   metadata), and `domain` (the sender's email address domain — also
   attacker-controlled). A subject containing
   ``[OPP-x' OR '1'='1' --]`` was reproduced, pre-fix, actually matching an
   unrelated real opportunity via a classic tautology + line-comment
   injection (not a synthetic claim — see report 74 for the exact captured
   `opportunity_id` this returned).
2. **No tenant GUC pinning anywhere in the file**: every query ran against
   RLS/FORCE-RLS-protected tables (`commercial_opportunities`,
   `opportunity_contacts`, `companies`, `activity_attributions`,
   `employee_email_events`) with no `app.tenant_id` GUC ever pinned — under
   the real restricted `salesos_app` role this fails closed to zero rows on
   every query, meaning the engine could never have matched anything at all,
   separately from the injection bug.
3. **`run_shadow_batch()` never called `session.commit()`**: every
   `INSERT INTO activity_attributions` this method performs would be
   silently discarded on normal `async with` exit (`AsyncSession.__aexit__`
   closes, it does not commit) — the method would report a nonzero
   `processed` count and persist nothing.
4. **A fourth, independent bug surfaced only once 1-3 were fixed**: the
   `activity_attributions` INSERT used `:param::jsonb` for four columns.
   SQLAlchemy's `text()` bind-parameter scanner does not recognize a name
   immediately followed by `::` as a bind parameter at all (confirmed in
   isolation) — every one of those four params was silently left as
   literal, uncompiled text, so the INSERT raised a hard
   `PostgresSyntaxError` on every real call. Fixed to
   `CAST(:param AS jsonb)`, matching this codebase's own established
   convention elsewhere. This bug could never have been observed before
   fixing 1-3, since with no GUC pinned the method never found anything to
   insert in the first place.

This test proves, end to end through `run_shadow_batch()` on a fresh
ephemeral database: (a) a legitimate explicit-reference email is correctly
attributed and durably persisted, (b) the specific injection payload that
was confirmed to succeed pre-fix now produces only the engine's own honest
"unresolved" fallthrough, never a real match, and (c) a same-shaped
legitimate opportunity in a different tenant is never cross-matched (also
resolving to the honest "unresolved" fallthrough, not silence).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from runtime.attribution import AttributionEngine


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


async def _seed_tenant_and_company(session, tenant_id: str) -> str:
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Attribution Test', :slug)"),
        {"id": tenant_id, "slug": f"attr-test-{tenant_id[:8]}"},
    )
    company_id = str(uuid.uuid4())
    await session.execute(
        text(
            "INSERT INTO companies (id, tenant_id, name_ar, status) "
            "VALUES (:id, :tid, 'شركة اختبار الإسناد', 'active')"
        ),
        {"id": company_id, "tid": tenant_id},
    )
    return company_id


async def _seed_opportunity(session, tenant_id: str, company_id: str, name: str) -> str:
    opp_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    await session.execute(
        text(
            "INSERT INTO commercial_opportunities "
            "(id, tenant_id, company_id, name, stage, value, probability, "
            " status, created_at, updated_at) "
            "VALUES (:id, :tid, :cid, :name, 'prospecting', 10000, 0.1, "
            " 'open', :now, :now)"
        ),
        {"id": opp_id, "tid": tenant_id, "cid": company_id, "name": name, "now": now},
    )
    return opp_id


async def _seed_email(
    session, tenant_id: str, subject: str, from_address: str = "sender@example.com"
) -> str:
    email_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    await session.execute(
        text(
            "INSERT INTO employee_email_events "
            "(id, employee_id, tenant_id, provider, provider_message_id, direction, "
            " from_address, subject, timestamp_utc, created_at, updated_at) "
            "VALUES (:id, :eid, :tid, 'gmail', :pmid, 'inbound', "
            " :from_addr, :subject, :now, :now, :now)"
        ),
        {
            "id": email_id,
            "eid": str(uuid.uuid4()),
            "tid": tenant_id,
            "pmid": f"msg-{email_id[:8]}",
            "from_addr": from_address,
            "subject": subject,
            "now": now,
        },
    )
    return email_id


@pytest.mark.asyncio
async def test_legitimate_reference_is_attributed_and_persists():
    tenant_id = str(uuid.uuid4())
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        company_id = await _seed_tenant_and_company(session, tenant_id)
        opp_id = await _seed_opportunity(session, tenant_id, company_id, "Deal ABC123")
        await _seed_email(session, tenant_id, subject="Re: [OPP-ABC123] follow up")
        await session.commit()
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )

        engine_svc = AttributionEngine(session_factory=async_session)
        processed = await engine_svc.run_shadow_batch(tenant_id, limit=10)
        assert processed == 1

        # Must be durably persisted (not silently discarded by a missing commit).
        rows = await session.execute(
            text(
                "SELECT opportunity_id, resolution_method FROM activity_attributions "
                "WHERE tenant_id = :tid"
            ),
            {"tid": tenant_id},
        )
        persisted = rows.mappings().all()
        assert len(persisted) == 1
        assert persisted[0]["opportunity_id"] == opp_id
        assert persisted[0]["resolution_method"] == "explicit_reference"
        await session.rollback()


@pytest.mark.asyncio
async def test_injection_shaped_subject_does_not_execute_as_sql():
    tenant_id = str(uuid.uuid4())
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        company_id = await _seed_tenant_and_company(session, tenant_id)
        # A real opportunity that a successful injection could have surfaced
        # or corrupted matching against.
        await _seed_opportunity(session, tenant_id, company_id, "Unrelated Deal")
        # Classic tautology-injection shape embedded in the only place this
        # engine ever regex-extracts from raw, attacker-controlled text.
        await _seed_email(
            session, tenant_id, subject="[OPP-x' OR '1'='1' --]"
        )
        await session.commit()
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )

        engine_svc = AttributionEngine(session_factory=async_session)
        # Must not raise (a real injection payload reaching the DB as literal
        # SQL would either error out on malformed syntax or, if it happened
        # to parse, could return unrelated rows -- this asserts neither). The
        # engine's own contract records every email's outcome even when
        # unresolved (shadow mode) -- so processed==1 here is correct by
        # design; what must never happen is a *real* opportunity_id/company
        # match surfacing through the injected payload.
        processed = await engine_svc.run_shadow_batch(tenant_id, limit=10)
        assert processed == 1

        rows = await session.execute(
            text(
                "SELECT opportunity_id, resolution_state FROM activity_attributions "
                "WHERE tenant_id = :tid"
            ),
            {"tid": tenant_id},
        )
        persisted = rows.mappings().all()
        assert len(persisted) == 1
        # The injection payload must never resolve to a real opportunity —
        # only the honest "unresolved" fallthrough is acceptable.
        assert persisted[0]["opportunity_id"] == ""
        assert persisted[0]["resolution_state"] == "unresolved"
        await session.rollback()


@pytest.mark.asyncio
async def test_cross_tenant_opportunity_is_never_matched():
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_a}
        )
        company_a = await _seed_tenant_and_company(session, tenant_a)
        await session.commit()

        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_b}
        )
        company_b = await _seed_tenant_and_company(session, tenant_b)
        # Same reference token in tenant B, must never resolve for tenant A.
        await _seed_opportunity(session, tenant_b, company_b, "Deal XYZ999")
        await session.commit()

        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_a}
        )
        await _seed_email(session, tenant_a, subject="Re: [OPP-XYZ999] any progress?")
        await session.commit()
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_a}
        )

        engine_svc = AttributionEngine(session_factory=async_session)
        processed = await engine_svc.run_shadow_batch(tenant_a, limit=10)
        assert processed == 1

        # Fail-closed: tenant A's session must never see tenant B's
        # "Deal XYZ999" opportunity — the engine's own honest "unresolved"
        # fallthrough is the only acceptable outcome, never a real match.
        rows = await session.execute(
            text(
                "SELECT opportunity_id, resolution_state FROM activity_attributions "
                "WHERE tenant_id = :tid"
            ),
            {"tid": tenant_a},
        )
        persisted = rows.mappings().all()
        assert len(persisted) == 1
        assert persisted[0]["opportunity_id"] == ""
        assert persisted[0]["resolution_state"] == "unresolved"
        await session.rollback()
