from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from .models import EmployeeSignal, SignalSource, SignalType
from .repository import EmployeeSignalRepository


class SignalPipeline:
    """Collects employee signals from 3+ sources:
    - CRM activity (deals assigned, contacts modified)
    - Timeline events (meetings, calls, emails)
    - Workflow completions (tasks completed, approvals)
    """

    SOURCE_MAP: dict[str, str] = {
        SignalSource.CRM.value: "crm",
        SignalSource.TIMELINE.value: "timeline",
        SignalSource.WORKFLOW.value: "workflow",
    }

    def __init__(
        self,
        repository: EmployeeSignalRepository,
        activity_runtime: Any = None,
        timeline_recorder: Any = None,
        workflow_service: Any = None,
        logger: Any = None,
    ):
        self._repository = repository
        self._activity_runtime = activity_runtime
        self._timeline_recorder = timeline_recorder
        self._workflow_service = workflow_service
        self._logger = logger

    async def collect_for_employee(
        self, employee_id: str, tenant_id: str, since: datetime | None = None
    ) -> list[EmployeeSignal]:
        signals: list[EmployeeSignal] = []

        crm_signals = await self._collect_crm_signals(employee_id, tenant_id, since)
        signals.extend(crm_signals)

        timeline_signals = await self._collect_timeline_signals(employee_id, tenant_id, since)
        signals.extend(timeline_signals)

        workflow_signals = await self._collect_workflow_signals(employee_id, tenant_id, since)
        signals.extend(workflow_signals)

        if signals:
            await self._repository.save_many(signals)

        return signals

    async def _collect_crm_signals(
        self, employee_id: str, tenant_id: str, since: datetime | None = None
    ) -> list[EmployeeSignal]:
        signals: list[EmployeeSignal] = []
        if not self._activity_runtime:
            return signals

        try:
            items, _ = await self._activity_runtime.query(
                actor=employee_id,
                tenant_id=tenant_id,
                since=since,
                limit=100,
            )
            for item in items:
                action = item.get("action", "")
                if "opportunity" in action or "deal" in action:
                    signal_type = SignalType.DEAL_ASSIGNED.value
                elif "contact" in action:
                    signal_type = SignalType.CONTACT_MODIFIED.value
                else:
                    continue

                signals.append(self._make_signal(
                    employee_id, tenant_id, signal_type,
                    SignalSource.CRM.value, item.get("metadata", {}),
                    item.get("timestamp"),
                ))
        except Exception as exc:
            if self._logger:
                self._logger.warning("crm_signal_collection_failed", error=str(exc))

        return signals

    async def _collect_timeline_signals(
        self, employee_id: str, tenant_id: str, since: datetime | None = None
    ) -> list[EmployeeSignal]:
        signals: list[EmployeeSignal] = []
        if not self._timeline_recorder:
            return signals

        try:
            entries = await self._timeline_recorder.get_by_actor(
                actor=employee_id, tenant_id=tenant_id, limit=100,
            )
            for entry in entries:
                event_type = getattr(entry, "event_type", "") if hasattr(entry, "event_type") else entry.get("event_type", "")
                ts = getattr(entry, "created_at", None) or entry.get("created_at", None)

                signal_map = {
                    "meeting": SignalType.MEETING_COMPLETED,
                    "call": SignalType.CALL_COMPLETED,
                    "email": SignalType.EMAIL_SENT,
                }
                matched = None
                for prefix, stype in signal_map.items():
                    if prefix in event_type.lower():
                        matched = stype
                        break
                if not matched:
                    continue

                signals.append(self._make_signal(
                    employee_id, tenant_id, matched.value,
                    SignalSource.TIMELINE.value,
                    getattr(entry, "data", {}) if hasattr(entry, "data") else entry.get("data", {}),
                    ts,
                ))
        except Exception as exc:
            if self._logger:
                self._logger.warning("timeline_signal_collection_failed", error=str(exc))

        return signals

    async def _collect_workflow_signals(
        self, employee_id: str, tenant_id: str, since: datetime | None = None
    ) -> list[EmployeeSignal]:
        signals: list[EmployeeSignal] = []
        if not self._workflow_service:
            return signals

        try:
            executions = await self._workflow_service.get_executions_by_actor(
                actor=employee_id, tenant_id=tenant_id, limit=100,
            )
            for exec_ in executions:
                status = getattr(exec_, "status", "") if hasattr(exec_, "status") else exec_.get("status", "")
                if status != "completed":
                    continue

                signal_type = SignalType.WORKFLOW_COMPLETED.value
                ts = getattr(exec_, "completed_at", None) or exec_.get("completed_at", None)

                signals.append(self._make_signal(
                    employee_id, tenant_id, signal_type,
                    SignalSource.WORKFLOW.value,
                    getattr(exec_, "step_results", []) if hasattr(exec_, "step_results") else exec_.get("step_results", []),
                    ts,
                ))
        except Exception as exc:
            if self._logger:
                self._logger.warning("workflow_signal_collection_failed", error=str(exc))

        return signals

    async def ingest_signal(
        self, employee_id: str, tenant_id: str,
        signal_type: str, source: str,
        metadata: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> EmployeeSignal:
        signal = self._make_signal(employee_id, tenant_id, signal_type, source, metadata or {}, timestamp)
        await self._repository.save(signal)
        return signal

    def _make_signal(
        self, employee_id: str, tenant_id: str,
        signal_type: str, source: str,
        metadata: dict[str, Any],
        timestamp: Any | None = None,
    ) -> EmployeeSignal:
        ts = timestamp
        if ts and isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                ts = datetime.now(timezone.utc)
        elif not ts:
            ts = datetime.now(timezone.utc)

        return EmployeeSignal(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            tenant_id=tenant_id,
            signal_type=signal_type,
            source=source,
            metadata=metadata,
            timestamp=ts if isinstance(ts, datetime) else datetime.now(timezone.utc),
        )
