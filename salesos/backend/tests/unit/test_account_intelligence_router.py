"""Tenant-scoped CRM account context handler tests."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.modules.gtm import account_intelligence_router
from app.modules.gtm.account_intelligence_router import (
    get_account_intelligence,
    record_account_intelligence_evidence,
)


class _Mappings:
    def __init__(self, row):
        self._row = row

    def one_or_none(self):
        return self._row

    def one(self):
        return self._row


class _Result:
    def __init__(self, row):
        self._row = row

    def mappings(self):
        return _Mappings(self._row)


@pytest.mark.asyncio
async def test_account_intelligence_returns_grounded_signals_from_tenant_crm_facts():
    db = AsyncMock()
    db.execute.side_effect = [
        _Result(
            {
                "id": "co-1",
                "name_ar": "شركة",
                "name_en": "Company",
                "industry": "tech",
                "city": "Riyadh",
                "status": "active",
            }
        ),
        _Result(
            {"total_opportunities": 2, "active_opportunities": 1, "won_deals": 1, "lost_deals": 0}
        ),
        _Result(
            {
                "activity_count": 3,
                "last_activity_at": datetime.now(UTC) - timedelta(days=2),
                "recent_activity_count": 3,
                "previous_activity_count": 1,
            }
        ),
    ]

    result = await get_account_intelligence("co-1", tenant_id="tenant-1", db=db, _rbac=None)

    assert result["company_name"] == "Company"
    assert result["total_opportunities"] == 2
    assert result["active_opportunities"] == 1
    assert result["won_deals"] == 1
    assert result["activity_count"] == 3
    assert result["days_since_activity"] == 2
    assert result["missing_data"] == []
    assert result["method"] == "persisted_crm_records_with_explainable_rules"
    assert result["mutated_crm"] is False
    assert "health_score" not in result
    assert result["account_signals"]["status"] == "engaged"
    assert result["engagement_trend"]["trend"] == "improving"
    assert result["engagement_trend"]["change_percent"] == 200.0
    assert [signal["code"] for signal in result["account_signals"]["signals"]] == [
        "RECENT_ACTIVITY"
    ]
    for call in db.execute.await_args_list:
        assert call.args[1]["tenant_id"] == "tenant-1"
    assert "entity_type = 'company'" in str(db.execute.await_args_list[2].args[0])


@pytest.mark.asyncio
async def test_missing_history_is_reported_and_naive_timestamp_is_handled():
    db = AsyncMock()
    db.execute.side_effect = [
        _Result(
            {
                "id": "co-2",
                "name_ar": "شركة",
                "name_en": None,
                "industry": None,
                "city": None,
                "status": "active",
            }
        ),
        _Result(
            {"total_opportunities": 0, "active_opportunities": 0, "won_deals": 0, "lost_deals": 0}
        ),
        _Result(
            {
                "activity_count": 1,
                "last_activity_at": datetime.now(UTC).replace(tzinfo=None),
                "recent_activity_count": 1,
                "previous_activity_count": 0,
            }
        ),
    ]

    result = await get_account_intelligence("co-2", tenant_id="tenant-1", db=db, _rbac=None)

    assert result["company_name"] == "شركة"
    assert result["missing_data"] == ["opportunity_history"]
    assert result["days_since_activity"] == 0
    assert "health_score" not in result
    assert result["account_signals"]["status"] == "engaged"


@pytest.mark.asyncio
async def test_account_intelligence_hides_other_tenant_company():
    db = AsyncMock()
    db.execute.return_value = _Result(None)

    with pytest.raises(HTTPException) as error:
        await get_account_intelligence("foreign", tenant_id="tenant-2", db=db, _rbac=None)

    assert error.value.status_code == 404
    assert db.execute.await_count == 1


@pytest.mark.asyncio
async def test_open_deals_without_recent_activity_create_explainable_attention_signal():
    db = AsyncMock()
    db.execute.side_effect = [
        _Result(
            {
                "id": "co-3",
                "name_ar": None,
                "name_en": "Account",
                "industry": None,
                "city": None,
                "status": "active",
            }
        ),
        _Result(
            {"total_opportunities": 2, "active_opportunities": 1, "won_deals": 0, "lost_deals": 1}
        ),
        _Result(
            {
                "activity_count": 1,
                "last_activity_at": datetime.now(UTC) - timedelta(days=120),
                "recent_activity_count": 0,
                "previous_activity_count": 1,
            }
        ),
    ]

    result = await get_account_intelligence("co-3", tenant_id="tenant-1", db=db, _rbac=None)

    assert result["account_signals"]["status"] == "needs_attention"
    codes = {signal["code"] for signal in result["account_signals"]["signals"]}
    assert codes == {"STALE_ACTIVITY", "OPEN_DEALS_WITHOUT_RECENT_ACTIVITY", "LOSSES_OUTWEIGH_WINS"}
    assert len(result["account_signals"]["recommendations"]) == 2


@pytest.mark.asyncio
async def test_account_without_crm_history_reports_insufficient_data_instead_of_a_score():
    db = AsyncMock()
    db.execute.side_effect = [
        _Result(
            {
                "id": "co-4",
                "name_ar": None,
                "name_en": "New Account",
                "industry": None,
                "city": None,
                "status": "active",
            }
        ),
        _Result(
            {"total_opportunities": 0, "active_opportunities": 0, "won_deals": 0, "lost_deals": 0}
        ),
        _Result(
            {
                "activity_count": 0,
                "last_activity_at": None,
                "recent_activity_count": 0,
                "previous_activity_count": 0,
            }
        ),
    ]

    result = await get_account_intelligence("co-4", tenant_id="tenant-1", db=db, _rbac=None)

    assert result["account_signals"]["status"] == "insufficient_data"
    assert {signal["code"] for signal in result["account_signals"]["signals"]} == {
        "NO_OPPORTUNITY_HISTORY",
        "NO_ACTIVITY_HISTORY",
    }
    assert "health_score" not in result


@pytest.mark.asyncio
async def test_explicit_evidence_action_persists_the_tenant_account_snapshot(monkeypatch):
    db = AsyncMock()
    db.execute.side_effect = [
        _Result(
            {
                "id": "co-5",
                "name_ar": None,
                "name_en": "Evidence Co",
                "industry": "tech",
                "city": "Riyadh",
                "status": "active",
            }
        ),
        _Result(
            {"total_opportunities": 1, "active_opportunities": 1, "won_deals": 0, "lost_deals": 0}
        ),
        _Result(
            {
                "activity_count": 0,
                "last_activity_at": None,
                "recent_activity_count": 0,
                "previous_activity_count": 0,
            }
        ),
    ]
    persist = AsyncMock(return_value={"insight_id": "insight-1", "created": True})
    monkeypatch.setattr(account_intelligence_router, "persist_account_insight", persist)

    result = await record_account_intelligence_evidence(
        "co-5", tenant_id="tenant-1", db=db, _rbac=None
    )

    assert result == {"insight_id": "insight-1", "created": True}
    persist.assert_awaited_once()
    assert persist.await_args.kwargs["tenant_id"] == "tenant-1"
    assert persist.await_args.kwargs["company_id"] == "co-5"
    assert persist.await_args.kwargs["facts"]["account_signals"]["status"] == "needs_attention"


def test_activity_trend_has_no_change_percent_without_a_comparison_base():
    from intelligence.account_signals import build_engagement_trend

    result = build_engagement_trend(recent_90_days=3, previous_90_days=0)

    assert result["trend"] == "improving"
    assert result["change_percent"] is None


@pytest.mark.parametrize(
    ("recent", "previous", "expected"),
    [(11, 10, "stable"), (12, 10, "improving"), (8, 10, "declining"), (0, 0, "insufficient_data")],
)
def test_activity_trend_uses_documented_20_percent_threshold(recent, previous, expected):
    from intelligence.account_signals import build_engagement_trend

    result = build_engagement_trend(recent_90_days=recent, previous_90_days=previous)

    assert result["trend"] == expected
