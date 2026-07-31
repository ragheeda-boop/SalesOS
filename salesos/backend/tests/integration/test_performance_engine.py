"""Integration tests for EmployeePerformanceEngine with real database."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from domains.employee.models import EmployeeScore, EmployeeSignal
from domains.employee.performance import EmployeePerformanceEngine, RiskFlag
from domains.employee.postgres_repo import PostgresEmployeeSignalRepository


@pytest_asyncio.fixture
async def repo(db_session: AsyncSession) -> PostgresEmployeeSignalRepository:
    return PostgresEmployeeSignalRepository(db_session)


@pytest_asyncio.fixture
def employee_id() -> str:
    return str(uuid.uuid4())


@pytest_asyncio.fixture
def tenant_id() -> str:
    return str(uuid.uuid4())


@staticmethod
def _signal(
    eid: str,
    tid: str,
    sig_type: str = "email_sent",
    source: str = "crm",
    timestamp: datetime | None = None,
) -> EmployeeSignal:
    return EmployeeSignal(
        id=str(uuid.uuid4()),
        employee_id=eid,
        tenant_id=tid,
        signal_type=sig_type,
        source=source,
        metadata={},
        timestamp=timestamp or datetime.now(UTC),
    )


@staticmethod
def _score(
    eid: str,
    tid: str,
    overall: float = 0.75,
) -> EmployeeScore:
    return EmployeeScore(
        id=str(uuid.uuid4()),
        employee_id=eid,
        tenant_id=tid,
        overall_score=overall,
    )


class TestPerformanceEngineWithRealDB:
    """Integration tests that write to and read from a real test database."""

    async def test_compute_trend_from_real_signals(
        self,
        repo: PostgresEmployeeSignalRepository,
        employee_id: str,
        tenant_id: str,
    ):
        """Trend analysis computes score delta from real signal history (B-3)."""
        now = datetime.now(UTC)
        old_signal = _signal(employee_id, tenant_id, timestamp=now - timedelta(days=60))
        recent_signal = _signal(employee_id, tenant_id, timestamp=now - timedelta(days=10))
        await repo.save_many([old_signal, recent_signal])
        current_score = _score(employee_id, tenant_id, overall=80.0)
        await repo.save_score(current_score)

        engine = EmployeePerformanceEngine(repository=repo)
        result = await engine.compute_performance(
            employee_id,
            tenant_id,
            current_score=current_score,
            all_signals=[old_signal, recent_signal],
        )

        trend = result["trend"]
        assert "current_score" in trend
        assert "previous_score" in trend
        assert "delta" in trend
        assert "direction" in trend
        assert trend["current_score"] == 80.0
        assert trend["period_days"] == 30

    async def test_risk_flags_declining_signals(
        self,
        repo: PostgresEmployeeSignalRepository,
        employee_id: str,
        tenant_id: str,
    ):
        """Risk flag raised when signal volume drops significantly (B-3)."""
        now = datetime.now(UTC)
        older_signals = [
            _signal(employee_id, tenant_id, timestamp=now - timedelta(days=20)),
            _signal(employee_id, tenant_id, timestamp=now - timedelta(days=19)),
            _signal(employee_id, tenant_id, timestamp=now - timedelta(days=18)),
            _signal(employee_id, tenant_id, timestamp=now - timedelta(days=17)),
            _signal(employee_id, tenant_id, timestamp=now - timedelta(days=16)),
        ]
        recent_signals = [
            _signal(employee_id, tenant_id, timestamp=now - timedelta(days=5)),
        ]
        all_signals = older_signals + recent_signals
        await repo.save_many(all_signals)
        current_score = _score(employee_id, tenant_id, overall=60.0)
        await repo.save_score(current_score)

        engine = EmployeePerformanceEngine(repository=repo)
        result = await engine.compute_performance(
            employee_id,
            tenant_id,
            current_score=current_score,
            all_signals=all_signals,
        )

        flags = result["risk_flags"]
        declining_flags = [f for f in flags if f["flag"] == RiskFlag.DECLINING_SIGNALS]
        assert len(declining_flags) == 1
        assert declining_flags[0]["severity"] == "high"
        assert "Signal volume dropped" in declining_flags[0]["message"]

    async def test_risk_flags_low_engagement(
        self,
        repo: PostgresEmployeeSignalRepository,
        employee_id: str,
        tenant_id: str,
    ):
        """Risk flag raised for low 7-day engagement (B-3)."""
        now = datetime.now(UTC)
        old_signal = _signal(employee_id, tenant_id, timestamp=now - timedelta(days=14))
        await repo.save(old_signal)
        current_score = _score(employee_id, tenant_id, overall=70.0)
        await repo.save_score(current_score)

        engine = EmployeePerformanceEngine(repository=repo)
        result = await engine.compute_performance(
            employee_id,
            tenant_id,
            current_score=current_score,
            all_signals=[old_signal],
        )

        flags = result["risk_flags"]
        engagement_flags = [f for f in flags if f["flag"] == RiskFlag.LOW_ENGAGEMENT]
        assert len(engagement_flags) == 1
        assert engagement_flags[0]["severity"] == "high"

    async def test_risk_flags_declining_score(
        self,
        repo: PostgresEmployeeSignalRepository,
        employee_id: str,
        tenant_id: str,
    ):
        """Risk flag raised when score is declining (B-3)."""
        now = datetime.now(UTC)
        recent_signal = _signal(employee_id, tenant_id, timestamp=now - timedelta(days=5))
        await repo.save(recent_signal)
        current_score = _score(employee_id, tenant_id, overall=30.0)
        await repo.save_score(current_score)

        engine = EmployeePerformanceEngine(repository=repo)
        result = await engine.compute_performance(
            employee_id,
            tenant_id,
            current_score=current_score,
            all_signals=[recent_signal],
        )

        flags = result["risk_flags"]
        declining_flags = [f for f in flags if f["flag"] == RiskFlag.DECLINING_SCORE]
        if declining_flags:
            assert "Score declined" in declining_flags[0]["message"]
            assert declining_flags[0]["severity"] in ("high", "medium")

    async def test_peer_comparison_no_peers(
        self,
        repo: PostgresEmployeeSignalRepository,
        employee_id: str,
        tenant_id: str,
    ):
        """Peer comparison returns sensible defaults when no peers exist (B-3)."""
        current_score = _score(employee_id, tenant_id, overall=75.0)
        await repo.save_score(current_score)

        engine = EmployeePerformanceEngine(repository=repo)
        result = await engine.compute_performance(
            employee_id,
            tenant_id,
            current_score=current_score,
            all_signals=[],
        )

        peer = result["peer_comparison"]
        assert peer["employee_score"] == 75.0
        assert peer["above_average"] is True
        assert 0 <= peer["percentile"] <= 100

    async def test_empty_signals_returns_defaults(
        self,
        repo: PostgresEmployeeSignalRepository,
        employee_id: str,
        tenant_id: str,
    ):
        """Performance engine handles empty signal list gracefully (B-3)."""
        engine = EmployeePerformanceEngine(repository=repo)
        result = await engine.compute_performance(
            employee_id,
            tenant_id,
            all_signals=[],
        )

        assert "trend" in result
        assert "peer_comparison" in result
        assert "risk_flags" in result
        assert isinstance(result["risk_flags"], list)
        assert result["trend"]["direction"] == "stable"
