"""POST /api/v1/data-fabric/ingest -> DataFabricPipeline.run_batch().

Every session in the pipeline was opened without pinning app.tenant_id.
golden_records and companies are FORCE-RLS, so entity resolution failed its
WITH CHECK on the first insert; the endpoint still answered 201 with
golden_records_created=0 and the error buried in `errors`. Separately, the
embedding stage wrote to a nonexistent `companies.embedding` column (real
column: embedding_vector), so no embedding was ever stored.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from runtime.data_fabric_runtime import DataFabricPipeline


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


class _FakeEmbeddings:
    async def embed(self, _text: str) -> list[float]:
        v = [0.0] * 3072
        v[3] = 1.0
        return v


async def _tenant() -> str:
    tid = str(uuid.uuid4())
    async with async_session() as s:
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tid})
        await s.execute(text("INSERT INTO tenants (id, name, slug) VALUES (:i, 'DF', :s)"),
                        {"i": tid, "s": f"df-{tid[:8]}"})
        await s.commit()
    return tid


async def _count(tid: str, sql: str) -> int:
    async with async_session() as s:
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tid})
        return (await s.execute(text(sql), {"t": tid})).scalar_one()


@pytest.mark.asyncio
async def test_ingest_creates_golden_record_company_and_embedding():
    tid, other = await _tenant(), await _tenant()
    pipeline = DataFabricPipeline(session_factory=async_session, embedding_service=_FakeEmbeddings())
    result = await pipeline.run_batch(
        source_slug="manual",
        records=[{"cr_number": "1010999888", "name_ar": "شركة التكامل", "name_en": "Fabric Co",
                  "city": "Riyadh"}],
        tenant_id=tid,
    )
    assert result["errors"] == []
    assert result["golden_records_created"] == 1
    assert await _count(tid, "SELECT count(*) FROM golden_records WHERE tenant_id = :t") == 1
    assert await _count(tid, "SELECT count(*) FROM companies WHERE tenant_id = :t") == 1
    assert await _count(
        tid, "SELECT count(*) FROM companies WHERE tenant_id = :t AND embedding_vector IS NOT NULL") == 1
    # Tenant isolation holds for the other tenant.
    assert await _count(other, "SELECT count(*) FROM companies") == 0
    assert await _count(other, "SELECT count(*) FROM golden_records") == 0
