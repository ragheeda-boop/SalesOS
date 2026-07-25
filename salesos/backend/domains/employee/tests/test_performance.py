"""Tests for Employee Performance Insights — B-3."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domains.employee.models import EmployeeSignal, EmployeeScore, SignalSource, SignalType
from domains.employee.performance import EmployeePerformanceEngine, RiskFlag


def _signal(
    employee_id: str,
    tenant_id: str,
    signal_type: str,
    source: str,
    timestamp: datetime | None = None,
) -> EmployeeSignal:
    return EmployeeSignal(
        id=str(uuid.uuid4()),
        employee_id=employee_id,
        tenant_id=tenant_id,
        signal_type=signal_type,
        source=source,
        metadata={},
        timestamp=timestamp or datetime.now(timezone.utc),
    )


def _score(
    employee_id: str,
    tenant_id: str,
    overall: float = 0.7,
) -> EmployeeScore:
    return EmployeeScore(
        id=str(uuid.uuid4()),
        employee_id=employee_id,
        tenant_id=tenant_id,
        overall_score=overall,
        signal_volume_score=0.7,
        recency_score=0.8,
        diversity_score=0.6,
        completion_rate=0.8,
        confidence_interval_low=0.6,
        confidence_interval_high=0.8,
        signal_count=20,
    )


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.save = AsyncMock()
    repo.save_many = AsyncMock()
    repo.save_score = AsyncMock()
    repo.get_by_employee = AsyncMock(return_value=([], 0, None))
    repo.get_latest_score = AsyncMock(return_value=None)
    repo.db = MagicMock()
    return repo


@pytest.fixture
def engine(mock_repo):
    return EmployeePerformanceEngine(repository=mock_repo)


class TestPerformanceEngine:
    async def test_compute_performance_empty(self, engine, mock_repo):
        with patch.object(engine, '_get_peer_scores', new_callable=AsyncMock, return_value=[]):
            result = await engine.compute_performance("e1", "t1")
        assert "trend" in result
        assert "peer_comparison" in result
        assert "risk_flags" in result

    async def test_trend_with_score(self, engine, mock_repo):
        score = _score("e1", "t1", overall=0.7)
        mock_repo.get_latest_score = AsyncMock(return_value=score)
        mock_repo.get_by_employee = AsyncMock(return_value=([], 0, None))

        with patch.object(engine, '_get_peer_scores', new_callable=AsyncMock, return_value=[]):
            result = await engine.compute_performance("e1", "t1", current_score=score)
        trend = result["trend"]
        assert trend["current_score"] == 0.7
        assert trend["period_days"] == 30
        assert trend["direction"] in ("stable", "improving", "declining")

    async def test_trend_improving(self, engine, mock_repo):
        now = datetime.now(timezone.utc)
        old_signals = [
            _signal("e1", "t1", SignalType.EMAIL_SENT.value, SignalSource.TIMELINE.value,
                    now - timedelta(days=60)),
        ]
        mock_repo.get_by_employee = AsyncMock(return_value=(old_signals, 1, None))
        mock_repo.get_latest_score = AsyncMock(return_value=_score("e1", "t1", 0.5))

        with patch.object(engine._repository, 'get_by_employee', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (old_signals, 1, None)
            with patch('domains.employee.scoring.EmployeeScoringEngine') as MockScorer:
                MockScorer.return_value.compute_score = AsyncMock(
                    return_value=_score("e1", "t1", 0.5)
                )
                trend = await engine._compute_trend("e1", "t1", _score("e1", "t1", 0.8))

        assert trend["current_score"] == 0.8
        assert trend["previous_score"] == 0.5
        assert trend["direction"] == "improving"

    async def test_trend_stable(self, engine, mock_repo):
        now = datetime.now(timezone.utc)
        old_signals = [
            _signal("e1", "t1", SignalType.EMAIL_SENT.value, SignalSource.TIMELINE.value,
                    now - timedelta(days=35)),
            _signal("e1", "t1", SignalType.CALL_COMPLETED.value, SignalSource.TIMELINE.value,
                    now - timedelta(days=40)),
        ]
        mock_repo.get_by_employee = AsyncMock(return_value=(old_signals, 2, None))
        score = _score("e1", "t1", overall=0.7)

        with patch('domains.employee.scoring.EmployeeScoringEngine') as MockScorer:
            MockScorer.return_value.compute_score = AsyncMock(return_value=_score("e1", "t1", 0.7))
            trend = await engine._compute_trend("e1", "t1", score)
        assert trend["direction"] == "stable"
        assert abs(trend["delta"]) < 0.03

    async def test_trend_no_score(self, engine, mock_repo):
        trend = await engine._compute_trend("e1", "t1", None)
        assert trend["current_score"] == 0.0
        assert trend["direction"] == "stable"

    async def test_peer_comparison_with_score(self, engine, mock_repo):
        score = _score("e1", "t1", overall=0.8)
        with patch.object(engine, '_get_peer_scores', new_callable=AsyncMock) as mock_peers:
            mock_peers.return_value = [0.5, 0.6, 0.7, 0.9]
            peer = await engine._compute_peer_comparison("e1", "t1", score)

        assert peer["employee_score"] == 0.8
        assert peer["department_average"] == pytest.approx(0.675, abs=0.01)
        assert peer["percentile"] == 75
        assert peer["above_average"] is True

    async def test_peer_comparison_below_average(self, engine, mock_repo):
        score = _score("e1", "t1", overall=0.3)
        with patch.object(engine, '_get_peer_scores', new_callable=AsyncMock) as mock_peers:
            mock_peers.return_value = [0.5, 0.6, 0.7, 0.9]
            peer = await engine._compute_peer_comparison("e1", "t1", score)

        assert peer["employee_score"] == 0.3
        assert peer["above_average"] is False

    async def test_peer_comparison_no_peers(self, engine, mock_repo):
        score = _score("e1", "t1", overall=0.7)
        with patch.object(engine, '_get_peer_scores', new_callable=AsyncMock) as mock_peers:
            mock_peers.return_value = []
            peer = await engine._compute_peer_comparison("e1", "t1", score)

        assert peer["percentile"] == 50
        assert peer["above_average"] is True

    async def test_peer_comparison_no_score(self, engine, mock_repo):
        peer = await engine._compute_peer_comparison("e1", "t1", None)
        assert peer["employee_score"] == 0.0
        assert peer["percentile"] == 0

    async def test_risk_flags_declining_signals(self, engine):
        now = datetime.now(timezone.utc)
        signals = [
            _signal("e1", "t1", SignalType.EMAIL_SENT.value, SignalSource.TIMELINE.value,
                    now - timedelta(days=5)),
            _signal("e1", "t1", SignalType.CALL_COMPLETED.value, SignalSource.TIMELINE.value,
                    now - timedelta(days=20)),
            _signal("e1", "t1", SignalType.EMAIL_SENT.value, SignalSource.TIMELINE.value,
                    now - timedelta(days=21)),
            _signal("e1", "t1", SignalType.CALL_COMPLETED.value, SignalSource.TIMELINE.value,
                    now - timedelta(days=22)),
            _signal("e1", "t1", SignalType.EMAIL_SENT.value, SignalSource.TIMELINE.value,
                    now - timedelta(days=23)),
        ]
        score = _score("e1", "t1", 0.7)
        trend = {"direction": "stable", "delta": 0.0}
        flags = engine._compute_risk_flags(signals, score, trend)
        flag_types = [f["flag"] for f in flags]
        assert RiskFlag.DECLINING_SIGNALS in flag_types

    async def test_risk_flags_low_engagement(self, engine):
        now = datetime.now(timezone.utc)
        signals = [
            _signal("e1", "t1", SignalType.EMAIL_SENT.value, SignalSource.TIMELINE.value,
                    now - timedelta(days=3)),
        ]
        flags = engine._compute_risk_flags(signals, _score("e1", "t1"), {"direction": "stable"})
        flag_types = [f["flag"] for f in flags]
        assert RiskFlag.LOW_ENGAGEMENT in flag_types

    async def test_risk_flags_declining_score(self, engine):
        signals = [
            _signal("e1", "t1", SignalType.EMAIL_SENT.value, SignalSource.TIMELINE.value,
                    datetime.now(timezone.utc) - timedelta(days=2)),
        ]
        trend = {"direction": "declining", "delta": -0.15}
        flags = engine._compute_risk_flags(signals, _score("e1", "t1"), trend)
        flag_types = [f["flag"] for f in flags]
        assert RiskFlag.DECLINING_SCORE in flag_types

    async def test_risk_flags_no_signals(self, engine):
        flags = engine._compute_risk_flags([], None, {"direction": "stable"})
        assert len(flags) == 0 or all(
            f["flag"] == RiskFlag.LOW_ENGAGEMENT for f in flags
        )

    async def test_risk_flags_many_signals_no_flags(self, engine):
        now = datetime.now(timezone.utc)
        signals = [
            _signal("e1", "t1", SignalType.EMAIL_SENT.value, SignalSource.TIMELINE.value,
                    now - timedelta(days=i % 7))
            for i in range(20)
        ]
        flags = engine._compute_risk_flags(signals, _score("e1", "t1"), {"direction": "stable"})
        high_flags = [f for f in flags if f["severity"] == "high"]
        assert len(high_flags) == 0

    async def test_risk_flag_severity_medium_low_engagement(self, engine):
        now = datetime.now(timezone.utc)
        signals = [
            _signal("e1", "t1", SignalType.EMAIL_SENT.value, SignalSource.TIMELINE.value,
                    now - timedelta(days=2)),
        ]
        flags = engine._compute_risk_flags(signals, _score("e1", "t1"), {"direction": "stable"})
        le_flag = next((f for f in flags if f["flag"] == RiskFlag.LOW_ENGAGEMENT), None)
        assert le_flag is not None
        assert le_flag["severity"] == "medium"

    async def test_risk_flag_severity_high_zero_engagement(self, engine):
        flags = engine._compute_risk_flags([], None, {"direction": "stable"})
        le_flag = next((f for f in flags if f["flag"] == RiskFlag.LOW_ENGAGEMENT), None)
        if le_flag:
            assert le_flag["severity"] == "high"

    async def test_peer_comparison_percentile_100(self, engine, mock_repo):
        score = _score("e1", "t1", overall=1.0)
        with patch.object(engine, '_get_peer_scores', new_callable=AsyncMock) as mock_peers:
            mock_peers.return_value = [0.2, 0.3, 0.4]
            peer = await engine._compute_peer_comparison("e1", "t1", score)
        assert peer["percentile"] == 100
        assert peer["above_average"] is True

    async def test_peer_comparison_percentile_0(self, engine, mock_repo):
        score = _score("e1", "t1", overall=0.1)
        with patch.object(engine, '_get_peer_scores', new_callable=AsyncMock) as mock_peers:
            mock_peers.return_value = [0.5, 0.6, 0.7]
            peer = await engine._compute_peer_comparison("e1", "t1", score)
        assert peer["percentile"] == 0
        assert peer["above_average"] is False
