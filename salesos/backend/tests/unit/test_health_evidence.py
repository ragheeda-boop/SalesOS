from datetime import UTC, datetime, timedelta

from app.modules.admin.health_evidence import build_health_evidence


def test_health_evidence_clamps_score_and_marks_staleness():
    now = datetime(2026, 9, 22, tzinfo=UTC)
    fresh = build_health_evidence(
        score=1.5, status="healthy", calculated_at=now, source_metrics={"users": 3}, now=now
    )
    stale = build_health_evidence(
        score=-1, status="critical", calculated_at=now - timedelta(days=2), source_metrics={}, now=now
    )
    assert fresh.score == 1.0 and fresh.freshness == "FRESH"
    assert stale.score == 0.0 and stale.freshness == "STALE"
