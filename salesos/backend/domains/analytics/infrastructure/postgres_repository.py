"""PostgreSQL repository for Analytics & Reporting domain."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from domains.analytics.infrastructure.models import (
    ReportExecutionModel,
    ReportModel,
    ReportShareModel,
    ScheduledReportModel,
)
from domains.analytics.models import (
    CubeType,
    OutputFormat,
    PermissionLevel,
    ReportDefinition,
    ReportExecution,
    ReportShare,
    ReportStatus,
    ScheduledReport,
    ScheduleCadence,
)


class PostgresReportRepository:
    """PostgreSQL-backed repository for reports, executions, shares, and schedules."""

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
            metrics=report.metrics,
            dimensions=report.dimensions,
            filters=report.filters,
            visualization_type=report.visualization_type.value,
            created_by=report.created_by,
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

    async def list_reports(
        self,
        tenant_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
        cursor: str | None = None,
    ) -> tuple[list[ReportDefinition], str | None]:
        stmt = select(ReportModel).order_by(ReportModel.created_at.desc())
        if tenant_id:
            stmt = stmt.where(ReportModel.tenant_id == tenant_id)
        if cursor:
            stmt = stmt.where(ReportModel.id < cursor)
        stmt = stmt.limit(limit + 1)
        result = await self._session.execute(stmt)
        models = list(result.scalars().all())
        has_next = len(models) > limit
        models = models[:limit]
        next_cursor = models[-1].id if has_next and models else None
        return [_report_model_to_domain(m) for m in models], next_cursor

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
        model.metrics = report.metrics
        model.dimensions = report.dimensions
        model.filters = report.filters
        model.visualization_type = report.visualization_type.value
        model.created_by = report.created_by
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
        self,
        report_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ReportExecution], str | None]:
        stmt = select(ReportExecutionModel).order_by(
            ReportExecutionModel.started_at.desc().nullslast()
        )
        if report_id:
            stmt = stmt.where(ReportExecutionModel.report_id == report_id)
        stmt = stmt.limit(limit + 1).offset(offset)
        result = await self._session.execute(stmt)
        models = list(result.scalars().all())
        has_next = len(models) > limit
        models = models[:limit]
        next_cursor = models[-1].id if has_next and models else None
        return [_execution_model_to_domain(m) for m in models], next_cursor

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

    # ── Report Sharing ───────────────────────────────────────────────────────

    async def create_share(self, share: ReportShare) -> ReportShare:
        model = ReportShareModel(
            id=share.id,
            report_id=share.report_id,
            user_id=share.user_id,
            permission=share.permission.value,
            shared_by=share.shared_by,
            created_at=share.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return share

    async def get_share(self, share_id: str) -> ReportShare | None:
        result = await self._session.execute(
            select(ReportShareModel).where(ReportShareModel.id == share_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return _share_model_to_domain(model)

    async def list_shares(self, report_id: str) -> list[ReportShare]:
        result = await self._session.execute(
            select(ReportShareModel).where(ReportShareModel.report_id == report_id)
        )
        return [_share_model_to_domain(m) for m in result.scalars().all()]

    async def get_user_permission(
        self, report_id: str, user_id: str
    ) -> PermissionLevel | None:
        result = await self._session.execute(
            select(ReportShareModel).where(
                ReportShareModel.report_id == report_id,
                ReportShareModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return PermissionLevel(model.permission)

    async def delete_share(self, share_id: str) -> bool:
        result = await self._session.execute(
            select(ReportShareModel).where(ReportShareModel.id == share_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    async def update_share(self, share: ReportShare) -> ReportShare:
        result = await self._session.execute(
            select(ReportShareModel).where(ReportShareModel.id == share.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Share {share.id} not found")
        model.permission = share.permission.value
        await self._session.flush()
        return share

    # ── Scheduled Reports ────────────────────────────────────────────────────

    async def create_schedule(self, schedule: ScheduledReport) -> ScheduledReport:
        model = ScheduledReportModel(
            id=schedule.id,
            tenant_id=schedule.tenant_id,
            report_id=schedule.report_id,
            cadence=schedule.cadence.value,
            recipients=schedule.recipients,
            next_run=schedule.next_run,
            last_run=schedule.last_run,
            enabled=schedule.enabled,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return schedule

    async def get_schedule(self, schedule_id: str) -> ScheduledReport | None:
        result = await self._session.execute(
            select(ScheduledReportModel).where(ScheduledReportModel.id == schedule_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return _schedule_model_to_domain(model)

    async def list_schedules(
        self, tenant_id: str | None = None
    ) -> list[ScheduledReport]:
        stmt = select(ScheduledReportModel).order_by(ScheduledReportModel.created_at.desc())
        if tenant_id:
            stmt = stmt.where(ScheduledReportModel.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return [_schedule_model_to_domain(m) for m in result.scalars().all()]

    async def get_due_schedules(
        self, before: datetime | None = None
    ) -> list[ScheduledReport]:
        before = before or datetime.now(timezone.utc)
        stmt = (
            select(ScheduledReportModel)
            .where(
                ScheduledReportModel.enabled == True,  # noqa: E712
                ScheduledReportModel.next_run <= before,
            )
            .order_by(ScheduledReportModel.next_run)
        )
        result = await self._session.execute(stmt)
        return [_schedule_model_to_domain(m) for m in result.scalars().all()]

    async def update_schedule(self, schedule: ScheduledReport) -> ScheduledReport:
        result = await self._session.execute(
            select(ScheduledReportModel).where(ScheduledReportModel.id == schedule.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Schedule {schedule.id} not found")
        model.cadence = schedule.cadence.value
        model.recipients = schedule.recipients
        model.next_run = schedule.next_run
        model.last_run = schedule.last_run
        model.enabled = schedule.enabled
        model.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return schedule

    async def delete_schedule(self, schedule_id: str) -> bool:
        result = await self._session.execute(
            select(ScheduledReportModel).where(ScheduledReportModel.id == schedule_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True


def _report_model_to_domain(model: ReportModel) -> ReportDefinition:
    from domains.analytics.models import VisualizationType
    return ReportDefinition(
        id=model.id,
        tenant_id=model.tenant_id,
        name=model.name,
        type=CubeType(model.type),
        config=model.config or {},
        metrics=model.metrics or [],
        dimensions=model.dimensions or [],
        filters=model.filters or {},
        visualization_type=VisualizationType(model.visualization_type),
        created_by=model.created_by or "",
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


def _share_model_to_domain(model: ReportShareModel) -> ReportShare:
    return ReportShare(
        id=model.id,
        report_id=model.report_id,
        user_id=model.user_id,
        permission=PermissionLevel(model.permission),
        shared_by=model.shared_by,
        created_at=model.created_at,
    )


def _schedule_model_to_domain(model: ScheduledReportModel) -> ScheduledReport:
    return ScheduledReport(
        id=model.id,
        tenant_id=model.tenant_id,
        report_id=model.report_id,
        cadence=ScheduleCadence(model.cadence),
        recipients=model.recipients or [],
        next_run=model.next_run,
        last_run=model.last_run,
        enabled=model.enabled,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
