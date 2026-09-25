"""Unit checks for the tenant-scoped AI Studio document repository."""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock

import pytest

from app.modules.tenant_studio.postgres_store import PostgresTenantStudioStore


class _Mappings:
    def __init__(self, row):
        self._row = row

    def one_or_none(self):
        return self._row

    def all(self):
        return self._row

    def one(self):
        return self._row


class _Result:
    def __init__(self, row=None):
        self._row = row

    def mappings(self):
        return _Mappings(self._row)

    def scalar_one_or_none(self):
        return self._row


@pytest.mark.asyncio
async def test_replace_binds_tenant_type_and_expected_version():
    tenant_id = uuid.uuid4()
    payload = {"id": "prompt-1", "tenant_id": str(tenant_id), "key": "gtm.opening"}
    db = AsyncMock()
    db.execute.return_value = _Result({"payload": payload})

    result = await PostgresTenantStudioStore(db).replace_if_version(
        tenant_id=str(tenant_id),
        document_type="prompt_library",
        document_key="prompt-1",
        payload=payload,
        expected_schema_version=3,
        logical_key="gtm.opening",
    )

    assert result == payload
    statement, params = db.execute.await_args.args
    assert "AND schema_version = :expected_schema_version" in str(statement)
    assert params["tenant_id"] == tenant_id
    assert params["document_type"] == "prompt_library"
    assert params["logical_key"] == "gtm.opening"
    assert params["expected_schema_version"] == 3
    assert json.loads(params["payload"]) == payload


@pytest.mark.asyncio
async def test_create_returns_none_for_unique_conflict():
    tenant_id = uuid.uuid4()
    db = AsyncMock()
    db.execute.return_value = _Result(None)

    result = await PostgresTenantStudioStore(db).create(
        tenant_id=str(tenant_id),
        document_type="prompt_library",
        document_key="prompt-2",
        payload={"id": "prompt-2"},
        logical_key="gtm.opening",
    )

    assert result is None
    assert "ON CONFLICT DO NOTHING" in str(db.execute.await_args.args[0])


@pytest.mark.asyncio
async def test_invalid_tenant_id_fails_before_query():
    db = AsyncMock()

    with pytest.raises(ValueError, match="tenant_id must be a UUID"):
        await PostgresTenantStudioStore(db).list_for_tenant(
            tenant_id="not-a-uuid", document_type="ai_policies"
        )

    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_returns_true_only_when_row_was_deleted():
    db = AsyncMock()
    db.execute.return_value = _Result("prompt-3")

    deleted = await PostgresTenantStudioStore(db).delete(
        tenant_id=str(uuid.uuid4()),
        document_type="prompt_library",
        document_key="prompt-3",
    )

    assert deleted is True
    assert "tenant_id = :tenant_id" in str(db.execute.await_args.args[0])
