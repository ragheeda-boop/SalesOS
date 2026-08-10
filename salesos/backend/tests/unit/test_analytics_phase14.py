"""Tests for Analytics & Reporting domain — Phase 14 extensions.

Covers: unified analytics, report sharing, export engine, scheduled reports, pagination.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from domains.analytics.engine import CUBE_REGISTRY, ReportEngine, _compute_next_run
from domains.analytics.models import (
    CubeType,
    DomainMetrics,
    OutputFormat,
    PermissionLevel,
    ReportDefinition,
    ReportExecution,
    ReportStatus,
    ScheduleCadence,
    VisualizationType,
)
from domains.analytics.repository import InMemoryReportRepository

# Fixture rows for export path tests only — cubes stay honestly empty.
_PIPELINE_FIXTURE_ROWS = [
    {
        "stage": "prospecting",
        "owner": "owner-1",
        "date": "2026-08-01T00:00:00+00:00",
        "company": "comp-1",
        "count": 5,
        "value": 250000.0,
        "weighted_value": 25000.0,
        "avg_deal_size": 50000.0,
    },
]

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def repo():
    return InMemoryReportRepository()


@pytest.fixture
def engine(repo):
    return ReportEngine(repository=repo)


@pytest.fixture
def pipeline_cube_with_rows(monkeypatch):
    """Inject deterministic pipeline rows so export formatting is tested."""

    async def _query(*_args, **_kwargs):
        return list(_PIPELINE_FIXTURE_ROWS)

    monkeypatch.setattr(CUBE_REGISTRY[CubeType.PIPELINE], "query", _query)


@pytest.fixture
async def sample_report(repo):
    r = ReportDefinition(
        id=str(uuid.uuid4()),
        tenant_id="t-1",
        name="Test Report",
        type=CubeType.PIPELINE,
        config={"filters": {}, "granularity": "week", "output_format": "json"},
        metrics=["revenue", "deals"],
        dimensions=["stage", "owner"],
        visualization_type=VisualizationType.TABLE,
        created_by="user-1",
        schedule="0 9 * * 1",
    )
    return await repo.create_report(r)


@pytest.fixture
async def csv_report(repo):
    r = ReportDefinition(
        id=str(uuid.uuid4()),
        tenant_id="t-1",
        name="CSV Report",
        type=CubeType.PIPELINE,
        config={"filters": {}, "granularity": "week", "output_format": "csv"},
        metrics=["revenue"],
        dimensions=["stage"],
        visualization_type=VisualizationType.TABLE,
        created_by="user-1",
    )
    return await repo.create_report(r)


# ── Tests: Unified Analytics (B-1) ──────────────────────────────────────────


class TestUnifiedAnalytics:
    @pytest.mark.asyncio
    async def test_returns_domain_metrics(self, engine):
        metrics = await engine.get_unified_analytics("t-1")
        assert isinstance(metrics, DomainMetrics)
        assert metrics.total_deals >= 0
        assert metrics.total_revenue >= 0

    @pytest.mark.asyncio
    async def test_metrics_has_all_fields(self, engine):
        metrics = await engine.get_unified_analytics("t-1")
        assert hasattr(metrics, "total_deals")
        assert hasattr(metrics, "total_revenue")
        assert hasattr(metrics, "total_employees")
        assert hasattr(metrics, "total_workflows")
        assert hasattr(metrics, "conversion_rate")
        assert hasattr(metrics, "pipeline_value")
        assert hasattr(metrics, "avg_deal_size")
        assert hasattr(metrics, "win_rate")
        assert hasattr(metrics, "active_automations")
        assert hasattr(metrics, "generated_at")

    @pytest.mark.asyncio
    async def test_conversion_rate_is_percentage(self, engine):
        metrics = await engine.get_unified_analytics("t-1")
        assert 0.0 <= metrics.conversion_rate <= 100.0

    @pytest.mark.asyncio
    async def test_win_rate_is_percentage(self, engine):
        metrics = await engine.get_unified_analytics("t-1")
        assert 0.0 <= metrics.win_rate <= 100.0

    @pytest.mark.asyncio
    async def test_generated_at_is_utc(self, engine):
        metrics = await engine.get_unified_analytics("t-1")
        assert metrics.generated_at.tzinfo is not None


# ── Tests: Report Sharing (B-2) ─────────────────────────────────────────────


class TestReportSharing:
    @pytest.mark.asyncio
    async def test_share_report(self, engine, sample_report):
        share = await engine.share_report(
            sample_report.id, "user-2", PermissionLevel.VIEW, shared_by="user-1"
        )
        assert share.report_id == sample_report.id
        assert share.user_id == "user-2"
        assert share.permission == PermissionLevel.VIEW

    @pytest.mark.asyncio
    async def test_share_nonexistent_report(self, engine):
        with pytest.raises(ValueError, match="not found"):
            await engine.share_report("nonexistent", "user-2")

    @pytest.mark.asyncio
    async def test_list_shares(self, engine, sample_report):
        await engine.share_report(sample_report.id, "user-2")
        await engine.share_report(sample_report.id, "user-3", PermissionLevel.EDIT)
        shares = await engine.list_shares(sample_report.id)
        assert len(shares) == 2

    @pytest.mark.asyncio
    async def test_check_permission_view(self, engine, sample_report):
        await engine.share_report(sample_report.id, "user-2", PermissionLevel.VIEW)
        assert await engine.check_permission(sample_report.id, "user-2") is True

    @pytest.mark.asyncio
    async def test_check_permission_upgrade(self, engine, sample_report):
        await engine.share_report(sample_report.id, "user-2", PermissionLevel.VIEW)
        has_edit = await engine.check_permission(sample_report.id, "user-2", PermissionLevel.EDIT)
        assert has_edit is False

    @pytest.mark.asyncio
    async def test_check_permission_admin_has_view(self, engine, sample_report):
        await engine.share_report(sample_report.id, "user-2", PermissionLevel.ADMIN)
        has_view = await engine.check_permission(sample_report.id, "user-2", PermissionLevel.VIEW)
        assert has_view is True

    @pytest.mark.asyncio
    async def test_check_permission_unshared_user(self, engine, sample_report):
        has_view = await engine.check_permission(sample_report.id, "user-999")
        assert has_view is False

    @pytest.mark.asyncio
    async def test_remove_share(self, engine, sample_report):
        share = await engine.share_report(sample_report.id, "user-2")
        removed = await engine.remove_share(share.id)
        assert removed is True
        shares = await engine.list_shares(sample_report.id)
        assert len(shares) == 0

    @pytest.mark.asyncio
    async def test_remove_nonexistent_share(self, engine):
        removed = await engine.remove_share("nonexistent")
        assert removed is False


# ── Tests: Export Engine (B-3) ──────────────────────────────────────────────


class TestExportEngine:
    @pytest.mark.asyncio
    async def test_csv_render(self, engine):
        data = [{"name": "Alice", "value": 100}, {"name": "Bob", "value": 200}]
        csv = engine._render_csv(data)
        lines = csv.strip().splitlines()
        assert "name" in lines[0] and "value" in lines[0]
        assert "Alice" in lines[1]

    @pytest.mark.asyncio
    async def test_csv_render_empty(self, engine):
        csv = engine._render_csv([])
        assert csv == ""

    @pytest.mark.asyncio
    async def test_pdf_not_implemented(self, engine, csv_report, pipeline_cube_with_rows):
        with pytest.raises(ValueError, match="PDF export not implemented"):
            await engine.export_report(csv_report.id, "t-1", OutputFormat.PDF)

    @pytest.mark.asyncio
    async def test_export_report_csv(self, engine, csv_report, pipeline_cube_with_rows):
        result = await engine.export_report(csv_report.id, "t-1", OutputFormat.CSV)
        assert result["format"] == "csv"
        assert "stage" in result["content"]

    @pytest.mark.asyncio
    async def test_export_report_json(
        self, engine, sample_report, pipeline_cube_with_rows
    ):
        result = await engine.export_report(sample_report.id, "t-1", OutputFormat.JSON)
        assert result["format"] == "json"
        data = json.loads(result["content"])
        assert len(data) > 0
        assert data[0]["stage"] == "prospecting"

    @pytest.mark.asyncio
    async def test_export_report_pdf(self, engine, sample_report):
        with pytest.raises(ValueError, match="PDF export not implemented"):
            await engine.export_report(sample_report.id, "t-1", OutputFormat.PDF)

    @pytest.mark.asyncio
    async def test_export_nonexistent_report(self, engine):
        with pytest.raises(ValueError, match="not found"):
            await engine.export_report("nonexistent", "t-1")


# ── Tests: Scheduled Reports (B-4) ──────────────────────────────────────────


class TestScheduledReports:
    @pytest.mark.asyncio
    async def test_create_schedule(self, engine, sample_report):
        schedule = await engine.create_schedule(
            "t-1",
            sample_report.id,
            ScheduleCadence.WEEKLY,
            recipients=["user@example.com"],
        )
        assert schedule.report_id == sample_report.id
        assert schedule.cadence == ScheduleCadence.WEEKLY
        assert schedule.next_run is not None

    @pytest.mark.asyncio
    async def test_create_schedule_nonexistent_report(self, engine):
        with pytest.raises(ValueError, match="not found"):
            await engine.create_schedule("t-1", "nonexistent", ScheduleCadence.DAILY)

    @pytest.mark.asyncio
    async def test_list_schedules(self, engine, sample_report):
        await engine.create_schedule("t-1", sample_report.id, ScheduleCadence.DAILY)
        await engine.create_schedule("t-1", sample_report.id, ScheduleCadence.MONTHLY)
        schedules = await engine.list_schedules("t-1")
        assert len(schedules) == 2

    @pytest.mark.asyncio
    async def test_update_schedule_cadence(self, engine, sample_report):
        schedule = await engine.create_schedule("t-1", sample_report.id, ScheduleCadence.DAILY)
        updated = await engine.update_schedule(schedule.id, cadence=ScheduleCadence.MONTHLY)
        assert updated.cadence == ScheduleCadence.MONTHLY
        assert updated.next_run is not None

    @pytest.mark.asyncio
    async def test_update_schedule_recipients(self, engine, sample_report):
        schedule = await engine.create_schedule("t-1", sample_report.id, ScheduleCadence.WEEKLY)
        updated = await engine.update_schedule(schedule.id, recipients=["new@example.com"])
        assert updated.recipients == ["new@example.com"]

    @pytest.mark.asyncio
    async def test_update_schedule_disable(self, engine, sample_report):
        schedule = await engine.create_schedule("t-1", sample_report.id, ScheduleCadence.WEEKLY)
        updated = await engine.update_schedule(schedule.id, enabled=False)
        assert updated.enabled is False

    @pytest.mark.asyncio
    async def test_delete_schedule(self, engine, sample_report):
        schedule = await engine.create_schedule("t-1", sample_report.id, ScheduleCadence.WEEKLY)
        deleted = await engine.delete_schedule(schedule.id)
        assert deleted is True
        assert await engine.get_schedule(schedule.id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_schedule(self, engine):
        deleted = await engine.delete_schedule("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_execute_due_schedules(self, engine, sample_report):
        schedule = await engine.create_schedule("t-1", sample_report.id, ScheduleCadence.WEEKLY)
        # Force next_run to the past
        schedule.next_run = datetime.now(UTC) - timedelta(hours=1)
        await engine.repository.update_schedule(schedule)
        results = await engine.execute_due_schedules()
        assert len(results) == 1
        assert results[0]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_due_schedules_none_due(self, engine, sample_report):
        _ = await engine.create_schedule("t-1", sample_report.id, ScheduleCadence.WEEKLY)
        # next_run is in the future — should not execute
        results = await engine.execute_due_schedules()
        assert len(results) == 0


# ── Tests: Compute Next Run ─────────────────────────────────────────────────


class TestComputeNextRun:
    def test_daily_next_run(self):
        now = datetime(2026, 7, 16, 12, 0, 0, tzinfo=UTC)
        next_run = _compute_next_run(ScheduleCadence.DAILY, now)
        assert next_run.day == 17

    def test_weekly_next_run(self):
        now = datetime(2026, 7, 16, 12, 0, 0, tzinfo=UTC)
        next_run = _compute_next_run(ScheduleCadence.WEEKLY, now)
        assert next_run.day == 23

    def test_monthly_next_run(self):
        now = datetime(2026, 7, 16, 12, 0, 0, tzinfo=UTC)
        next_run = _compute_next_run(ScheduleCadence.MONTHLY, now)
        assert next_run.month == 8

    def test_quarterly_next_run(self):
        now = datetime(2026, 7, 16, 12, 0, 0, tzinfo=UTC)
        next_run = _compute_next_run(ScheduleCadence.QUARTERLY, now)
        assert next_run.month == 10


# ── Tests: Keyset Pagination (B-1) ─────────────────────────────────────────


class TestKeysetPagination:
    @pytest.mark.asyncio
    async def test_list_reports_with_limit(self, repo):
        for i in range(5):
            r = ReportDefinition(
                id=str(uuid.uuid4()),
                tenant_id="t-1",
                name=f"Report {i}",
                type=CubeType.PIPELINE,
            )
            await repo.create_report(r)
        page, next_cursor = await repo.list_reports(tenant_id="t-1", limit=2)
        assert len(page) == 2
        assert next_cursor is not None

    @pytest.mark.asyncio
    async def test_list_reports_cursor_pagination(self, repo):
        ids = []
        for i in range(5):
            r = ReportDefinition(
                id=str(uuid.uuid4()),
                tenant_id="t-1",
                name=f"Report {i}",
                type=CubeType.PIPELINE,
            )
            await repo.create_report(r)
            ids.append(r.id)
        page1, cursor = await repo.list_reports(tenant_id="t-1", limit=2)
        assert len(page1) == 2
        page2, cursor2 = await repo.list_reports(tenant_id="t-1", limit=2, cursor=cursor)
        assert len(page2) == 2
        assert page1[0].id != page2[0].id

    @pytest.mark.asyncio
    async def test_list_reports_last_page(self, repo):
        for i in range(3):
            r = ReportDefinition(
                id=str(uuid.uuid4()),
                tenant_id="t-1",
                name=f"Report {i}",
                type=CubeType.PIPELINE,
            )
            await repo.create_report(r)
        page, next_cursor = await repo.list_reports(tenant_id="t-1", limit=50)
        assert len(page) == 3
        assert next_cursor is None

    @pytest.mark.asyncio
    async def test_list_executions_with_pagination(self, repo):
        for _ in range(5):
            e = ReportExecution(
                id=str(uuid.uuid4()),
                report_id="r-1",
                status=ReportStatus.COMPLETED,
            )
            await repo.create_execution(e)
        page, next_cursor = await repo.list_executions(report_id="r-1", limit=2)
        assert len(page) == 2


# ── Tests: Existing functionality preserved ──────────────────────────────────


class TestExistingCRUD:
    @pytest.mark.asyncio
    async def test_create_and_get_report(self, repo):
        r = ReportDefinition(
            id=str(uuid.uuid4()),
            tenant_id="t-1",
            name="Preserved",
            type=CubeType.FORECAST,
            metrics=["forecast_amount"],
            dimensions=["quarter"],
            visualization_type=VisualizationType.LINE,
            created_by="user-1",
        )
        await repo.create_report(r)
        found = await repo.get_report(r.id)
        assert found is not None
        assert found.metrics == ["forecast_amount"]
        assert found.visualization_type == VisualizationType.LINE
        assert found.created_by == "user-1"

    @pytest.mark.asyncio
    async def test_report_with_all_new_fields(self, repo):
        r = ReportDefinition(
            id=str(uuid.uuid4()),
            tenant_id="t-1",
            name="Full Report",
            type=CubeType.CUSTOM,
            config={"key": "value"},
            metrics=["revenue", "deals", "pipeline"],
            dimensions=["stage", "owner", "date"],
            filters={"stage": ["prospecting"]},
            visualization_type=VisualizationType.BAR,
            created_by="admin-1",
        )
        created = await repo.create_report(r)
        assert created.metrics == ["revenue", "deals", "pipeline"]
        assert created.dimensions == ["stage", "owner", "date"]
        assert created.filters == {"stage": ["prospecting"]}
        assert created.visualization_type == VisualizationType.BAR

    @pytest.mark.asyncio
    async def test_report_status_enum_values(self):
        assert ReportStatus.PENDING.value == "pending"
        assert ReportStatus.RUNNING.value == "running"
        assert ReportStatus.COMPLETED.value == "completed"
        assert ReportStatus.FAILED.value == "failed"

    @pytest.mark.asyncio
    def test_visualization_type_enum(self):
        assert VisualizationType.TABLE.value == "table"
        assert VisualizationType.BAR.value == "bar"
        assert VisualizationType.LINE.value == "line"
        assert VisualizationType.PIE.value == "pie"
        assert VisualizationType.FUNNEL.value == "funnel"

    @pytest.mark.asyncio
    async def test_engine_generates_execution(self, engine, sample_report):
        execution = await engine.generate(sample_report.id, "t-1")
        assert execution.status == ReportStatus.COMPLETED
        assert execution.output_path is not None
        assert os.path.exists(execution.output_path)
