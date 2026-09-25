from datetime import UTC, datetime, timedelta, timezone

import pytest

from domains.commercial.evidence.temporal import TemporalContractError, TemporalEnvelope


def test_temporal_envelope_normalizes_and_supports_point_in_time_queries():
    observed = datetime(2026, 9, 22, 10, tzinfo=timezone(timedelta(hours=3)))
    envelope = TemporalEnvelope(
        observed_at=observed,
        valid_from=datetime(2026, 9, 22, 7, tzinfo=UTC),
        valid_to=datetime(2026, 9, 23, tzinfo=UTC),
    )
    assert envelope.observed_at.tzinfo == UTC
    assert envelope.as_of(datetime(2026, 9, 22, 9, tzinfo=UTC)) is True
    assert envelope.as_of(datetime(2026, 9, 23, tzinfo=UTC)) is False
    assert envelope.freshness(
        now=datetime(2026, 9, 22, 12, tzinfo=UTC), stale_after=timedelta(days=1)
    ) == "FRESH"


def test_temporal_envelope_rejects_ambiguous_or_backwards_times():
    with pytest.raises(TemporalContractError, match="timezone-aware"):
        TemporalEnvelope(observed_at=datetime(2026, 9, 22))
    with pytest.raises(TemporalContractError, match="valid_to"):
        TemporalEnvelope(
            observed_at=datetime(2026, 9, 22, tzinfo=UTC),
            valid_from=datetime(2026, 9, 23, tzinfo=UTC),
            valid_to=datetime(2026, 9, 22, tzinfo=UTC),
        )
