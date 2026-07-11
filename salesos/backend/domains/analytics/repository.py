"""In-memory repository for Analytics domain — perfect for tests and prototyping."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from domains.analytics.models import ReportDefinition, ReportExecution, ReportStatus


class InMemoryReportRepository:
    """Thread-safe in-memory store for reports and executions."""

    def __init__(self) -> None:
        self._reports: dict[str, ReportDefinition] = {}
        self._executions: dict[str, ReportExecution] = {}

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

    async def list_reports(self, tenant_id: str | None = None) -> list[ReportDefinition]:
        reports = list(self._reports.values())
        if tenant_id:
            reports = [r for r in reports if r.tenant_id == tenant_id]
        return sorted(reports, key=lambda r: r.created_at, reverse=True)

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
        self, report_id: str | None = None
    ) -> list[ReportExecution]:
        executions = list(self._executions.values())
        if report_id:
            executions = [e for e in executions if e.report_id == report_id]
        return sorted(executions, key=lambda e: e.started_at or datetime.min, reverse=True)

    async def update_execution(self, execution: ReportExecution) -> ReportExecution:
        self._executions[execution.id] = execution
        return execution
