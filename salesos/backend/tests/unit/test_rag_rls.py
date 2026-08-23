"""Phase 4A Part B — RAG Row-Level Security proofs (canonical DEC-085).

Uses REAL postgres via the app role (salesos_app, non-superuser) so policies
genuinely bite. Test documents/chunks are TRANSIENT: created under a pinned
tenant GUC, asserted against, then deleted in finally. Fixed UUIDs make
cleanup idempotent even after a crashed earlier run. No business corpus,
no persistent seed data.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session

NS = uuid.uuid5(uuid.NAMESPACE_URL, "phase4a-rag-rls-tests")

T_A = "a0000000-0000-4000-a000-000000000001"
T_B = "b0000000-0000-4000-a000-000000000002"

DOC_A1 = str(uuid.uuid5(NS, "doc-a1"))
DOC_A2 = str(uuid.uuid5(NS, "doc-a2"))
DOC_B1 = str(uuid.uuid5(NS, "doc-b1"))
CHUNK_A1 = str(uuid.uuid5(NS, "chunk-a1"))


async def _pin(db, tenant):
    await db.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant})


async def _seed():
    """Create 2 docs for A, 1 for B, 1 chunk under A's first doc."""
    async with async_session() as db:
        await _pin(db, T_A)
        await db.execute(
            text(
                "INSERT INTO rag_documents (id, tenant_id, source_type, source_id, "
                "title, content) VALUES (CAST(:i AS uuid), CAST(:t AS uuid), "
                "'test', 'x', 't', 'c') ON CONFLICT (id) DO NOTHING"
            ),
            {"i": DOC_A1, "t": T_A},
        )
        await db.execute(
            text(
                "INSERT INTO rag_documents (id, tenant_id, source_type, source_id, "
                "title, content) VALUES (CAST(:i AS uuid), CAST(:t AS uuid), "
                "'test', 'x', 't', 'c') ON CONFLICT (id) DO NOTHING"
            ),
            {"i": DOC_A2, "t": T_A},
        )
        await db.execute(
            text(
                "INSERT INTO rag_document_chunks (id, document_id, content, chunk_index) "
                "VALUES (CAST(:i AS uuid), CAST(:d AS uuid), 'c', 0) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"i": CHUNK_A1, "d": DOC_A1},
        )
        await db.commit()
    async with async_session() as db:
        await _pin(db, T_B)
        await db.execute(
            text(
                "INSERT INTO rag_documents (id, tenant_id, source_type, source_id, "
                "title, content) VALUES (CAST(:i AS uuid), CAST(:t AS uuid), "
                "'test', 'x', 't', 'c') ON CONFLICT (id) DO NOTHING"
            ),
            {"i": DOC_B1, "t": T_B},
        )
        await db.commit()


async def _cleanup():
    for t in (T_B, T_A):
        async with async_session() as db:
            await _pin(db, t)
            for doc in (DOC_A1, DOC_A2, DOC_B1):
                await db.execute(
                    text("DELETE FROM rag_document_chunks WHERE document_id=CAST(:d AS uuid)"),
                    {"d": doc},
                )
                await db.execute(
                    text("DELETE FROM rag_documents WHERE id=CAST(:i AS uuid)"),
                    {"i": doc},
                )
            await db.commit()


@pytest_asyncio.fixture(autouse=True)
async def _rag_seed_cleanup():
    await _cleanup()  # idempotent pre-clean (crashed-run leftovers)
    await _seed()
    yield
    await _cleanup()
    # each test gets its own asyncio loop; drop pooled connections bound to it
    from app.database import engine

    await engine.dispose()


async def _count_docs(tenant=None):
    async with async_session() as db:
        if tenant:
            await _pin(db, tenant)
        else:
            # explicitly ensure NO GUC is set on this connection
            await db.execute(text("SELECT set_config('app.tenant_id', '', false)"))
        rows = (
            await db.execute(
                text(
                    "SELECT id FROM rag_documents WHERE id IN (:a,:b,:c) ORDER BY id"
                ),
                {"a": DOC_A1, "b": DOC_A2, "c": DOC_B1},
            )
        ).all()
        return {str(r[0]) for r in rows}


@pytest.mark.asyncio
async def test_1_no_guc_sees_zero_rows():
    assert await _count_docs(tenant=None) == set()


@pytest.mark.asyncio
async def test_2_tenant_a_sees_only_a():
    seen = await _count_docs(T_A)
    assert seen == {DOC_A1, DOC_A2}


@pytest.mark.asyncio
async def test_3_tenant_a_cannot_read_b_doc():
    seen = await _count_docs(T_A)
    assert DOC_B1 not in seen


@pytest.mark.asyncio
async def test_4_tenant_b_cannot_read_a_docs():
    seen = await _count_docs(T_B)
    assert seen == {DOC_B1}


@pytest.mark.asyncio
async def test_5_chunk_access_cannot_bypass_document_tenancy():
    # read path: B cannot see a chunk whose parent belongs to A
    async with async_session() as db:
        await _pin(db, T_B)
        n = (
            await db.execute(
                text("SELECT COUNT(*) FROM rag_document_chunks WHERE id=:i"),
                {"i": CHUNK_A1},
            )
        ).scalar()
    assert n == 0
    # write path: B cannot attach a chunk to A's document (WITH CHECK EXISTS)
    async with async_session() as db:
        await _pin(db, T_B)
        with pytest.raises(Exception) as ei:
            await db.execute(
                text(
                    "INSERT INTO rag_document_chunks (id, document_id, content, "
                    "chunk_index) VALUES (CAST(:i AS uuid), CAST(:d AS uuid), 'x', 0)"
                ),
                {"i": str(uuid.uuid5(NS, "chunk-b-attempt")), "d": DOC_A1},
            )
        await db.rollback()
        assert "policy" in str(ei.value).lower() or "row-level" in str(ei.value).lower()


@pytest.mark.asyncio
async def test_6_app_level_filter_remains_compatible_under_guc():
    """The retrieval service filters `WHERE d.tenant_id = :tenant_id`; prove that
    query shape still returns correct rows when the GUC is also pinned."""
    from sqlalchemy import bindparam

    async with async_session() as db:
        await _pin(db, T_A)
        stmt = text(
            "SELECT d.id FROM rag_documents d WHERE d.tenant_id = :t AND d.id IN (:a,:b,:c)"
        ).bindparams(bindparam("t", type_=None))
        rows = (
            await db.execute(stmt, {"t": T_A, "a": DOC_A1, "b": DOC_A2, "c": DOC_B1})
        ).all()
        ids = {str(r[0]) for r in rows}
    assert DOC_B1 not in ids and {DOC_A1, DOC_A2} <= ids


@pytest.mark.asyncio
async def test_7_evidence_style_pin_then_query_works():
    """EvidencePack pins the GUC per transaction; same pattern must keep working
    for RAG reads (service/retrieval compatibility)."""
    got = await _count_docs(T_A)
    assert len(got) == 2


@pytest.mark.asyncio
async def test_8_force_rls_binds_even_table_owner_path():
    """FORCE ROW LEVEL SECURITY is set — the non-superuser app role cannot
    bypass policies by any plain SELECT/INSERT (proven implicitly by tests 1-5;
    here we assert the catalog state directly as a guard against drift)."""
    async with async_session() as db:
        rows = (
            await db.execute(
                text(
                    "SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity "
                    "FROM pg_class c WHERE c.relname IN "
                    "('rag_documents','rag_document_chunks')"
                )
            )
        ).all()
    state = {r[0]: (r[1], r[2]) for r in rows}
    assert state["rag_documents"] == (True, True)
    assert state["rag_document_chunks"] == (True, True)
