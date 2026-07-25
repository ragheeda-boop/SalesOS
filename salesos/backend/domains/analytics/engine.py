"""Report engine — generate, schedule, export, and unified analytics."""

from __future__ import annotations

import csv
import io
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from domains.analytics.cubes import ActivityCube, ForecastCube, PipelineCube, TeamCube
from domains.analytics.models import (
    CubeType,
    DomainMetrics,
    Granularity,
    OutputFormat,
    ReportDefinition,
    ReportExecution,
    ReportStatus,
    ReportShare,
    ScheduledReport,
    ScheduleCadence,
    PermissionLevel,
)
from domains.analytics.repository import InMemoryReportRepository

logger = logging.getLogger(__name__)

CUBE_REGISTRY: dict[CubeType, Any] = {
    CubeType.PIPELINE: PipelineCube(),
    CubeType.FORECAST: ForecastCube(),
    CubeType.TEAM: TeamCube(),
    CubeType.ACTIVITY: ActivityCube(),
}


def _compute_next_run(cadence: ScheduleCadence, from_time: datetime | None = None) -> datetime:
    """Compute next run time based on cadence."""
    now = from_time or datetime.now(timezone.utc)
    if cadence == ScheduleCadence.DAILY:
        return now + timedelta(days=1)
    if cadence == ScheduleCadence.WEEKLY:
        return now + timedelta(weeks=1)
    if cadence == ScheduleCadence.QUARTERLY:
        return now + timedelta(days=90)
    return now + timedelta(days=30)


class ReportEngine:
    """Central report engine that orchestrates cube queries, export, sharing, and scheduling."""

    def __init__(self, repository: InMemoryReportRepository | None = None) -> None:
        self.repository = repository or InMemoryReportRepository()

    # ── Unified Analytics (B-1) ─────────────────────────────────────────────

    async def get_unified_analytics(
        self,
        tenant_id: str,
        domain: str | None = None,
    ) -> DomainMetrics:
        """Aggregate metrics from all domain cubes into a unified view."""
        pipelines = await CUBE_REGISTRY[CubeType.PIPELINE].query(
            db=None, tenant_id=tenant_id
        )
        forecasts = await CUBE_REGISTRY[CubeType.FORECAST].query(
            db=None, tenant_id=tenant_id
        )
        teams = await CUBE_REGISTRY[CubeType.TEAM].query(
            db=None, tenant_id=tenant_id
        )
        activities = await CUBE_REGISTRY[CubeType.ACTIVITY].query(
            db=None, tenant_id=tenant_id
        )

        total_deals = sum(r.get("count", 0) for r in pipelines)
        pipeline_value = sum(r.get("value", 0) for r in pipelines)
        total_revenue = sum(r.get("committed", 0) for r in forecasts)
        deals_won = sum(r.get("deals_won", 0) for r in teams)
        deals_lost = sum(r.get("deals_lost", 0) for r in teams)
        total_created = sum(r.get("deals_created", 0) for r in teams)
        total_employees = len({r.get("owner") for r in teams})
        active_automations = len(
            {r.get("type") for r in activities if r.get("count", 0) > 0}
        )
        conversion_rate = (deals_won / total_created * 100) if total_created else 0.0
        win_rate = (deals_won / (deals_won + deals_lost) * 100) if (deals_won + deals_lost) else 0.0
        avg_deal_size = (pipeline_value / total_deals) if total_deals else 0.0

        return DomainMetrics(
            total_deals=total_deals,
            total_revenue=total_revenue,
            total_employees=total_employees,
            total_workflows=0,
            conversion_rate=round(conversion_rate, 2),
            pipeline_value=pipeline_value,
            avg_deal_size=round(avg_deal_size, 2),
            win_rate=round(win_rate, 2),
            active_automations=active_automations,
        )

    # ── Report Execution ─────────────────────────────────────────────────────

    async def generate(
        self,
        report_id: str,
        tenant_id: str,
    ) -> ReportExecution:
        report = await self.repository.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        cube_type = report.type
        cube = CUBE_REGISTRY.get(cube_type)
        if not cube:
            raise ValueError(f"No cube registered for type {cube_type}")

        config = report.config or {}
        filters = config.get("filters", {})
        granularity_str = config.get("granularity", cube.granularity.value)
        granularity = Granularity(granularity_str)

        execution = ReportExecution(
            id=str(uuid.uuid4()),
            report_id=report_id,
            status=ReportStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        await self.repository.create_execution(execution)

        try:
            raw_data = await cube.query(
                db=None, tenant_id=tenant_id, filters=filters, granularity=granularity
            )
            output_format_str = config.get("output_format", "json")
            output_format = OutputFormat(output_format_str)

            output_path = f"/tmp/reports/{execution.id}.{output_format.value}"

            if output_format == OutputFormat.CSV:
                output_data = self._render_csv(raw_data)
            elif output_format == OutputFormat.PDF:
                output_data = self._render_pdf_stub(raw_data, report.name)
            else:
                output_data = json.dumps(raw_data, indent=2, default=str)

            import os
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output_data)

            execution.status = ReportStatus.COMPLETED
            execution.output_path = output_path
            execution.output_format = output_format
            execution.completed_at = datetime.now(timezone.utc)
        except Exception as exc:
            execution.status = ReportStatus.FAILED
            execution.error = str(exc)
            execution.completed_at = datetime.now(timezone.utc)

        await self.repository.update_execution(execution)
        return execution

    # ── Export Engine (B-3) ──────────────────────────────────────────────────

    def _render_csv(self, data: list[dict]) -> str:
        """Stream CSV from data rows."""
        if not data:
            return ""
        buf = io.StringIO()
        headers = list(data[0].keys())
        writer = csv.DictWriter(buf, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
        return buf.getvalue()

    def _render_pdf_stub(self, data: list[dict], title: str = "Report") -> str:
        """Render PDF content as structured JSON for downstream PDF generation."""
        return json.dumps(
            {
                "title": title,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_rows": len(data),
                "data": data,
                "format": "pdf",
                "render_engine": "charts+tables",
            },
            indent=2,
            default=str,
        )

    async def export(
        self,
        execution_id: str,
        fmt: OutputFormat = OutputFormat.JSON,
    ) -> dict:
        execution = await self.repository.get_execution(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        if execution.status != ReportStatus.COMPLETED:
            raise ValueError(
                f"Execution {execution_id} is {execution.status.value}, not completed"
            )

        if execution.output_path:
            import os
            if os.path.exists(execution.output_path):
                with open(execution.output_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return {
                    "content": content,
                    "format": execution.output_format.value,
                    "path": execution.output_path,
                }

        return {"content": "", "format": fmt.value, "path": None}

    async def export_report(
        self,
        report_id: str,
        tenant_id: str,
        fmt: OutputFormat = OutputFormat.CSV,
    ) -> dict:
        """Execute a report and return the exported content in the requested format."""
        report = await self.repository.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        original_config = dict(report.config or {})
        report.config = {**(report.config or {}), "output_format": fmt.value}
        execution = await self.generate(report_id, tenant_id)
        report.config = original_config
        if execution.status == ReportStatus.FAILED:
            raise ValueError(f"Report execution failed: {execution.error}")
        return await self.export(execution.id, fmt)

    # ── Report Sharing (B-2) ─────────────────────────────────────────────────

    async def share_report(
        self,
        report_id: str,
        user_id: str,
        permission: PermissionLevel = PermissionLevel.VIEW,
        shared_by: str = "",
    ) -> ReportShare:
        report = await self.repository.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        share = ReportShare(
            id=str(uuid.uuid4()),
            report_id=report_id,
            user_id=user_id,
            permission=permission,
            shared_by=shared_by,
        )
        return await self.repository.create_share(share)

    async def check_permission(
        self, report_id: str, user_id: str, required: PermissionLevel = PermissionLevel.VIEW
    ) -> bool:
        perm = await self.repository.get_user_permission(report_id, user_id)
        if perm is None:
            return False
        hierarchy = {
            PermissionLevel.VIEW: 1,
            PermissionLevel.EDIT: 2,
            PermissionLevel.ADMIN: 3,
        }
        return hierarchy.get(perm, 0) >= hierarchy.get(required, 0)

    async def remove_share(self, share_id: str) -> bool:
        return await self.repository.delete_share(share_id)

    async def list_shares(self, report_id: str) -> list[ReportShare]:
        return await self.repository.list_shares(report_id)

    # ── Scheduled Reports (B-4) ─────────────────────────────────────────────

    async def create_schedule(
        self,
        tenant_id: str,
        report_id: str,
        cadence: ScheduleCadence,
        recipients: list[str] | None = None,
    ) -> ScheduledReport:
        report = await self.repository.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        schedule = ScheduledReport(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            report_id=report_id,
            cadence=cadence,
            recipients=recipients or [],
            next_run=_compute_next_run(cadence),
        )
        return await self.repository.create_schedule(schedule)

    async def get_schedule(self, schedule_id: str) -> ScheduledReport | None:
        return await self.repository.get_schedule(schedule_id)

    async def list_schedules(self, tenant_id: str | None = None) -> list[ScheduledReport]:
        return await self.repository.list_schedules(tenant_id)

    async def update_schedule(
        self,
        schedule_id: str,
        cadence: ScheduleCadence | None = None,
        recipients: list[str] | None = None,
        enabled: bool | None = None,
    ) -> ScheduledReport:
        schedule = await self.repository.get_schedule(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")
        if cadence is not None:
            schedule.cadence = cadence
            schedule.next_run = _compute_next_run(cadence)
        if recipients is not None:
            schedule.recipients = recipients
        if enabled is not None:
            schedule.enabled = enabled
        return await self.repository.update_schedule(schedule)

    async def delete_schedule(self, schedule_id: str) -> bool:
        return await self.repository.delete_schedule(schedule_id)

    async def execute_due_schedules(self) -> list[dict[str, Any]]:
        """Pick up due schedules, execute reports, send email stubs."""
        due = await self.repository.get_due_schedules()
        results = []
        for schedule in due:
            try:
                execution = await self.generate(schedule.report_id, schedule.tenant_id)
                schedule.last_run = datetime.now(timezone.utc)
                schedule.next_run = _compute_next_run(schedule.cadence, schedule.last_run)
                await self.repository.update_schedule(schedule)
                results.append(
                    {
                        "schedule_id": schedule.id,
                        "report_id": schedule.report_id,
                        "execution_id": execution.id,
                        "status": execution.status.value,
                        "recipients": schedule.recipients,
                        "email_sent": True,
                    }
                )
            except Exception as exc:
                logger.exception("Scheduled report execution failed: %s", schedule.id)
                results.append(
                    {
                        "schedule_id": schedule.id,
                        "report_id": schedule.report_id,
                        "status": "failed",
                        "error": str(exc),
                    }
                )
        return results
