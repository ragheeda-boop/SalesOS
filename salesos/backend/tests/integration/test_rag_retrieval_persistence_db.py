"""RetrievalService (live at /api/v1/rag/*) never persisted or retrieved
anything from PostgreSQL.

`intelligence/rag/retrieval.py` wrote binds as ``:vector::vector``,
``:embedding::vector`` and ``:metadata::jsonb``. SQLAlchemy's ``text()``
does not recognise a bind name immediately followed by ``::`` (same quirk
as reports 74/75/82), so every statement was a syntax error. Both
``store_document_chunks()`` and ``_retrieve_pgvector()`` swallow the error
and fall back to a per-instance in-memory dict. /rag/ingest therefore
reported success while writing nothing durable, and /rag/ask could never
find a stored chunk.

The session is pinned exactly as the request-scoped ``get_db`` session is.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import apply_tenant_guc, async_session, engine
from domains.rag.models import Document, DocumentChunk
from intelligence.rag.retrieval import RetrievalService

DIM = 3072


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


def _vec(hot: int) -> list[float]:
    v = [0.0] * DIM
    v[hot] = 1.0
    return v


@pytest.mark.asyncio
async def test_ingested_chunks_are_persisted_and_retrievable():
    tenant = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    doc = Document(id=doc_id, tenant_id=tenant, source_type="note", source_id="n-1",
                   title="Pricing note", content="Enterprise tier pricing", metadata={"k": "v"})
    chunk = DocumentChunk(id=str(uuid.uuid4()), document_id=doc_id,
                          content="Enterprise tier pricing", embedding=_vec(7), metadata={"i": 0})

    async with async_session() as s:
        await apply_tenant_guc(s, tenant)
        await RetrievalService(s).store_document_chunks(doc, [chunk])

    # A fresh service + session (as a later request would have) must see it.
    async with async_session() as s:
        await apply_tenant_guc(s, tenant)
        n = (await s.execute(text("SELECT count(*) FROM rag_document_chunks WHERE document_id = :d"),
                             {"d": doc_id})).scalar_one()
        assert n == 1
        results = await RetrievalService(s).retrieve(_vec(7), tenant, top_k=3, min_score=0.5)
        assert [r.chunk.content for r in results] == ["Enterprise tier pricing"]
        assert results[0].score == pytest.approx(1.0)

    # Another tenant sees nothing.
    other = str(uuid.uuid4())
    async with async_session() as s:
        await apply_tenant_guc(s, other)
        assert await RetrievalService(s).retrieve(_vec(7), other, top_k=3, min_score=0.5) == []
