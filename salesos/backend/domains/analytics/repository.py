"""In-memory repository for Analytics domain — perfect for tests and prototyping."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from domains.analytics.models import (
    PermissionLevel,
    ReportDefinition,
    ReportExecution,
    ReportShare,
    ReportStatus,
    ScheduledReport,
)


class InMemoryReportRepository:
    """Thread-safe in-memory store for reports, executions, shares, and schedules."""

    def __init__(self) -> None:
        self._reports: dict[str, ReportDefinition] = {}
        self._executions: dict[str, ReportExecution] = {}
        self._shares: dict[str, ReportShare] = {}
        self._schedules: dict[str, ScheduledReport] = {}

    # ── Reports ──────────────────────────────────────────────────────────────

    async def create_report(self, report: ReportDefinition) -> ReportDefinition:
        if not report.id:
            report.id = str(uuid.uuid4())
        report.created_at = datetime.now(timezone.utc)
        report.updated_at = report.created_at
        self._reports[report.id] = report
        return report

    async def get_report(self, report_id: str) -> ReportDefinition | None:
        return self._reports.get(report_id)

    async def list_reports(
        self,
        tenant_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
        cursor: str | None = None,
    ) -> tuple[list[ReportDefinition], str | None]:
        reports = list(self._reports.values())
        if tenant_id:
            reports = [r for r in reports if r.tenant_id == tenant_id]
        reports = sorted(reports, key=lambda r: r.created_at, reverse=True)
        if cursor:
            cursor_idx = next(
                (i for i, r in enumerate(reports) if r.id == cursor), len(reports)
            )
            reports = reports[cursor_idx:]
        page = reports[offset : offset + limit]
        next_cursor = page[-1].id if len(page) == limit and reports else None
        return page, next_cursor

    async def update_report(self, report: ReportDefinition) -> ReportDefinition:
        report.updated_at = datetime.now(timezone.utc)
        self._reports[report.id] = report
        return report

    async def delete_report(self, report_id: str) -> bool:
        return self._reports.pop(report_id, None) is not None

    # ── Executions ───────────────────────────────────────────────────────────

    async def create_execution(self, execution: ReportExecution) -> ReportExecution:
        if not execution.id:
            execution.id = str(uuid.uuid4())
        self._executions[execution.id] = execution
        return execution

    async def get_execution(self, execution_id: str) -> ReportExecution | None:
        return self._executions.get(execution_id)

    async def list_executions(
        self,
        report_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ReportExecution], str | None]:
        executions = list(self._executions.values())
        if report_id:
            executions = [e for e in executions if e.report_id == report_id]
        executions = sorted(
            executions, key=lambda e: e.started_at or datetime.min, reverse=True
        )
        page = executions[offset : offset + limit]
        next_cursor = page[-1].id if len(page) == limit and executions else None
        return page, next_cursor

    async def update_execution(self, execution: ReportExecution) -> ReportExecution:
        self._executions[execution.id] = execution
        return execution

    # ── Report Sharing ───────────────────────────────────────────────────────

    async def create_share(self, share: ReportShare) -> ReportShare:
        share.id = share.id or str(uuid.uuid4())
        share.created_at = datetime.now(timezone.utc)
        self._shares[share.id] = share
        return share

    async def get_share(self, share_id: str) -> ReportShare | None:
        return self._shares.get(share_id)

    async def list_shares(self, report_id: str) -> list[ReportShare]:
        return [s for s in self._shares.values() if s.report_id == report_id]

    async def get_user_permission(
        self, report_id: str, user_id: str
    ) -> PermissionLevel | None:
        for s in self._shares.values():
            if s.report_id == report_id and s.user_id == user_id:
                return s.permission
        return None

    async def delete_share(self, share_id: str) -> bool:
        return self._shares.pop(share_id, None) is not None

    async def update_share(self, share: ReportShare) -> ReportShare:
        self._shares[share.id] = share
        return share

    # ── Scheduled Reports ────────────────────────────────────────────────────

    async def create_schedule(self, schedule: ScheduledReport) -> ScheduledReport:
        schedule.id = schedule.id or str(uuid.uuid4())
        schedule.created_at = datetime.now(timezone.utc)
        schedule.updated_at = schedule.created_at
        self._schedules[schedule.id] = schedule
        return schedule

    async def get_schedule(self, schedule_id: str) -> ScheduledReport | None:
        return self._schedules.get(schedule_id)

    async def list_schedules(
        self, tenant_id: str | None = None
    ) -> list[ScheduledReport]:
        schedules = list(self._schedules.values())
        if tenant_id:
            schedules = [s for s in schedules if s.tenant_id == tenant_id]
        return sorted(schedules, key=lambda s: s.created_at, reverse=True)

    async def get_due_schedules(
        self, before: datetime | None = None
    ) -> list[ScheduledReport]:
        before = before or datetime.now(timezone.utc)
        return [
            s
            for s in self._schedules.values()
            if s.enabled and s.next_run and s.next_run <= before
        ]

    async def update_schedule(self, schedule: ScheduledReport) -> ScheduledReport:
        schedule.updated_at = datetime.now(timezone.utc)
        self._schedules[schedule.id] = schedule
        return schedule

    async def delete_schedule(self, schedule_id: str) -> bool:
        return self._schedules.pop(schedule_id, None) is not None
