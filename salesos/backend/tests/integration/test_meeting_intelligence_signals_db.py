"""GET /api/v1/meetings/{opportunity_id}/brief returned an unhandled 500 on
every real call.

Mechanical finding, `domains/commercial/meeting/intelligence.py::
MeetingIntelligenceService.generate_brief()` — this is genuinely LIVE:
called from `app/routers/meetings.py`'s `GET /meetings/{opportunity_id}/brief`,
mounted at boot (`app/boot/routers.py`).

The recent-signals query compared `company_signals.company_id` (`uuid`)
directly against a subquery returning `commercial_opportunities.company_id`
(`varchar(36)`), with no cast — confirmed via direct reproduction:
`ERROR: operator does not exist: uuid = character varying`. Every real
call raised this, was caught by the router's own broad `except Exception`,
and surfaced as an unhandled 500 to the caller — the pre-meeting brief
feature has likely never worked. The existing unit test
(`test_meeting_intelligence.py`) mocks the session entirely
(`AsyncMock()`), so this had never been caught. Fixed by casting the
subquery's result to `uuid` (`company_id::uuid`), matching
`company_signals.company_id`'s real column type.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from domains.commercial.meeting.intelligence import MeetingIntelligenceService


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_generate_brief_includes_recent_signals_for_the_opportunitys_company():
    tenant_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    opportunity_id = str(uuid.uuid4())

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Meeting Intel Test', :slug)"),
            {"id": tenant_id, "slug": f"mi-test-{tenant_id[:8]}"},
        )
        await session.execute(
            text("""
                INSERT INTO companies (id, tenant_id, name_ar, name_en, industry, city, is_active)
                VALUES (:id, :tid, 'شركة', 'Meeting Co', 'Tech', 'Riyadh', true)
            """),
            {"id": company_id, "tid": tenant_id},
        )
        await session.execute(
            text("""
                INSERT INTO commercial_opportunities
                    (id, tenant_id, company_id, name, stage, value, probability, status, created_at, updated_at)
                VALUES (:oid, :tid, :cid, 'Deal', 'proposal', 50000, 0.5, 'open', now(), now())
            """),
            {"oid": opportunity_id, "tid": tenant_id, "cid": company_id},
        )
        await session.execute(
            text("""
                INSERT INTO company_signals
                    (tenant_id, company_id, signal_type, title, description, severity, source, status,
                     first_seen_at, last_seen_at)
                VALUES (:tid, :cid, 'growth', 'Growth signal', 'Company is expanding', 'high', 'heuristic',
                        'active', now(), now())
            """),
            {"tid": tenant_id, "cid": company_id},
        )
        await session.commit()

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        service = MeetingIntelligenceService(session, tenant_id)
        brief = await service.generate_brief(opportunity_id, company_id)

    assert brief["opportunity_name"] == "Deal"
    assert brief["company_name"] == "شركة"
    assert len(brief["recent_signals"]) == 1
    assert "Growth signal" in brief["recent_signals"][0]
