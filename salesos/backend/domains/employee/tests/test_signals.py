"""Tests for Employee Signal Pipeline — B-1."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from domains.employee.models import EmployeeSignal, SignalSource, SignalType
from domains.employee.signals import SignalPipeline


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.save = AsyncMock()
    repo.save_many = AsyncMock()
    repo.get_by_employee = AsyncMock(return_value=([], 0, None))
    return repo


@pytest.fixture
def pipeline(mock_repo):
    return SignalPipeline(
        repository=mock_repo,
        activity_runtime=MagicMock(),
        timeline_recorder=MagicMock(),
        workflow_service=MagicMock(),
    )


class TestSignalPipeline:
    async def test_collect_crm_signals(self, pipeline):
        pipeline._activity_runtime.query = AsyncMock(return_value=(
            [
                {"action": "opportunity.created", "metadata": {"deal_value": 100000}, "timestamp": datetime.now(timezone.utc)},
                {"action": "contact.updated", "metadata": {}, "timestamp": datetime.now(timezone.utc)},
                {"action": "login", "metadata": {}, "timestamp": datetime.now(timezone.utc)},
            ], 3,
        ))
        signals = await pipeline._collect_crm_signals(
            str(uuid.uuid4()), str(uuid.uuid4())
        )
        assert len(signals) == 2
        assert signals[0].signal_type == SignalType.DEAL_ASSIGNED.value
        assert signals[1].signal_type == SignalType.CONTACT_MODIFIED.value

    async def test_collect_timeline_signals(self, pipeline):
        class MockEntry:
            def __init__(self, event_type, data, created_at):
                self.event_type = event_type
                self.data = data
                self.created_at = created_at

        pipeline._timeline_recorder.get_by_actor = AsyncMock(return_value=[
            MockEntry("meeting.completed", {"duration": 60}, datetime.now(timezone.utc)),
            MockEntry("call.completed", {"duration": 15}, datetime.now(timezone.utc)),
            MockEntry("email.sent", {"to": "test@example.com"}, datetime.now(timezone.utc)),
            MockEntry("note.created", {"text": "some note"}, datetime.now(timezone.utc)),
        ])
        signals = await pipeline._collect_timeline_signals(
            str(uuid.uuid4()), str(uuid.uuid4())
        )
        assert len(signals) == 3
        types = {s.signal_type for s in signals}
        assert SignalType.MEETING_COMPLETED.value in types
        assert SignalType.CALL_COMPLETED.value in types
        assert SignalType.EMAIL_SENT.value in types

    async def test_collect_workflow_signals(self, pipeline):
        class MockExecution:
            def __init__(self, status, completed_at):
                self.status = status
                self.completed_at = completed_at
                self.step_results = [{"step": "approval", "result": "approved"}]

        pipeline._workflow_service.get_executions_by_actor = AsyncMock(return_value=[
            MockExecution("completed", datetime.now(timezone.utc)),
            MockExecution("running", None),
            MockExecution("completed", datetime.now(timezone.utc)),
        ])
        signals = await pipeline._collect_workflow_signals(
            str(uuid.uuid4()), str(uuid.uuid4())
        )
        assert len(signals) == 2
        assert all(s.signal_type == SignalType.WORKFLOW_COMPLETED.value for s in signals)

    async def test_collect_for_employee(self, pipeline, mock_repo):
        pipeline._collect_crm_signals = AsyncMock(return_value=[
            EmployeeSignal(id="1", employee_id="e1", tenant_id="t1",
                          signal_type=SignalType.DEAL_ASSIGNED.value,
                          source=SignalSource.CRM.value, metadata={}),
        ])
        pipeline._collect_timeline_signals = AsyncMock(return_value=[
            EmployeeSignal(id="2", employee_id="e1", tenant_id="t1",
                          signal_type=SignalType.MEETING_COMPLETED.value,
                          source=SignalSource.TIMELINE.value, metadata={}),
        ])
        pipeline._collect_workflow_signals = AsyncMock(return_value=[
            EmployeeSignal(id="3", employee_id="e1", tenant_id="t1",
                          signal_type=SignalType.WORKFLOW_COMPLETED.value,
                          source=SignalSource.WORKFLOW.value, metadata={}),
        ])

        signals = await pipeline.collect_for_employee("e1", "t1")
        assert len(signals) == 3
        mock_repo.save_many.assert_called_once()

    async def test_ingest_signal(self, pipeline, mock_repo):
        signal = await pipeline.ingest_signal(
            employee_id="e1", tenant_id="t1",
            signal_type=SignalType.TASK_COMPLETED.value,
            source=SignalSource.WORKFLOW.value,
            metadata={"task": "onboarding"},
        )
        assert signal.employee_id == "e1"
        assert signal.signal_type == SignalType.TASK_COMPLETED.value
        assert signal.source == SignalSource.WORKFLOW.value
        mock_repo.save.assert_called_once()

    async def test_no_activity_runtime(self, pipeline):
        pipeline._activity_runtime = None
        signals = await pipeline._collect_crm_signals("e1", "t1")
        assert len(signals) == 0

    async def test_no_timeline_recorder(self, pipeline):
        pipeline._timeline_recorder = None
        signals = await pipeline._collect_timeline_signals("e1", "t1")
        assert len(signals) == 0

    async def test_no_workflow_service(self, pipeline):
        pipeline._workflow_service = None
        signals = await pipeline._collect_workflow_signals("e1", "t1")
        assert len(signals) == 0
