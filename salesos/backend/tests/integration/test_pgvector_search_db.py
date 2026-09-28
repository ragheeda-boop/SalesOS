"""sdk.search.PgVectorSearch had zero prior test coverage and zero live callers.

Reviewed against a fresh, fully-migrated database: `companies.embedding_vector`
is the only real backing column among all 8 ALLOWED_COLLECTIONS -- the stub
declared it as `embedding` (String), which does not exist on any of the 5
tables that exist at all, and the other 3 collections (`company_embeddings`,
`contact_embeddings`, `document_embeddings`) do not exist as tables at all.

test_upsert_and_search_round_trip_through_real_embedding_vector_column
proves the embedding_vector column-name/type/serialization fix in isolation,
against a scratch table shaped exactly like _embedding_table()'s stub
(id uuid, embedding_vector vector(3072), metadata jsonb) -- a genuine
`<=>` cosine-distance round trip through real pgvector, not a mock.
Isolation via a scratch table (rather than the real "companies" table) is
deliberate: see the next test for why "companies" cannot be used for this
at all, independent of the embedding_vector fix.

test_upsert_has_no_tenant_scoping_and_cannot_write_companies_at_all
documents (does not fix) a second, deeper, pre-existing gap discovered
while writing the first test: PgVectorSearch's entire public API
(search/upsert/delete) has no tenant_id parameter anywhere, and
_embedding_table()'s stub has no tenant_id column -- so upsert() cannot
write to ANY of the 5 real tenant-scoped tables in ALLOWED_COLLECTIONS
(companies/contacts/licenses/branches/opportunities all have a NOT NULL
tenant_id) even from the unrestricted owner/superuser role (a plain
NOT NULL violation, independent of RLS entirely) -- let alone under the
real, restricted application role (which additionally hits FORCE RLS on
top of that). This is a genuine API/architecture gap needing a design
decision (should the methods take an explicit tenant_id? should every
collection's stub carry one and pin the GUC?) that this session should not
decide unilaterally, matching the established precedent (reports
85/87/147/152/157).

Separately documented, not tested here: delete() issues an unconditional
`DELETE FROM <table> WHERE id = ...` -- for a shared-entity collection like
"companies" this deletes the entire business record, not just a search
index entry, which is almost certainly not the intended semantic if this
were ever wired to a real "remove this document from the index" caller.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import sdk.search as sdk_search
from sdk.search import PgVectorSearch

OWNER_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:55521/salesos_test"
SCRATCH_TABLE = "_test_pgvector_scratch"


@pytest_asyncio.fixture
async def owner_session_factory():
    engine = create_async_engine(OWNER_DATABASE_URL)
    async with engine.connect() as conn:
        db_name = await conn.scalar(text("SELECT current_database()"))
    assert db_name == "salesos_test", f"REFUSING: connected to {db_name!r}, expected salesos_test"
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest_asyncio.fixture
async def scratch_table(owner_session_factory):
    """A minimal table shaped exactly like _embedding_table()'s stub, with
    no tenant_id/RLS -- isolates the embedding_vector fix from the separate,
    documented-not-fixed tenant-scoping gap."""
    async with owner_session_factory() as session:
        await session.execute(
            text(
                f"CREATE TABLE {SCRATCH_TABLE} "
                "(id uuid PRIMARY KEY, embedding_vector vector(3072), metadata jsonb)"
            )
        )
        await session.commit()
    yield
    async with owner_session_factory() as session:
        await session.execute(text(f"DROP TABLE IF EXISTS {SCRATCH_TABLE}"))
        await session.commit()


@pytest.mark.asyncio
async def test_upsert_and_search_round_trip_through_real_embedding_vector_column(
    owner_session_factory, scratch_table, monkeypatch
) -> None:
    monkeypatch.setattr(sdk_search, "ALLOWED_COLLECTIONS", frozenset({SCRATCH_TABLE}))
    monkeypatch.setattr(PgVectorSearch, "_TABLE_MAP", {SCRATCH_TABLE: SCRATCH_TABLE})

    search = PgVectorSearch(session_factory=owner_session_factory)
    document_id = str(uuid.uuid4())
    vector = [0.1] * 3072

    await search.upsert(
        collection=SCRATCH_TABLE,
        document_id=document_id,
        vector=vector,
        metadata={"name": "Acme"},
    )

    results = await search.search(collection=SCRATCH_TABLE, vector=vector, top_k=5)

    assert len(results) == 1, "expected exactly the one upserted row back"
    assert results[0].id == document_id
    # Cosine distance of a vector against itself is 0 -> score = 1 - 0 = 1.0.
    assert results[0].score == pytest.approx(1.0, abs=1e-6)
    assert results[0].data == {"name": "Acme"}

    # A second upsert (ON CONFLICT DO UPDATE path) must not duplicate the row.
    await search.upsert(
        collection=SCRATCH_TABLE,
        document_id=document_id,
        vector=vector,
        metadata={"name": "Acme Updated"},
    )
    results_after_update = await search.search(collection=SCRATCH_TABLE, vector=vector, top_k=5)
    assert len(results_after_update) == 1
    assert results_after_update[0].data == {"name": "Acme Updated"}


@pytest.mark.asyncio
async def test_upsert_has_no_tenant_scoping_and_cannot_write_companies_at_all(
    owner_session_factory,
) -> None:
    """Documents a real, pre-existing gap: PgVectorSearch never supplies or
    pins tenant_id anywhere. Even using the unrestricted owner connection
    (bypassing RLS entirely), upsert() against "companies" cannot succeed
    at all -- companies.tenant_id is NOT NULL and this class has no way to
    provide it. This is reproduced, not assumed: if this test ever starts
    passing without a deliberate change to PgVectorSearch's tenant-scoping
    design, that signals the gap was closed and this finding should be
    revisited."""
    search = PgVectorSearch(session_factory=owner_session_factory)

    with pytest.raises(IntegrityError, match="tenant_id"):
        await search.upsert(
            collection="companies",
            document_id=str(uuid.uuid4()),
            vector=[0.1] * 3072,
            metadata={"name": "Acme"},
        )
