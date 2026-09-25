"""Tenant boundary and serialization tests for commercial evidence reads."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.modules.gtm.evidence_router import list_evidence_insights


class _Result:
    def __init__(self, rows=None, count=None):
        self._rows = rows or []
        self._count = count

    def scalar_one(self):
        return self._count

    def mappings(self):
        return self

    def all(self):
        return self._rows


@pytest.mark.asyncio
async def test_evidence_read_returns_source_chain_scoped_to_tenant():
    created_at = datetime(2026, 9, 21, tzinfo=UTC)
    db = AsyncMock()
    db.execute.side_effect = [
        _Result(count=1),
        _Result(
            rows=[
                {
                    "id": "insight-1",
                    "category": "deal_risk",
                    "title": "Stalled deal",
                    "description": "The opportunity has not moved.",
                    "target_id": "deal-1",
                    "target_type": "opportunity",
                    "overall_confidence": 0.7,
                    "confidence_level": "medium",
                    "created_at": created_at,
                    "updated_at": created_at,
                }
            ]
        ),
        _Result(
            rows=[
                {
                    "id": "evidence-1",
                    "insight_id": "insight-1",
                    "evidence_type": "activity_signal",
                    "source_domain": "activity",
                    "source_type": "table_aggregate",
                    "source_id": "activity-1",
                    "source_name": "CRM activity",
                    "description": "No activity recorded in the current stage.",
                    "confidence": 0.6,
                    "confidence_level": "medium",
                    "evidence_kind": "crm.system_of_record",
                    "created_at": created_at,
                }
            ]
        ),
    ]

    result = await list_evidence_insights(
        page=1,
        page_size=25,
        target_type="opportunity",
        target_id="deal-1",
        category=None,
        tenant_id="tenant-1",
        db=db,
        _rbac=None,
    )

    assert result["total"] == 1
    assert result["read_only"] is True
    insight = result["items"][0]
    assert insight["target_id"] == "deal-1"
    assert insight["evidence_items"][0]["source_domain"] == "activity"
    assert insight["evidence_items"][0]["evidence_kind"] == "crm.system_of_record"
    assert "data" not in insight["evidence_items"][0]
    for call in db.execute.await_args_list[:2]:
        assert call.args[1]["tenant_id"] == "tenant-1"
    assert db.execute.await_args_list[1].args[1]["target_type"] == "opportunity"
    assert db.execute.await_args_list[1].args[1]["target_id"] == "deal-1"
    assert db.execute.await_args_list[2].args[1] == {
        "tenant_id": "tenant-1",
        "insight_ids": ["insight-1"],
    }


@pytest.mark.asyncio
async def test_evidence_read_skips_second_query_when_page_is_empty():
    db = AsyncMock()
    db.execute.side_effect = [_Result(count=0), _Result(rows=[])]

    result = await list_evidence_insights(
        page=1,
        page_size=25,
        tenant_id="tenant-1",
        db=db,
        _rbac=None,
    )

    assert result["items"] == []
    assert db.execute.await_count == 2
