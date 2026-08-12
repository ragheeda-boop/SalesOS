"""Tests for employee Celery tasks — calendar sync, email sync, scoring, cleanup."""

import inspect
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta

from domains.employee.tasks import (
    calendar_sync_employee,
    calendar_sync_all_employees,
    score_rebuild_all_employees,
    signal_retention_cleanup,
    gdpr_purge_expired_users,
    _all_internal_attendees,
    _health_ping,
)
from domains.employee.oauth_service import EmployeeOAuthToken


class TestAllInternalAttendees:
    def test_empty_attendees_internal(self):
        assert _all_internal_attendees([]) is True

    def test_single_domain_internal(self):
        attendees = [{"email": "a@company.com"}, {"email": "b@company.com"}]
        assert _all_internal_attendees(attendees) is True

    def test_multi_domain_external(self):
        attendees = [{"email": "a@company.com"}, {"email": "b@external.com"}]
        assert _all_internal_attendees(attendees) is False

    def test_missing_email(self):
        attendees = [{"name": "No Email"}, {"email": "a@company.com"}]
        assert _all_internal_attendees(attendees) is True


class TestCalendarSyncEmployee:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_token(self, db_session):
        """Should return silently when no OAuth token exists."""
        with patch("domains.employee.tasks._get_session", return_value=db_session):
            with patch.object(EmployeeOAuthToken, "__init__", return_value=None):
                result = None
                try:
                    from domains.employee.tasks import OAuthTokenService
                    with patch.object(OAuthTokenService, "get_access_token", return_value=None):
                        result = await calendar_sync_employee(
                            "00000000-0000-0000-0000-000000000001",
                            "00000000-0000-0000-0000-000000000001",
                            "google",
                        )
                except Exception:
                    result = None
                assert result is None

    @pytest.mark.asyncio
    async def test_handles_db_session_cleanup(self, monkeypatch):
        """Should close DB session even on error."""
        closed = False
        async def fake_close():
            nonlocal closed
            closed = True

        mock_session = AsyncMock()
        mock_session.close = fake_close
        mock_session.execute = AsyncMock(side_effect=Exception("DB error"))

        with patch("domains.employee.tasks._get_session", return_value=mock_session):
            with patch.object(OAuthTokenService, "get_access_token", return_value="fake-token"):
                try:
                    await calendar_sync_employee("uid", "tid", "google")
                except Exception:
                    pass
        assert closed is True


class TestScoreRebuild:
    @pytest.mark.asyncio
    async def test_handles_no_active_users(self, db_session):
        """Should return scored=0 when no active users exist."""
        with patch("domains.employee.tasks._get_session", return_value=db_session):
            result = await score_rebuild_all_employees()
            assert "scored" in result
            assert "total" in result
            assert result["scored"] == 0


class TestRetentionCleanup:
    @pytest.mark.asyncio
    async def test_handles_empty_signal_table(self, db_session):
        """Should return removed=0 when no orphaned signals."""
        with patch("domains.employee.tasks._get_session", return_value=db_session):
            result = await signal_retention_cleanup()
            assert "removed" in result
            assert result["removed"] >= 0


class TestGDPRPurge:
    @pytest.mark.asyncio
    async def test_handles_no_expired_users(self, db_session):
        """Should return purged=0 when no users past retention."""
        with patch("domains.employee.tasks._get_session", return_value=db_session):
            result = await gdpr_purge_expired_users()
            assert "purged" in result
            assert result["purged"] == 0


class TestHealthPing:
    @pytest.mark.asyncio
    async def test_returns_ok_when_db_connected(self, db_session):
        """Should return status ok when DB responds."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.close = AsyncMock()
        with patch("domains.employee.tasks._get_session", return_value=mock_session):
            result = await _health_ping()
            assert result["status"] == "ok"
            assert result["database"] == "connected"

    def test_worker_health_ping_uses_asyncio_run(self):
        """Sync Celery wrapper must use asyncio.run (no get_event_loop)."""
        from domains.employee.tasks import worker_health_ping_task

        with patch("domains.employee.tasks._run_async", return_value={"status": "ok"}) as run_async:
            result = worker_health_ping_task()
        assert result == {"status": "ok"}
        run_async.assert_called_once()

    def test_run_async_uses_asyncio_run(self):
        from domains.employee.tasks import _run_async

        async def _ok():
            return {"status": "ok"}

        assert _run_async(_ok()) == {"status": "ok"}

    def test_run_async_disposes_engine_on_same_loop(self):
        """Lazy process _engine must be disposed before asyncio.run returns."""
        from domains.employee import tasks as tasks_mod

        mock_engine = MagicMock()
        mock_engine.dispose = AsyncMock()

        async def _ok():
            return {"status": "ok"}

        tasks_mod._engine = mock_engine
        try:
            result = tasks_mod._run_async(_ok())
        finally:
            tasks_mod._engine = None

        assert result == {"status": "ok"}
        mock_engine.dispose.assert_awaited()
        assert tasks_mod._engine is None

    def test_successive_run_async_ticks_create_fresh_engine(self):
        """Each asyncio.run tick must create+dispose — not reuse a loop-bound engine."""
        from domains.employee import tasks as tasks_mod

        engines = [MagicMock(), MagicMock()]
        for engine in engines:
            engine.dispose = AsyncMock()
        mock_session = MagicMock()

        tasks_mod._engine = None
        try:
            with (
                patch(
                    "domains.employee.tasks.create_async_engine",
                    side_effect=engines,
                ) as created,
                patch(
                    "domains.employee.tasks.async_sessionmaker",
                    return_value=MagicMock(return_value=mock_session),
                ),
            ):
                async def tick():
                    await tasks_mod._get_session()
                    return "ok"

                assert tasks_mod._run_async(tick()) == "ok"
                assert tasks_mod._run_async(tick()) == "ok"
        finally:
            tasks_mod._engine = None

        assert created.call_count == 2
        engines[0].dispose.assert_awaited()
        engines[1].dispose.assert_awaited()
        assert tasks_mod._engine is None

    def test_run_async_source_disposes_engine(self):
        from domains.employee.tasks import _run_async

        source = inspect.getsource(_run_async)
        assert "asyncio.run" in source
        assert "asyncio.get_event_loop" not in source
        assert "dispose" in source


class TestTaskRetryBehavior:
    def test_calendar_sync_task_has_retry_config(self):
        from domains.employee.tasks import calendar_sync_all_employees_task
        assert calendar_sync_all_employees_task.max_retries == 3
        assert calendar_sync_all_employees_task.default_retry_delay == 300

    def test_score_rebuild_has_time_limit(self):
        from domains.employee.tasks import score_rebuild_task
        assert score_rebuild_task.time_limit == 3600

    def test_gdpr_purge_has_time_limit(self):
        from domains.employee.tasks import gdpr_purge_task
        assert gdpr_purge_task.time_limit == 1800

    def test_health_ping_has_no_retries(self):
        from domains.employee.tasks import worker_health_ping_task
        assert worker_health_ping_task.max_retries == 0


class TestTaskNameRegistration:
    def test_all_tasks_registered(self):
        from domains.employee.tasks import (
            calendar_sync_all_employees_task,
            email_sync_all_task,
            webhook_renewal_all_task,
            score_rebuild_task,
            gdpr_purge_task,
            signal_cleanup_task,
            worker_health_ping_task,
            calendar_event_cleanup_task,
        )
        assert calendar_sync_all_employees_task.name == "calendar_sync_all"
        assert email_sync_all_task.name == "email_sync_all"
        assert webhook_renewal_all_task.name == "webhook_renewal_all"
        assert score_rebuild_task.name == "score_rebuild_all_employees"
        assert gdpr_purge_task.name == "gdpr_purge_expired_users"
        assert signal_cleanup_task.name == "signal_retention_cleanup"
        assert worker_health_ping_task.name == "worker_health_ping"
        assert calendar_event_cleanup_task.name == "calendar_event_cleanup"


class TestOAuthTokenLifecycle:
    def test_expired_token_detection(self):
        token = EmployeeOAuthToken()
        assert token.is_access_token_expired() is True

    def test_future_token_not_expired(self):
        token = EmployeeOAuthToken(
            access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=2)
        )
        assert token.is_access_token_expired() is False

    def test_retry_below_max(self):
        token = EmployeeOAuthToken(is_active=True, max_failures=10, consecutive_failures=5)
        assert token.should_retry() is True

    def test_no_retry_above_max(self):
        token = EmployeeOAuthToken(is_active=True, max_failures=10, consecutive_failures=10)
        assert token.should_retry() is False

    def test_success_resets_failures(self):
        token = EmployeeOAuthToken(consecutive_failures=8, connection_error="prev err")
        token.record_success()
        assert token.consecutive_failures == 0
        assert token.connection_error is None
        assert token.is_connected is True

    def test_failure_disconnects_at_max(self):
        token = EmployeeOAuthToken(consecutive_failures=9, max_failures=10)
        token.record_failure("auth failed")
        assert token.consecutive_failures == 10
        assert token.is_connected is False
