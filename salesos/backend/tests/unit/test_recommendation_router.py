"""Read-only contract checks for deterministic seller recommendations."""

from unittest.mock import AsyncMock

import pytest

from app.modules.gtm.recommendation_router import list_recommendations


class _Mappings:
    def all(self):
        return [
            {
                "id": "opp-critical",
                "name": "Stalled deal",
                "stage": "proposal",
                "value": 300000,
                "probability": 0.15,
                "activity_count": 0,
                "days_in_stage": 46.5,
            },
            {
                "id": "opp-missing-probability",
                "name": "Unscored deal",
                "stage": "qualification",
                "value": 50000,
                "probability": None,
                "activity_count": 0,
                "days_in_stage": None,
            },
        ]


class _Result:
    def mappings(self):
        return _Mappings()


@pytest.mark.asyncio
async def test_recommendations_are_evidence_backed_read_only_and_skip_unknown_probability():
    db = AsyncMock()
    db.execute.return_value = _Result()

    result = await list_recommendations(tenant_id="tenant-1", db=db, _rbac=None, limit=20)

    assert result["total"] == 1
    assert result["source_opportunities"] == 2
    assert result["skipped_missing_probability"] == 1
    assert result["mutated_crm"] is False
    recommendation = result["items"][0]
    assert recommendation["target_id"] == "opp-critical"
    assert recommendation["priority"] == "critical"
    assert recommendation["evidence"]
    assert db.execute.await_args.args[1] == {"tenant_id": "tenant-1"}
