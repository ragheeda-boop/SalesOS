"""PostgreSQL repository for Analytics & Reporting domain."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from domains.analytics.infrastructure.models import ReportExecutionModel, ReportModel
from domains.analytics.models import (
    CubeType,
    OutputFormat,
    ReportDefinition,
    ReportExecution,
    ReportStatus,
)


class PostgresReportRepository:
    """PostgreSQL-backed repository for reports and executions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Reports ──────────────────────────────────────────────────────────────

    async def create_report(self, report: ReportDefinition) -> ReportDefinition:
        model = ReportModel(
            id=report.id,
            tenant_id=report.tenant_id,
            name=report.name,
            type=report.type.value,
            config=report.config,
            schedule=report.schedule,
            recipients=report.recipients,
            created_at=report.created_at,
            updated_at=report.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return report

    async def get_report(self, report_id: str) -> ReportDefinition | None:
        result = await self._session.execute(
            select(ReportModel).where(ReportModel.id == report_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return _report_model_to_domain(model)

    async def list_reports(self, tenant_id: str | None = None) -> list[ReportDefinition]:
        stmt = select(ReportModel).order_by(ReportModel.created_at.desc())
        if tenant_id:
            stmt = stmt.where(ReportModel.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return [_report_model_to_domain(r) for r in result.scalars().all()]

    async def update_report(self, report: ReportDefinition) -> ReportDefinition:
        result = await self._session.execute(
            select(ReportModel).where(ReportModel.id == report.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Report {report.id} not found")
        model.name = report.name
        model.type = report.type.value
        model.config = report.config
        model.schedule = report.schedule
        model.recipients = report.recipients
        model.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return report

    async def delete_report(self, report_id: str) -> bool:
        result = await self._session.execute(
            select(ReportModel).where(ReportModel.id == report_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    # ── Executions ───────────────────────────────────────────────────────────

    async def create_execution(self, execution: ReportExecution) -> ReportExecution:
        model = ReportExecutionModel(
            id=execution.id,
            report_id=execution.report_id,
            status=execution.status.value,
            output_format=execution.output_format.value,
            output_path=execution.output_path,
            error=execution.error,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
        )
        self._session.add(model)
        await self._session.flush()
        return execution

    async def get_execution(self, execution_id: str) -> ReportExecution | None:
        result = await self._session.execute(
            select(ReportExecutionModel).where(ReportExecutionModel.id == execution_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return _execution_model_to_domain(model)

    async def list_executions(
        self, report_id: str | None = None
    ) -> list[ReportExecution]:
        stmt = select(ReportExecutionModel).order_by(
            ReportExecutionModel.started_at.desc().nullslast()
        )
        if report_id:
            stmt = stmt.where(ReportExecutionModel.report_id == report_id)
        result = await self._session.execute(stmt)
        return [_execution_model_to_domain(r) for r in result.scalars().all()]

    async def update_execution(self, execution: ReportExecution) -> ReportExecution:
        result = await self._session.execute(
            select(ReportExecutionModel).where(ReportExecutionModel.id == execution.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Execution {execution.id} not found")
        model.status = execution.status.value
        model.output_path = execution.output_path
        model.error = execution.error
        model.started_at = execution.started_at
        model.completed_at = execution.completed_at
        await self._session.flush()
        return execution


def _report_model_to_domain(model: ReportModel) -> ReportDefinition:
    return ReportDefinition(
        id=model.id,
        tenant_id=model.tenant_id,
        name=model.name,
        type=CubeType(model.type),
        config=model.config or {},
        schedule=model.schedule,
        recipients=model.recipients or [],
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _execution_model_to_domain(model: ReportExecutionModel) -> ReportExecution:
    return ReportExecution(
        id=model.id,
        report_id=model.report_id,
        status=ReportStatus(model.status),
        output_format=OutputFormat(model.output_format),
        output_path=model.output_path,
        error=model.error,
        started_at=model.started_at,
        completed_at=model.completed_at,
    )
