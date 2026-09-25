from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.modules.master_data.muhide_adapter import bulk_insert_source_rows

EXPECTED_INSERTED_ROWS = 2


@pytest.mark.asyncio
async def test_bulk_insert_source_rows_reports_actual_insert_count():
    session = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(rowcount=EXPECTED_INSERTED_ROWS))
    )
    rows = [
        {"source_record_id": "row-1", "raw_payload": {"id": 1}},
        {"source_record_id": "row-2", "raw_payload": {"id": 2}},
        {"source_record_id": "row-3", "raw_payload": {"id": 3}},
    ]

    inserted = await bulk_insert_source_rows(
        session,
        tenant_id="tenant-test",
        source_file_id="file-test",
        source_id="test-source",
        rows=rows,
    )

    assert inserted == EXPECTED_INSERTED_ROWS
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_bulk_insert_source_rows_rejects_unknown_insert_count():
    session = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(rowcount=-1)))

    with pytest.raises(RuntimeError, match="did not report"):
        await bulk_insert_source_rows(
            session,
            tenant_id="tenant-test",
            source_file_id="file-test",
            source_id="test-source",
            rows=[{"source_record_id": "row-1", "raw_payload": {"id": 1}}],
        )
