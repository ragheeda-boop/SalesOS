"""Tests for Employee Scoring Engine — B-2."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from domains.employee.models import EmployeeSignal, EmployeeScore, SignalSource, SignalType
from domains.employee.scoring import EmployeeScoringEngine


def _signal(employee_id: str, tenant_id: str, signal_type: str, source: str,
            timestamp: datetime | None = None) -> EmployeeSignal:
    return EmployeeSignal(
        id=str(uuid.uuid4()),
        employee_id=employee_id,
        tenant_id=tenant_id,
        signal_type=signal_type,
        source=source,
        metadata={},
        timestamp=timestamp or datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.save_score = AsyncMock()
    repo.get_by_employee = AsyncMock()
    return repo


@pytest.fixture
def scorer(mock_repo):
    return EmployeeScoringEngine(repository=mock_repo)


class TestEmployeeScoringEngine:
    async def test_compute_score_with_signals(self, scorer, mock_repo):
        signals = [
            _signal("e1", "t1", SignalType.DEAL_ASSIGNED.value, SignalSource.CRM.value,
                    datetime.now(timezone.utc) - timedelta(hours=1)),
            _signal("e1", "t1", SignalType.MEETING_COMPLETED.value, SignalSource.TIMELINE.value,
                    datetime.now(timezone.utc) - timedelta(hours=2)),
            _signal("e1", "t1", SignalType.EMAIL_SENT.value, SignalSource.TIMELINE.value,
                    datetime.now(timezone.utc) - timedelta(hours=3)),
            _signal("e1", "t1", SignalType.TASK_COMPLETED.value, SignalSource.WORKFLOW.value,
                    datetime.now(timezone.utc) - timedelta(hours=4)),
            _signal("e1", "t1", SignalType.WORKFLOW_COMPLETED.value, SignalSource.WORKFLOW.value,
                    datetime.now(timezone.utc) - timedelta(hours=5)),
        ]
        score = await scorer.compute_score("e1", "t1", signals)
        assert score.employee_id == "e1"
        assert score.overall_score > 0
        assert score.signal_count == 5
        assert score.confidence_interval_low < score.overall_score < score.confidence_interval_high
        mock_repo.save_score.assert_called_once()

    async def test_compute_score_empty(self, scorer, mock_repo):
        score = await scorer.compute_score("e1", "t1", [])
        assert score.overall_score == 0.0
        assert score.signal_count == 0

    async def test_signal_volume(self, scorer):
        many_signals = [_signal("e1", "t1", SignalType.EMAIL_SENT.value, SignalSource.TIMELINE.value)
                        for _ in range(80)]
        volume = scorer._compute_signal_volume(many_signals)
        assert volume == pytest.approx(0.8, abs=0.01)

        volume_empty = scorer._compute_signal_volume([])
        assert volume_empty == 0.0

    async def test_recency_recent(self, scorer):
        signals = [
            _signal("e1", "t1", SignalType.EMAIL_SENT.value, SignalSource.TIMELINE.value,
                    datetime.now(timezone.utc) - timedelta(hours=1)),
        ]
        recency = scorer._compute_recency(signals)
        assert recency > 0.95

    async def test_recency_old(self, scorer):
        signals = [
            _signal("e1", "t1", SignalType.EMAIL_SENT.value, SignalSource.TIMELINE.value,
                    datetime.now(timezone.utc) - timedelta(days=60)),
        ]
        recency = scorer._compute_recency(signals)
        assert recency < 0.5

    async def test_recency_empty(self, scorer):
        assert scorer._compute_recency([]) == 0.0

    async def test_diversity(self, scorer):
        signals = [
            _signal("e1", "t1", SignalType.DEAL_ASSIGNED.value, SignalSource.CRM.value),
            _signal("e1", "t1", SignalType.MEETING_COMPLETED.value, SignalSource.TIMELINE.value),
            _signal("e1", "t1", SignalType.EMAIL_SENT.value, SignalSource.TIMELINE.value),
            _signal("e1", "t1", SignalType.WORKFLOW_COMPLETED.value, SignalSource.WORKFLOW.value),
        ]
        diversity = scorer._compute_diversity(signals)
        assert 0 < diversity <= 1.0

    async def test_diversity_empty(self, scorer):
        assert scorer._compute_diversity([]) == 0.0

    async def test_completion_rate(self, scorer):
        signals = [
            _signal("e1", "t1", SignalType.TASK_COMPLETED.value, SignalSource.WORKFLOW.value),
            _signal("e1", "t1", SignalType.WORKFLOW_COMPLETED.value, SignalSource.WORKFLOW.value),
            _signal("e1", "t1", SignalType.DEAL_ASSIGNED.value, SignalSource.CRM.value),
        ]
        rate = scorer._compute_completion_rate(signals)
        assert rate == 1.0

    async def test_completion_rate_no_workflow(self, scorer):
        signals = [
            _signal("e1", "t1", SignalType.TASK_COMPLETED.value, SignalSource.CRM.value),
        ]
        rate = scorer._compute_completion_rate(signals)
        assert rate == 0.5

    async def test_confidence_interval(self, scorer):
        low, high = scorer._compute_confidence_interval(0.7, 3)
        assert low == pytest.approx(0.45, abs=0.01)
        assert high == 0.95

        low, high = scorer._compute_confidence_interval(0.7, 60)
        assert low == pytest.approx(0.65, abs=0.01)
        assert high == 0.75

    async def test_decision_context_factors(self, scorer):
        score = EmployeeScore(
            id="s1", employee_id="e1", tenant_id="t1",
            overall_score=0.75, signal_volume_score=0.8,
            recency_score=0.9, diversity_score=0.6,
            completion_rate=0.85, signal_count=20,
        )
        factors = await scorer.get_decision_context_factors(score)
        assert len(factors) == 4
        assert factors[0]["key"] == "employee_overall_score"
        assert factors[0]["value"] == 0.75
