"""Regression: Activity Intelligence readers must scope all queries by tenant_id."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from intelligence.activity_intelligence.readers.postgres_readers import (
    PostgresEmailReader,
    PostgresMeetingReader,
)


def _capturing_db(row: dict | None = None):
    captured: list[dict] = []
    mock_db = AsyncMock()
    result = MagicMock()
    mapping = MagicMock()
    mapping.first.return_value = row
    mapping.all.return_value = [row] if row else []
    mapping.one.return_value = {"c": 0, "minutes": 0}
    result.mappings.return_value = mapping

    async def execute(sql, params=None):
        sql_text = str(getattr(sql, "text", sql))
        captured.append({"sql": sql_text, "params": dict(params or {})})
        return result

    mock_db.execute = execute
    mock_db._captured = captured
    return mock_db


def _assert_tenant_scoped(cap: dict, tenant_id: str) -> None:
    assert "tenant_id" in cap["sql"]
    assert ":tid" in cap["sql"]
    assert cap["params"].get("tid") == tenant_id
    # Cross-tenant guard: SQL must bind tenant, not omit it.
    assert "WHERE" in cap["sql"].upper() or "where" in cap["sql"]


@pytest.mark.asyncio
async def test_email_get_requires_tenant_filter():
    email_id = str(uuid4())
    tenant_id = str(uuid4())
    db = _capturing_db(
        {
            "id": email_id,
            "subject": "x",
            "direction": "inbound",
            "from_address": "a@b.c",
            "sent_at": None,
        }
    )
    reader = PostgresEmailReader(db)
    await reader.get(email_id, tenant_id)
    cap = db._captured[-1]
    _assert_tenant_scoped(cap, tenant_id)
    assert cap["params"].get("id") == email_id


@pytest.mark.asyncio
async def test_email_list_by_company_requires_tenant_filter():
    tenant_a = str(uuid4())
    company_b = str(uuid4())
    db = _capturing_db()
    reader = PostgresEmailReader(db)
    await reader.list_by_company(company_b, tenant_a, limit=10)
    cap = db._captured[-1]
    _assert_tenant_scoped(cap, tenant_a)
    assert cap["params"].get("company_id") == company_b


@pytest.mark.asyncio
async def test_email_count_by_company_requires_tenant_filter():
    tenant_a = str(uuid4())
    company_b = str(uuid4())
    db = _capturing_db()
    reader = PostgresEmailReader(db)
    await reader.count_by_company(company_b, tenant_a)
    await reader.count_by_company(company_b, tenant_a, direction="inbound")
    for cap in db._captured:
        _assert_tenant_scoped(cap, tenant_a)
        assert cap["params"].get("company_id") == company_b
    assert db._captured[-1]["params"].get("direction") == "inbound"
    # No f-string interpolation of direction into SQL text.
    assert ":direction" in db._captured[-1]["sql"]


@pytest.mark.asyncio
async def test_email_last_and_employee_count_require_tenant():
    tenant_a = str(uuid4())
    company_b = str(uuid4())
    employee_c = str(uuid4())
    db = _capturing_db()
    reader = PostgresEmailReader(db)
    await reader.last_email(company_b, tenant_a)
    await reader.count_by_employee(employee_c, tenant_a)
    await reader.count_by_employee(employee_c, tenant_a, direction="outbound")
    for cap in db._captured:
        _assert_tenant_scoped(cap, tenant_a)


@pytest.mark.asyncio
async def test_meeting_get_requires_tenant_filter():
    meeting_id = str(uuid4())
    tenant_id = str(uuid4())
    db = _capturing_db(
        {
            "id": meeting_id,
            "title": "x",
            "date": None,
            "duration_minutes": 30,
            "status": "completed",
        }
    )
    reader = PostgresMeetingReader(db)
    await reader.get(meeting_id, tenant_id)
    cap = db._captured[-1]
    _assert_tenant_scoped(cap, tenant_id)
    assert cap["params"].get("id") == meeting_id


@pytest.mark.asyncio
async def test_meeting_company_and_employee_methods_require_tenant():
    tenant_a = str(uuid4())
    company_b = str(uuid4())
    employee_c = str(uuid4())
    db = _capturing_db()
    reader = PostgresMeetingReader(db)
    await reader.list_by_company(company_b, tenant_a)
    await reader.count_by_company(company_b, tenant_a)
    await reader.last_meeting(company_b, tenant_a)
    await reader.count_by_employee(employee_c, tenant_a)
    await reader.hours_by_employee(employee_c, tenant_a)
    assert len(db._captured) == 5
    for cap in db._captured:
        _assert_tenant_scoped(cap, tenant_a)


@pytest.mark.asyncio
async def test_tenant_a_params_never_use_tenant_b_id():
    """Simulate Tenant A lookup: bound tid must be A, never B."""
    tenant_a = str(uuid4())
    tenant_b = str(uuid4())
    email_id = str(uuid4())
    db = _capturing_db({"id": email_id})
    reader = PostgresEmailReader(db)
    await reader.get(email_id, tenant_a)
    cap = db._captured[-1]
    assert cap["params"]["tid"] == tenant_a
    assert cap["params"]["tid"] != tenant_b
    assert tenant_b not in cap["sql"]
