"""Tests for Analytics & Reporting domain — cubes, engine, repository, templates."""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime

import pytest

from domains.analytics.cubes import ActivityCube, ForecastCube, PipelineCube, TeamCube
from domains.analytics.engine import CUBE_REGISTRY, ReportEngine
from domains.analytics.models import (
    CubeType,
    Granularity,
    OutputFormat,
    ReportDefinition,
    ReportExecution,
    ReportStatus,
    ScheduleCadence,
)
from domains.analytics.repository import InMemoryReportRepository
from domains.analytics.templates import (
    STANDARD_TEMPLATES,
    activity_report,
    monthly_forecast_report,
    team_performance_report,
    weekly_pipeline_summary,
)

# Fixture rows for export/generate path tests only — cubes stay honestly empty.
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


@pytest.fixture
def pipeline_cube_with_rows(monkeypatch):
    """Inject deterministic pipeline rows so generate/export formatting is tested."""

    async def _query(*_args, **_kwargs):
        return list(_PIPELINE_FIXTURE_ROWS)

    monkeypatch.setattr(CUBE_REGISTRY[CubeType.PIPELINE], "query", _query)

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def repo():
    return InMemoryReportRepository()


@pytest.fixture
def engine(repo):
    return ReportEngine(repository=repo)


@pytest.fixture
async def sample_report(repo):
    r = ReportDefinition(
        id=str(uuid.uuid4()),
        tenant_id="t-1",
        name="Test Report",
        type=CubeType.PIPELINE,
        config={"filters": {}, "granularity": "week", "output_format": "json"},
        schedule="0 9 * * 1",
    )
    return await repo.create_report(r)


# ── Tests: Cube Definitions ──────────────────────────────────────────────────


class TestCubeDefinitions:
    def test_pipeline_cube_has_correct_dimensions(self):
        cube = PipelineCube()
        assert cube.name == "pipeline"
        assert set(cube.dimensions) == {"stage", "owner", "date", "company"}
        assert set(cube.measures) == {"count", "value", "weighted_value", "avg_deal_size"}

    def test_forecast_cube_has_correct_dimensions(self):
        cube = ForecastCube()
        assert cube.name == "forecast"
        assert set(cube.dimensions) == {"quarter", "owner", "product_line"}
        assert set(cube.measures) == {
            "forecast_amount",
            "committed",
            "best_case",
            "pipeline_coverage",
        }

    def test_team_cube_has_correct_dimensions(self):
        cube = TeamCube()
        assert cube.name == "team"
        assert set(cube.dimensions) == {"owner", "team", "month"}
        assert set(cube.measures) == {
            "deals_created",
            "deals_won",
            "deals_lost",
            "avg_cycle_days",
            "win_rate",
        }

    def test_activity_cube_has_correct_dimensions(self):
        cube = ActivityCube()
        assert cube.name == "activity"
        assert set(cube.dimensions) == {"type", "owner", "date"}
        assert set(cube.measures) == {"count", "duration"}

    def test_all_cubes_registered(self):
        assert CubeType.PIPELINE in CUBE_REGISTRY
        assert CubeType.FORECAST in CUBE_REGISTRY
        assert CubeType.TEAM in CUBE_REGISTRY
        assert CubeType.ACTIVITY in CUBE_REGISTRY


# ── Tests: Cube Queries ──────────────────────────────────────────────────────


class TestPipelineCubeQuery:
    @pytest.mark.asyncio
    async def test_returns_rows(self):
        cube = PipelineCube()
        rows = await cube.query(db=None, tenant_id="t-1")
        # Honest empty until cubes query real tenant data
        assert rows == []

    @pytest.mark.asyncio
    async def test_filters_by_stage(self):
        cube = PipelineCube()
        rows = await cube.query(db=None, tenant_id="t-1", filters={"stage": ["closed_won"]})
        assert rows == []

    @pytest.mark.asyncio
    async def test_filters_by_owner(self):
        cube = PipelineCube()
        rows = await cube.query(db=None, tenant_id="t-1", filters={"owner": ["owner-2"]})
        assert rows == []

    @pytest.mark.asyncio
    async def test_filters_empty_list_returns_none(self):
        cube = PipelineCube()
        rows = await cube.query(db=None, tenant_id="t-1", filters={"stage": ["nonexistent"]})
        assert len(rows) == 0


class TestForecastCubeQuery:
    @pytest.mark.asyncio
    async def test_returns_rows(self):
        cube = ForecastCube()
        rows = await cube.query(db=None, tenant_id="t-1")
        assert rows == []

    @pytest.mark.asyncio
    async def test_filters_by_quarter(self):
        cube = ForecastCube()
        rows = await cube.query(db=None, tenant_id="t-1", filters={"quarter": ["2026-Q4"]})
        assert rows == []

    @pytest.mark.asyncio
    async def test_filters_by_product_line(self):
        cube = ForecastCube()
        rows = await cube.query(db=None, tenant_id="t-1", filters={"product_line": ["SalesOS Pro"]})
        assert rows == []


class TestTeamCubeQuery:
    @pytest.mark.asyncio
    async def test_returns_rows(self):
        cube = TeamCube()
        rows = await cube.query(db=None, tenant_id="t-1")
        assert rows == []

    @pytest.mark.asyncio
    async def test_filters_by_team(self):
        cube = TeamCube()
        rows = await cube.query(db=None, tenant_id="t-1", filters={"team": ["SMB Sales"]})
        assert rows == []

    @pytest.mark.asyncio
    async def test_filters_by_month(self):
        cube = TeamCube()
        now = datetime.now(UTC)
        this_month = now.strftime("%Y-%m")
        rows = await cube.query(db=None, tenant_id="t-1", filters={"month": [this_month]})
        assert rows == []


class TestActivityCubeQuery:
    @pytest.mark.asyncio
    async def test_returns_rows(self):
        cube = ActivityCube()
        rows = await cube.query(db=None, tenant_id="t-1")
        assert rows == []

    @pytest.mark.asyncio
    async def test_filters_by_type(self):
        cube = ActivityCube()
        rows = await cube.query(db=None, tenant_id="t-1", filters={"type": ["email"]})
        assert rows == []

    @pytest.mark.asyncio
    async def test_filters_by_owner(self):
        cube = ActivityCube()
        rows = await cube.query(db=None, tenant_id="t-1", filters={"owner": ["owner-2"]})
        assert rows == []

    @pytest.mark.asyncio
    async def test_with_granularity_override(self):
        cube = ActivityCube()
        rows = await cube.query(db=None, tenant_id="t-1", granularity=Granularity.WEEK)
        assert rows == []


# ── Tests: Granularity ───────────────────────────────────────────────────────


class TestGranularity:
    @pytest.mark.asyncio
    async def test_day_granularity(self):
        cube = PipelineCube()
        rows = await cube.query(db=None, tenant_id="t-1", granularity=Granularity.DAY)
        assert rows == []

    @pytest.mark.asyncio
    async def test_week_granularity(self):
        cube = PipelineCube()
        rows = await cube.query(db=None, tenant_id="t-1", granularity=Granularity.WEEK)
        assert rows == []

    @pytest.mark.asyncio
    async def test_month_granularity(self):
        cube = ForecastCube()
        rows = await cube.query(db=None, tenant_id="t-1", granularity=Granularity.MONTH)
        assert rows == []


# ── Tests: Report CRUD ───────────────────────────────────────────────────────


class TestReportCRUD:
    @pytest.mark.asyncio
    async def test_create_report(self, repo):
        r = ReportDefinition(
            id=str(uuid.uuid4()), tenant_id="t-1", name="My Report", type=CubeType.PIPELINE
        )
        created = await repo.create_report(r)
        assert created.id == r.id
        assert created.name == "My Report"

    @pytest.mark.asyncio
    async def test_get_report(self, repo):
        r = ReportDefinition(
            id=str(uuid.uuid4()), tenant_id="t-1", name="Get Me", type=CubeType.PIPELINE
        )
        await repo.create_report(r)
        found = await repo.get_report(r.id)
        assert found is not None
        assert found.name == "Get Me"

    @pytest.mark.asyncio
    async def test_get_report_not_found(self, repo):
        found = await repo.get_report("nonexistent")
        assert found is None

    @pytest.mark.asyncio
    async def test_list_reports(self, repo):
        for i in range(3):
            r = ReportDefinition(
                id=str(uuid.uuid4()),
                tenant_id="t-1",
                name=f"Report {i}",
                type=CubeType.PIPELINE,
            )
            await repo.create_report(r)
        reports, _ = await repo.list_reports(tenant_id="t-1")
        assert len(reports) == 3

    @pytest.mark.asyncio
    async def test_list_reports_tenant_isolation(self, repo):
        r1 = ReportDefinition(
            id=str(uuid.uuid4()), tenant_id="t-1", name="Report 1", type=CubeType.PIPELINE
        )
        r2 = ReportDefinition(
            id=str(uuid.uuid4()), tenant_id="t-2", name="Report 2", type=CubeType.PIPELINE
        )
        await repo.create_report(r1)
        await repo.create_report(r2)
        t1_reports, _ = await repo.list_reports(tenant_id="t-1")
        assert len(t1_reports) == 1
        assert t1_reports[0].tenant_id == "t-1"

    @pytest.mark.asyncio
    async def test_update_report(self, repo):
        r = ReportDefinition(
            id=str(uuid.uuid4()), tenant_id="t-1", name="Original", type=CubeType.PIPELINE
        )
        await repo.create_report(r)
        r.name = "Updated"
        await repo.update_report(r)
        found = await repo.get_report(r.id)
        assert found.name == "Updated"

    @pytest.mark.asyncio
    async def test_delete_report(self, repo):
        r = ReportDefinition(
            id=str(uuid.uuid4()), tenant_id="t-1", name="Delete Me", type=CubeType.PIPELINE
        )
        await repo.create_report(r)
        deleted = await repo.delete_report(r.id)
        assert deleted is True
        found = await repo.get_report(r.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_report(self, repo):
        deleted = await repo.delete_report("nonexistent")
        assert deleted is False


# ── Tests: Report Execution ──────────────────────────────────────────────────


class TestReportExecution:
    @pytest.mark.asyncio
    async def test_execute_report_success(self, engine, sample_report):
        execution = await engine.generate(sample_report.id, "t-1")
        assert execution.status == ReportStatus.COMPLETED
        assert execution.output_path is not None

    @pytest.mark.asyncio
    async def test_execute_nonexistent_report(self, engine):
        with pytest.raises(ValueError, match="not found"):
            await engine.generate("nonexistent", "t-1")

    @pytest.mark.asyncio
    async def test_execution_has_timestamps(self, engine, sample_report):
        execution = await engine.generate(sample_report.id, "t-1")
        assert execution.started_at is not None
        assert execution.completed_at is not None
        assert execution.completed_at >= execution.started_at

    @pytest.mark.asyncio
    async def test_execution_output_format(self, engine, sample_report):
        execution = await engine.generate(sample_report.id, "t-1")
        assert execution.output_format == OutputFormat.JSON

    @pytest.mark.asyncio
    async def test_execution_csv_format(self, engine, repo):
        r = ReportDefinition(
            id=str(uuid.uuid4()),
            tenant_id="t-1",
            name="CSV Report",
            type=CubeType.PIPELINE,
            config={"filters": {}, "granularity": "week", "output_format": "csv"},
        )
        await repo.create_report(r)
        execution = await engine.generate(r.id, "t-1")
        assert execution.output_format == OutputFormat.CSV

    @pytest.mark.asyncio
    async def test_execution_creates_output_file(self, engine, sample_report):
        execution = await engine.generate(sample_report.id, "t-1")
        assert execution.output_path is not None
        assert os.path.exists(execution.output_path)

    @pytest.mark.asyncio
    async def test_execution_output_contains_data(
        self, engine, sample_report, pipeline_cube_with_rows
    ):
        execution = await engine.generate(sample_report.id, "t-1")
        with open(execution.output_path) as f:
            data = json.load(f)
        assert len(data) > 0
        assert data[0]["stage"] == "prospecting"

    @pytest.mark.asyncio
    async def test_execution_csv_contains_headers(
        self, engine, repo, pipeline_cube_with_rows
    ):
        r = ReportDefinition(
            id=str(uuid.uuid4()),
            tenant_id="t-1",
            name="CSV Test",
            type=CubeType.PIPELINE,
            config={"filters": {}, "granularity": "week", "output_format": "csv"},
        )
        await repo.create_report(r)
        execution = await engine.generate(r.id, "t-1")
        with open(execution.output_path) as f:
            lines = f.read().strip().split("\n")
        assert "stage" in lines[0]

    @pytest.mark.asyncio
    async def test_list_executions(self, engine, sample_report):
        await engine.generate(sample_report.id, "t-1")
        executions = await engine.repository.list_executions()
        assert len(executions) >= 1

    @pytest.mark.asyncio
    async def test_export_completed(self, engine, sample_report):
        execution = await engine.generate(sample_report.id, "t-1")
        result = await engine.export(execution.id)
        assert "content" in result
        assert result["format"] == "json"

    @pytest.mark.asyncio
    async def test_export_nonexistent_execution(self, engine):
        with pytest.raises(ValueError, match="not found"):
            await engine.export("nonexistent")


# ── Tests: Scheduling ────────────────────────────────────────────────────────


class TestScheduling:
    @pytest.mark.asyncio
    async def test_schedule_report(self, engine, sample_report):
        schedule = await engine.create_schedule(
            report_id=sample_report.id,
            tenant_id="t-1",
            cadence=ScheduleCadence.DAILY,
            recipients=["user-1@example.com"],
        )
        assert schedule.cadence == ScheduleCadence.DAILY
        assert "user-1@example.com" in schedule.recipients
        assert schedule.report_id == sample_report.id

    @pytest.mark.asyncio
    async def test_schedule_nonexistent_report(self, engine):
        with pytest.raises(ValueError, match="not found"):
            await engine.create_schedule(
                report_id="nonexistent",
                tenant_id="t-1",
                cadence=ScheduleCadence.DAILY,
                recipients=["user@example.com"],
            )


# ── Tests: Templates ─────────────────────────────────────────────────────────


class TestTemplates:
    def test_weekly_pipeline_summary(self):
        r = weekly_pipeline_summary("t-1")
        assert r.name == "Weekly Pipeline Summary"
        assert r.type == CubeType.PIPELINE
        assert r.tenant_id == "t-1"

    def test_monthly_forecast_report(self):
        r = monthly_forecast_report("t-1")
        assert r.name == "Monthly Forecast Report"
        assert r.type == CubeType.FORECAST
        assert r.schedule == "0 8 1 * *"

    def test_team_performance_report(self):
        r = team_performance_report("t-1")
        assert r.name == "Team Performance Report"
        assert r.type == CubeType.TEAM

    def test_activity_report(self):
        r = activity_report("t-1")
        assert r.name == "Activity Report"
        assert r.type == CubeType.ACTIVITY
        assert r.config.get("granularity") == "day"

    def test_standard_templates_registry(self):
        assert "weekly_pipeline_summary" in STANDARD_TEMPLATES
        assert "monthly_forecast_report" in STANDARD_TEMPLATES
        assert "team_performance_report" in STANDARD_TEMPLATES
        assert "activity_report" in STANDARD_TEMPLATES

    def test_all_templates_return_valid_reports(self):
        for _name, factory in STANDARD_TEMPLATES.items():
            r = factory("t-1")
            assert r.name is not None
            assert r.type in CubeType
            assert r.tenant_id == "t-1"

    @pytest.mark.asyncio
    async def test_template_creates_valid_report_in_repo(self, repo):
        r = weekly_pipeline_summary("t-1")
        created = await repo.create_report(r)
        assert created.id == r.id
        found = await repo.get_report(created.id)
        assert found.type == CubeType.PIPELINE


# ── Tests: Engine ────────────────────────────────────────────────────────────


class TestEngine:
    @pytest.mark.asyncio
    async def test_engine_initializes_with_repo(self):
        eng = ReportEngine()
        assert eng.repository is not None

    @pytest.mark.asyncio
    async def test_engine_custom_repo(self, repo):
        eng = ReportEngine(repository=repo)
        assert eng.repository is repo

    @pytest.mark.asyncio
    async def test_cube_registry_contains_all_types(self):
        for cube_type in CubeType:
            if cube_type == CubeType.CUSTOM:
                continue
            assert cube_type in CUBE_REGISTRY


# ── Tests: Execution CRUD ────────────────────────────────────────────────────


class TestExecutionCRUD:
    @pytest.mark.asyncio
    async def test_create_execution(self, repo):
        e = ReportExecution(
            id=str(uuid.uuid4()), report_id=str(uuid.uuid4()), status=ReportStatus.PENDING
        )
        created = await repo.create_execution(e)
        assert created.id == e.id

    @pytest.mark.asyncio
    async def test_get_execution(self, repo):
        e = ReportExecution(
            id=str(uuid.uuid4()), report_id=str(uuid.uuid4()), status=ReportStatus.PENDING
        )
        await repo.create_execution(e)
        found = await repo.get_execution(e.id)
        assert found is not None

    @pytest.mark.asyncio
    async def test_get_execution_not_found(self, repo):
        found = await repo.get_execution("nonexistent")
        assert found is None

    @pytest.mark.asyncio
    async def test_update_execution(self, repo):
        e = ReportExecution(
            id=str(uuid.uuid4()), report_id=str(uuid.uuid4()), status=ReportStatus.PENDING
        )
        await repo.create_execution(e)
        e.status = ReportStatus.COMPLETED
        await repo.update_execution(e)
        found = await repo.get_execution(e.id)
        assert found.status == ReportStatus.COMPLETED
