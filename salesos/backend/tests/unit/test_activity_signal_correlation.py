from datetime import UTC, datetime, timedelta

from app.modules.activity.signal_correlation import correlate_activity_signals


def test_activity_signal_correlation_is_company_and_time_bounded():
    now = datetime(2026, 9, 22, tzinfo=UTC)
    result = correlate_activity_signals(
        [{"id": "a1", "company_id": "c1", "occurred_at": now}],
        [
            {"id": "s1", "company_id": "c1", "observed_at": now + timedelta(days=2)},
            {"id": "s2", "company_id": "c2", "observed_at": now},
            {"id": "s3", "company_id": "c1", "observed_at": now + timedelta(days=15)},
        ],
    )
    assert [(item.activity_id, item.signal_id, item.confidence) for item in result] == [("a1", "s1", 0.7)]
