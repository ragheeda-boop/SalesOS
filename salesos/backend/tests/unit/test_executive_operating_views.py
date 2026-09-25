from app.modules.executive.operating_views import leadership_revenue_snapshot, manager_seller_view


RECORDS = [
    {"owner_id": "a", "status": "won", "value": "100", "segment": "enterprise", "currency": "SAR"},
    {"owner_id": "a", "status": "open", "value": "50", "segment": "enterprise", "currency": "SAR"},
    {"owner_id": "b", "status": "won", "value": "20", "segment": "mid", "currency": "USD"},
]


def test_manager_view_rolls_up_seller_value_without_float_rounding():
    result = manager_seller_view(RECORDS)
    assert result == [
        {"owner_id": "a", "opportunities": 2, "open_value": "50", "won_value": "100"},
        {"owner_id": "b", "opportunities": 1, "open_value": "0", "won_value": "20"},
    ]


def test_leadership_snapshot_keeps_currency_buckets_separate():
    result = leadership_revenue_snapshot(RECORDS)
    assert result["by_segment"] == {"enterprise": "100", "mid": "20"}
    assert result["by_currency"] == {"SAR": "100", "USD": "20"}
    assert result["mixed_currency"] is True
