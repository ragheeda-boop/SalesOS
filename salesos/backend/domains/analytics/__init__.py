"""Analytics & Reporting Domain — cubes, reports, schedules, and export engine.

Zero cross-domain imports. All external data flows through cube.query(db, ...).
"""

from domains.analytics.models import (
    AnalyticsCube,
    CubeType,
    DomainMetrics,
    Granularity,
    OutputFormat,
    PermissionLevel,
    ReportDefinition,
    ReportExecution,
    ReportShare,
    ReportStatus,
    ScheduledReport,
    ScheduleCadence,
    VisualizationType,
)
from domains.analytics.cubes import PipelineCube, ForecastCube, TeamCube, ActivityCube
from domains.analytics.engine import ReportEngine
from domains.analytics.repository import InMemoryReportRepository

__all__ = [
    "AnalyticsCube",
    "CubeType",
    "DomainMetrics",
    "Granularity",
    "OutputFormat",
    "PermissionLevel",
    "ReportDefinition",
    "ReportExecution",
    "ReportShare",
    "ReportStatus",
    "ScheduledReport",
    "ScheduleCadence",
    "VisualizationType",
    "PipelineCube",
    "ForecastCube",
    "TeamCube",
    "ActivityCube",
    "ReportEngine",
    "InMemoryReportRepository",
]
