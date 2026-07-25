"""Tests for PostgresEmployeeSignalRepository — query, save, pagination."""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from sqlalchemy import select, text, func

from domains.employee.postgres_repo import PostgresEmployeeSignalRepository
from domains.employee.models import EmployeeSignal
from domains.employee.db_models import EmployeeSignalModel


class TestSaveAndGet:
    @pytest.mark.asyncio
    async def test_save_signal(self, db_session):
        repo = PostgresEmployeeSignalRepository(db_session)
        signal = EmployeeSignal(
            id=str(uuid4()),
            employee_id=str(uuid4()),
            tenant_id=str(uuid4()),
            signal_type="email_sent",
            source="crm",
            metadata={"key": "val"},
            timestamp=datetime.now(timezone.utc),
        )
        saved = await repo.save(signal)
        assert saved.id == signal.id
        assert saved.signal_type == "email_sent"

    @pytest.mark.asyncio
    async def test_get_by_employee_returns_empty_list(self, db_session):
        repo = PostgresEmployeeSignalRepository(db_session)
        items, total, cursor = await repo.get_by_employee(
            str(uuid4()), str(uuid4()), limit=10
        )
        assert items == []
        assert total == 0
        assert cursor is None

    @pytest.mark.asyncio
    async def test_get_by_employee_filters_by_source(self, db_session):
        repo = PostgresEmployeeSignalRepository(db_session)
        eid = str(uuid4())
        tid = str(uuid4())
        signal = EmployeeSignal(
            id=str(uuid4()), employee_id=eid, tenant_id=tid,
            signal_type="meeting_completed", source="timeline",
            metadata={}, timestamp=datetime.now(timezone.utc),
        )
        await repo.save(signal)
        items, total, _ = await repo.get_by_employee(eid, tid, source="timeline", limit=10)
        assert total >= 1
        assert all(s.source == "timeline" for s in items)


class TestGetSummary:
    @pytest.mark.asyncio
    async def test_empty_summary(self, db_session):
        repo = PostgresEmployeeSignalRepository(db_session)
        summary = await repo.get_summary(str(uuid4()), str(uuid4()))
        assert summary["total_signals"] == 0
        assert summary["by_source"] == {}
        assert summary["by_type"] == {}
        assert summary["recent_signals"] == []

    @pytest.mark.asyncio
    async def test_summary_aggregates_counts(self, db_session):
        repo = PostgresEmployeeSignalRepository(db_session)
        eid = str(uuid4())
        tid = str(uuid4())
        signals = [
            EmployeeSignal(id=str(uuid4()), employee_id=eid, tenant_id=tid,
                          signal_type=t, source=s, metadata={},
                          timestamp=datetime.now(timezone.utc))
            for t, s in [("email_sent", "crm"), ("email_sent", "crm"),
                         ("call_completed", "timeline")]
        ]
        await repo.save_many(signals)
        summary = await repo.get_summary(eid, tid)
        assert summary["total_signals"] == 3
        assert summary["by_source"]["crm"] == 2
        assert summary["by_source"]["timeline"] == 1
        assert summary["by_type"]["email_sent"] == 2


class TestSaveScore:
    @pytest.mark.asyncio
    async def test_save_and_get_latest_score(self, db_session):
        from domains.employee.models import EmployeeScore
        repo = PostgresEmployeeSignalRepository(db_session)
        eid = str(uuid4())
        tid = str(uuid4())
        score = EmployeeScore(
            id=str(uuid4()), employee_id=eid, tenant_id=tid,
            overall_score=0.75, signal_volume_score=0.8,
            recency_score=0.7, diversity_score=0.6,
            completion_rate=0.9, confidence_interval_low=0.65,
            confidence_interval_high=0.85, signal_count=50,
        )
        await repo.save_score(score)
        latest = await repo.get_latest_score(eid, tid)
        assert latest is not None
        assert latest.overall_score == 0.75
        assert latest.signal_count == 50

    @pytest.mark.asyncio
    async def test_get_latest_score_none_for_unknown_employee(self, db_session):
        repo = PostgresEmployeeSignalRepository(db_session)
        result = await repo.get_latest_score(str(uuid4()), str(uuid4()))
        assert result is None


class TestDeleteByEmployee:
    @pytest.mark.asyncio
    async def test_delete_removes_signals(self, db_session):
        repo = PostgresEmployeeSignalRepository(db_session)
        eid = str(uuid4())
        tid = str(uuid4())
        signal = EmployeeSignal(
            id=str(uuid4()), employee_id=eid, tenant_id=tid,
            signal_type="task_completed", source="workflow",
            metadata={}, timestamp=datetime.now(timezone.utc),
        )
        await repo.save(signal)
        deleted = await repo.delete_by_employee(eid, tid)
        assert deleted >= 1
        items, total, _ = await repo.get_by_employee(eid, tid)
        assert total == 0


class TestPagination:
    @pytest.mark.asyncio
    async def test_cursor_pagination_returns_next_cursor(self, db_session):
        repo = PostgresEmployeeSignalRepository(db_session)
        eid = str(uuid4())
        tid = str(uuid4())
        for i in range(15):
            signal = EmployeeSignal(
                id=str(uuid4()), employee_id=eid, tenant_id=tid,
                signal_type="email_sent", source="crm", metadata={},
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=i),
            )
            await repo.save(signal)
        items, total, cursor = await repo.get_by_employee(eid, tid, limit=10)
        assert len(items) == 10
        assert cursor is not None
        items2, total2, cursor2 = await repo.get_by_employee(eid, tid, limit=10, cursor=cursor)
        assert len(items2) >= 1


class TestDatabaseIntegrity:
    @pytest.mark.asyncio
    async def test_signal_has_all_required_fields(self, db_session):
        repo = PostgresEmployeeSignalRepository(db_session)
        signal = EmployeeSignal(
            id=str(uuid4()), employee_id=str(uuid4()), tenant_id=str(uuid4()),
            signal_type="deal_assigned", source="crm",
            metadata={"deal_id": "123"}, timestamp=datetime.now(timezone.utc),
        )
        await repo.save(signal)
        row = (await db_session.execute(
            select(EmployeeSignalModel).where(EmployeeSignalModel.id == signal.id)
        )).scalar_one_or_none()
        assert row is not None
        assert row.signal_type == "deal_assigned"
        assert row.source == "crm"
        assert row.metadata == {"deal_id": "123"}
