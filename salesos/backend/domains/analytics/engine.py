"""Report engine — generate, schedule, and export reports."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from domains.analytics.cubes import ActivityCube, ForecastCube, PipelineCube, TeamCube
from domains.analytics.models import (
    CubeType,
    Granularity,
    OutputFormat,
    ReportDefinition,
    ReportExecution,
    ReportStatus,
)
from domains.analytics.repository import InMemoryReportRepository

CUBE_REGISTRY: dict[CubeType, Any] = {
    CubeType.PIPELINE: PipelineCube(),
    CubeType.FORECAST: ForecastCube(),
    CubeType.TEAM: TeamCube(),
    CubeType.ACTIVITY: ActivityCube(),
}


class ReportEngine:
    """Central report engine that orchestrates cube queries and output generation."""

    def __init__(self, repository: InMemoryReportRepository | None = None) -> None:
        self.repository = repository or InMemoryReportRepository()
        self._schedules: dict[str, str] = {}

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

            if output_format == OutputFormat.JSON:
                output_data = json.dumps(raw_data, indent=2, default=str)
            elif output_format == OutputFormat.CSV:
                if raw_data:
                    headers = list(raw_data[0].keys())
                    lines = [",".join(headers)]
                    for row in raw_data:
                        lines.append(
                            ",".join(str(row.get(h, "")) for h in headers)
                        )
                    output_data = "\n".join(lines)
                else:
                    output_data = ""
            else:
                output_data = json.dumps({"data": raw_data, "format": "pdf_stub"}, indent=2)

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

    async def schedule(
        self,
        report_id: str,
        cron: str,
    ) -> str:
        report = await self.repository.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        report.schedule = cron
        await self.repository.update_report(report)
        self._schedules[report_id] = cron
        return cron

    async def export(
        self,
        execution_id: str,
        fmt: OutputFormat = OutputFormat.JSON,
    ) -> dict:
        execution = await self.repository.get_execution(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        if execution.status != ReportStatus.COMPLETED:
            raise ValueError(f"Execution {execution_id} is {execution.status.value}, not completed")

        if execution.output_path:
            import os
            if os.path.exists(execution.output_path):
                with open(execution.output_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return {"content": content, "format": execution.output_format.value, "path": execution.output_path}

        return {"content": "", "format": fmt.value, "path": None}
