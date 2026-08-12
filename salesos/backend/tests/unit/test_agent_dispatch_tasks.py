"""Unit tests for agent_dispatch_all Celery asyncio bridge.

Proves the sync wrapper uses asyncio.run (via _run_async), not
get_event_loop — required for Celery prefork MainThread on Python 3.12.

Also proves same-loop engine.dispose so module-level AsyncEngine pool
connections are not reused across asyncio.run ticks (loop-affinity).
"""

from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, MagicMock, patch

from runtime.agent_runtime import tasks as tasks_mod
from runtime.agent_runtime.tasks import (
    ACTIVE_TENANT_IDS_SQL,
    _run_async,
    agent_dispatch_all,
)


class TestRunAsync:
    def test_run_async_uses_asyncio_run(self):
        """_run_async must bridge via asyncio.run (no event-loop getter call)."""
        source = inspect.getsource(_run_async)
        assert "asyncio.run" in source
        assert "asyncio.get_event_loop" not in source
        assert ".get_event_loop(" not in source

        async def _ok():
            return {"status": "ok"}

        assert _run_async(_ok()) == {"status": "ok"}

    def test_run_async_executes_coro(self):
        async def _ok():
            return {"tenants_processed": 1}

        assert _run_async(_ok()) == {"tenants_processed": 1}


class TestAgentDispatchAll:
    def test_uses_run_async_not_get_event_loop(self):
        """Sync Celery wrapper must use _run_async / asyncio.run."""
        expected = {"tenants_processed": 2, "tasks_claimed": 3, "errors": []}
        with patch.object(tasks_mod, "_run_async", return_value=expected) as run_async:
            with patch.object(
                tasks_mod.asyncio,
                "get_event_loop",
                side_effect=AssertionError("must not use get_event_loop"),
            ):
                result = agent_dispatch_all.run()

        assert result == expected
        run_async.assert_called_once()

    def test_returns_stats_on_success(self):
        stats = {"tenants_processed": 1, "tasks_claimed": 5, "errors": []}
        with patch.object(tasks_mod, "_run_async", return_value=stats):
            result = agent_dispatch_all.run()

        assert result == stats
        assert "error" not in result

    def test_returns_error_dict_on_fatal(self):
        """Existing contract: fatal bridge errors become {\"error\": ...}, not re-raise."""
        with patch.object(
            tasks_mod,
            "_run_async",
            side_effect=RuntimeError(
                "There is no current event loop in thread 'MainThread'."
            ),
        ):
            result = agent_dispatch_all.run()

        assert result == {
            "error": "There is no current event loop in thread 'MainThread'."
        }

    def test_dispatch_disposes_engine_on_same_loop(self):
        """asyncio.run + module-level engine requires same-loop dispose."""
        mock_engine = MagicMock()
        mock_engine.dispose = AsyncMock()

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_factory = MagicMock(return_value=mock_session)

        with (
            patch("app.database.async_session", mock_factory),
            patch("app.database.engine", mock_engine),
        ):
            result = agent_dispatch_all.run()

        assert result == {
            "tenants_processed": 0,
            "tasks_claimed": 0,
            "errors": [],
        }
        mock_engine.dispose.assert_awaited()

    def test_module_does_not_use_get_event_loop(self):
        """Guard against regressions: tasks.py must not call get_event_loop()."""
        source = inspect.getsource(tasks_mod)
        assert "asyncio.get_event_loop" not in source
        assert ".get_event_loop(" not in source
        assert "run_until_complete" not in source
        assert "asyncio.run" in source
        assert "_run_async" in source
        assert "dispose()" in source


class TestActiveTenantFilter:
    def test_sql_uses_tenant_model_columns_not_status(self):
        """tenants.status never existed — align to is_active / deleted_at / provisioning_status."""
        sql = ACTIVE_TENANT_IDS_SQL
        sql_upper = sql.upper()
        assert "FROM TENANTS" in sql_upper
        assert "IS_ACTIVE" in sql_upper
        assert "DELETED_AT" in sql_upper
        assert "PROVISIONING_STATUS" in sql_upper
        assert "WHERE STATUS" not in sql_upper
        assert "TENANTS.STATUS" not in sql_upper
        assert "STATUS = 'ACTIVE'" not in sql.replace("provisioning_status = 'active'", "")

    def test_module_source_does_not_select_tenants_status(self):
        source = inspect.getsource(tasks_mod)
        assert "WHERE status = 'active'" not in source
        assert 'WHERE status = "active"' not in source
        assert "tenants.status" not in source
        assert "ACTIVE_TENANT_IDS_SQL" in source
        assert "is_active IS TRUE" in source

    def test_dispatch_executes_active_tenant_sql(self):
        mock_engine = MagicMock()
        mock_engine.dispose = AsyncMock()

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_factory = MagicMock(return_value=mock_session)

        with (
            patch("app.database.async_session", mock_factory),
            patch("app.database.engine", mock_engine),
        ):
            result = agent_dispatch_all.run()

        assert result["errors"] == []
        mock_session.execute.assert_awaited()
        executed = mock_session.execute.await_args.args[0]
        executed_sql = str(executed)
        assert "is_active" in executed_sql
        assert "WHERE status" not in executed_sql.upper().replace("PROVISIONING_STATUS", "")

    def test_dispatch_processes_loaded_tenants(self):
        mock_engine = MagicMock()
        mock_engine.dispose = AsyncMock()

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        row = MagicMock()
        row.id = "11111111-1111-1111-1111-111111111111"
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [row]
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_factory = MagicMock(return_value=mock_session)

        async def _dispatch(_tid):
            return {"claimed_fast": 2, "claimed_research": 1, "errors": []}

        with (
            patch("app.database.async_session", mock_factory),
            patch("app.database.engine", mock_engine),
            patch(
                "runtime.agent_runtime.dispatcher.dispatch_all",
                side_effect=_dispatch,
            ),
        ):
            result = agent_dispatch_all.run()

        assert result == {
            "tenants_processed": 1,
            "tasks_claimed": 3,
            "errors": [],
        }
        mock_engine.dispose.assert_awaited()
