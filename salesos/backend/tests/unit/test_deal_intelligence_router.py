"""Pure contract tests for the read-only, tenant-scoped deal intelligence route."""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.modules.gtm.deal_intelligence_router import get_deal_intelligence


class _Mappings:
    def __init__(self, row):
        self._row = row

    def one_or_none(self):
        return self._row


class _Result:
    def __init__(self, row):
        self._row = row

    def mappings(self):
        return _Mappings(self._row)


@pytest.mark.asyncio
async def test_deal_intelligence_uses_tenant_scoped_crm_inputs_and_returns_rules():
    db = AsyncMock()
    db.execute.return_value = _Result(
        {
            "id": "opp-1",
            "name": "ERP Upgrade",
            "stage": "proposal",
            "value": 120000,
            "probability": 0.72,
            "status": "open",
            "activity_count": 6,
            "days_in_stage": 8,
        }
    )

    result = await get_deal_intelligence("opp-1", tenant_id="tenant-1", db=db, _rbac=None)

    assert result["health_score"] is not None
    assert result["health_level"] == "healthy"
    assert result["activity_count"] == 6
    assert result["missing_fields"] == []
    assert result["method"] == "deterministic_crm_rules"
    params = db.execute.await_args.args[1]
    assert params == {"opportunity_id": "opp-1", "tenant_id": "tenant-1"}


@pytest.mark.asyncio
async def test_deal_without_probability_returns_unknown_instead_of_a_guessed_score():
    db = AsyncMock()
    db.execute.return_value = _Result(
        {
            "id": "opp-2",
            "name": "Unscored deal",
            "stage": "qualification",
            "value": 50000,
            "probability": None,
            "status": "open",
            "activity_count": 0,
            "days_in_stage": None,
        }
    )

    result = await get_deal_intelligence("opp-2", tenant_id="tenant-1", db=db, _rbac=None)

    assert result["health_score"] is None
    assert result["health_level"] == "unknown"
    assert result["missing_fields"] == ["probability", "days_in_stage"]


@pytest.mark.asyncio
async def test_deal_intelligence_hides_opportunities_outside_tenant():
    db = AsyncMock()
    db.execute.return_value = _Result(None)

    with pytest.raises(HTTPException) as error:
        await get_deal_intelligence("foreign", tenant_id="tenant-2", db=db, _rbac=None)

    assert error.value.status_code == 404
    assert db.execute.await_args.args[1]["tenant_id"] == "tenant-2"
