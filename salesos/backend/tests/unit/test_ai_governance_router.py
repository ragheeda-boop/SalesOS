"""Tenant boundary and response-shape tests for the AI governance feed."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.modules.gtm.ai_governance_router import list_ai_governance_audit


class _Mappings:
    def all(self):
        return [
            {
                "id": 7,
                "user_id": "user-1",
                "action": "ai:policy:blocked",
                "resource_type": "ai:governance/policy",
                "resource_id": "policy-1",
                "outcome": "success",
                "request_id": "req-1",
                "created_at": datetime(2026, 9, 21, tzinfo=UTC),
                "policy_name": "Outbound safety",
                "decision": None,
                "enforcement_action": "blocked",
            }
        ]


class _RowsResult:
    def mappings(self):
        return _Mappings()


class _CountResult:
    def scalar_one(self):
        return 1


@pytest.mark.asyncio
async def test_ai_governance_feed_is_tenant_scoped_paginated_and_redacted():
    db = AsyncMock()
    db.execute.side_effect = [_CountResult(), _RowsResult()]

    result = await list_ai_governance_audit(
        page=2,
        page_size=10,
        tenant_id="tenant-1",
        db=db,
        _rbac=None,
    )

    assert result["total"] == 1
    assert result["page"] == 2
    assert result["read_only"] is True
    assert result["items"][0]["policy_name"] == "Outbound safety"
    assert "details" not in result["items"][0]
    assert "ip_address" not in result["items"][0]
    count_sql = str(db.execute.await_args_list[0].args[0])
    rows_sql = str(db.execute.await_args_list[1].args[0])
    assert "tenant_id = :tenant_id" in count_sql
    assert "resource_type LIKE 'ai:governance/%'" in rows_sql
    assert db.execute.await_args_list[1].args[1] == {
        "tenant_id": "tenant-1",
        "page_size": 10,
        "offset": 10,
    }
