"""Database proof for opportunity-note tenant isolation and fail-closed RLS."""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from app.routers.commercial import (
    OpportunityNoteCreateBody,
    create_opportunity_note,
    list_opportunity_notes,
)


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


async def _set_tenant(conn, tenant_id: str | None) -> None:
    if tenant_id:
        await conn.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": tenant_id},
        )
    else:
        await conn.execute(text("RESET app.tenant_id"))


async def _insert_opportunity(conn, tenant_id: str, suffix: str) -> str:
    opportunity_id = str(uuid.uuid4())
    await _set_tenant(conn, tenant_id)
    await conn.execute(
        text(
            "INSERT INTO commercial_opportunities (id, tenant_id, company_id, name) "
            "VALUES (:id, :tenant_id, :company_id, :name)"
        ),
        {
            "id": opportunity_id,
            "tenant_id": tenant_id,
            "company_id": f"company-{suffix}",
            "name": f"Opportunity {suffix}",
        },
    )
    return opportunity_id


@pytest.mark.asyncio
async def test_opportunity_notes_are_tenant_scoped_and_fail_closed():
    async with engine.begin() as conn:
        tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
        for tenant_id, suffix in ((tenant_a, "a"), (tenant_b, "b")):
            await conn.execute(
                text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
                {
                    "id": tenant_id,
                    "name": f"Opportunity Note {suffix.upper()}",
                    "slug": f"opp-notes-{suffix}-{tenant_id[:8]}",
                },
            )
        opportunity_a = await _insert_opportunity(conn, tenant_a, "a")
        opportunity_b = await _insert_opportunity(conn, tenant_b, "b")
        for tenant_id, opportunity_id, suffix in (
            (tenant_a, opportunity_a, "a"),
            (tenant_b, opportunity_b, "b"),
        ):
            await _set_tenant(conn, tenant_id)
            await conn.execute(
                text(
                    "INSERT INTO commercial_opportunity_notes "
                    "(id, tenant_id, opportunity_id, author_id, body, idempotency_key) "
                    "VALUES (:id, :tenant_id, :opportunity_id, :author_id, :body, :key)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "opportunity_id": opportunity_id,
                    "author_id": f"seller-{suffix}",
                    "body": f"note-{suffix}",
                    "key": f"retry-{suffix}",
                },
            )

        await _set_tenant(conn, tenant_a)
        own_count = (await conn.execute(text("SELECT count(*) FROM commercial_opportunity_notes"))).scalar()
        cross_count = (
            await conn.execute(
                text("SELECT count(*) FROM commercial_opportunity_notes WHERE opportunity_id = :id"),
                {"id": opportunity_b},
            )
        ).scalar()
        assert own_count == 1
        assert cross_count == 0
        await _set_tenant(conn, None)
        assert (await conn.execute(text("SELECT count(*) FROM commercial_opportunity_notes"))).scalar() == 0
        await conn.rollback()


@pytest.mark.asyncio
async def test_note_handler_uses_authenticated_author_and_is_idempotent():
    """The HTTP handler's core path stores one note for a retried request."""
    async with async_session() as session:
        tenant_id = str(uuid.uuid4())
        opportunity_id = str(uuid.uuid4())
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
            {
                "id": tenant_id,
                "name": "Opportunity Note Handler",
                "slug": f"opp-handler-{tenant_id[:8]}",
            },
        )
        await _set_tenant(session, tenant_id)
        await session.execute(
            text(
                "INSERT INTO commercial_opportunities (id, tenant_id, company_id, name) "
                "VALUES (:id, :tenant_id, :company_id, :name)"
            ),
            {
                "id": opportunity_id,
                "tenant_id": tenant_id,
                "company_id": "company-handler",
                "name": "Handler Opportunity",
            },
        )
        payload = OpportunityNoteCreateBody(text="Seller-confirmed discovery", idempotency_key="retry-1")
        first = await create_opportunity_note(
            opportunity_id, payload, tenant_id, "authenticated-seller", session, True
        )
        second = await create_opportunity_note(
            opportunity_id, payload, tenant_id, "untrusted-client-author", session, True
        )
        notes = await list_opportunity_notes(opportunity_id, tenant_id, session, True)

        assert first["id"] == second["id"]
        assert first["author_id"] == "authenticated-seller"
        assert notes["items"] == [first]
        await session.rollback()
