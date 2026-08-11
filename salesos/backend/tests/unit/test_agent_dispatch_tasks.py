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
from runtime.agent_runtime.tasks import _run_async, agent_dispatch_all


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
