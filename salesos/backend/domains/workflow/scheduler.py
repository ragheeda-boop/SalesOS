"""Scheduled job scheduler — cron expressions, one-time delays, recurring intervals."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from domains.workflow.models import JobExecution, ScheduledJob

logger = logging.getLogger(__name__)


def parse_cron_next_run(cron_expr: str, now: datetime | None = None) -> datetime | None:
    """Calculate next run time from a simplified cron expression.

    Supports: minute hour day_of_month month day_of_week
    Special values: *, */N, lists (1,3,5), ranges (1-5)
    """
    now = now or datetime.now(timezone.utc)
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        return None

    minute_p, hour_p, dom_p, month_p, dow_p = parts

    def _matches_field(value: int, field: str, max_val: int) -> bool:
        if field == "*":
            return True
        if field.startswith("*/"):
            step = int(field[2:])
            return value % step == 0
        if "," in field:
            return value in [int(x) for x in field.split(",")]
        if "-" in field:
            lo, hi = [int(x) for x in field.split("-")]
            return lo <= value <= hi
        return value == int(field)

    # Search forward up to 366 days
    candidate = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _ in range(366 * 24 * 60):
        if (
            _matches_field(candidate.minute, minute_p, 59)
            and _matches_field(candidate.hour, hour_p, 23)
            and _matches_field(candidate.day, dom_p, 31)
            and _matches_field(candidate.month, month_p, 12)
            and _matches_field(candidate.weekday(), dow_p, 6)
        ):
            return candidate
        candidate += timedelta(minutes=1)
    return None


def parse_interval_next_run(interval_str: str, last_run: datetime | None = None, now: datetime | None = None) -> datetime | None:
    """Calculate next run time from an interval string like '30m', '2h', '1d', '45s'.

    Supported units: s (seconds), m (minutes), h (hours), d (days)
    """
    now = now or datetime.now(timezone.utc)
    match = re.match(r"^(\d+)\s*(s|m|h|d)$", interval_str.strip())
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    deltas = {"s": timedelta(seconds=amount), "m": timedelta(minutes=amount), "h": timedelta(hours=amount), "d": timedelta(days=amount)}
    base = last_run or now
    return base + deltas[unit]


def parse_one_time_next_run(iso_timestamp: str) -> datetime | None:
    """Parse an ISO 8601 timestamp for one-time job execution."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


class JobScheduler:
    """Manages scheduled job execution — picks up due jobs, executes, updates state."""

    def __init__(self, repository: Any) -> None:
        self._repo = repository
        self._handlers: dict[str, Any] = {}

    def register_handler(self, job_type: str, handler: Any) -> None:
        """Register a handler function for a specific job type."""
        self._handlers[job_type] = handler

    async def tick(self, now: datetime | None = None) -> list[JobExecution]:
        """Process all due jobs. Returns list of executions created."""
        now = now or datetime.now(timezone.utc)
        due_jobs = await self._repo.list_due_jobs(now)
        executions: list[JobExecution] = []

        for job in due_jobs:
            exec_result = await self._execute_job(job, now)
            if exec_result:
                executions.append(exec_result)

        return executions

    async def _execute_job(self, job: ScheduledJob, now: datetime) -> JobExecution | None:
        """Execute a single job and update its state."""
        execution = JobExecution(
            id=f"jobexec_{job.id}_{int(now.timestamp())}",
            job_id=job.id,
            tenant_id=job.tenant_id,
            status="running",
            started_at=now,
        )
        execution = await self._repo.create_job_execution(execution)

        handler = self._handlers.get(job.job_type)
        if not handler:
            execution.status = "failed"
            execution.error = f"No handler for job_type '{job.job_type}'"
            execution.completed_at = now
            await self._repo.update_job_execution(execution)
            await self._update_job_after_failure(job, execution.error, now)
            return execution

        try:
            result = await handler(job.config, job.payload, job.tenant_id)
            execution.status = "completed"
            execution.result = result
            execution.completed_at = datetime.now(timezone.utc)
            await self._repo.update_job_execution(execution)
            await self._update_job_after_success(job, execution.completed_at)
            return execution
        except Exception as exc:
            logger.exception("Job %s (%s) failed: %s", job.name, job.id, exc)
            execution.status = "failed"
            execution.error = str(exc)
            execution.completed_at = datetime.now(timezone.utc)
            await self._repo.update_job_execution(execution)
            await self._update_job_after_failure(job, str(exc), execution.completed_at)
            return execution

    async def _update_job_after_success(self, job: ScheduledJob, completed_at: datetime) -> None:
        job.last_run_at = completed_at
        job.run_count += 1
        job.retry_count = 0
        job.next_run_at = self._calculate_next_run(job, completed_at)
        if not job.next_run_at:
            job.status = "completed"
        await self._repo.update_job(job)

    async def _update_job_after_failure(self, job: ScheduledJob, error: str, completed_at: datetime) -> None:
        job.last_run_at = completed_at
        job.run_count += 1
        job.retry_count += 1
        if job.retry_count > job.max_retries:
            job.status = "failed"
        else:
            job.next_run_at = self._calculate_next_run(job, completed_at)
        await self._repo.update_job(job)

    def _calculate_next_run(self, job: ScheduledJob, base: datetime) -> datetime | None:
        """Calculate the next run time based on job type and schedule."""
        if job.job_type == "cron":
            return parse_cron_next_run(job.schedule, base)
        elif job.job_type == "interval":
            return parse_interval_next_run(job.schedule, base, base)
        elif job.job_type == "one_time":
            return None  # one-time jobs do not reschedule
        return None
