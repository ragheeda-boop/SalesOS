"""Unit tests for Celery asyncio.run + AsyncEngine same-loop dispose.

asyncio.run closes the loop after each Celery tick. Module-level /
process-lazy AsyncEngine pools are loop-bound; reusing them on the next
tick raises 'Future attached to a different loop'.
"""

from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.communication_hub.tasks import _run as hub_run
from app.tasks import _run_async as app_run_async
from domains.employee import tasks as employee_tasks
from domains.employee.tasks import _run_async as employee_run_async


class TestEmployeeRunAsyncDispose:
    def test_run_async_uses_asyncio_run(self):
        source = inspect.getsource(employee_run_async)
        assert "asyncio.run" in source
        assert "asyncio.get_event_loop" not in source
        assert "dispose" in source

        async def _ok():
            return {"status": "ok"}

        assert employee_run_async(_ok()) == {"status": "ok"}

    def test_disposes_lazy_engine_on_same_loop(self):
        mock_engine = MagicMock()
        mock_engine.dispose = AsyncMock()

        async def _ok():
            return {"status": "ok"}

        employee_tasks._engine = mock_engine
        try:
            result = employee_run_async(_ok())
        finally:
            employee_tasks._engine = None

        assert result == {"status": "ok"}
        mock_engine.dispose.assert_awaited()
        assert employee_tasks._engine is None

    def test_successive_ticks_create_fresh_engine(self):
        engines = [MagicMock(), MagicMock()]
        for engine in engines:
            engine.dispose = AsyncMock()
        mock_session = MagicMock()

        employee_tasks._engine = None
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
                    await employee_tasks._get_session()
                    return "ok"

                assert employee_run_async(tick()) == "ok"
                assert employee_run_async(tick()) == "ok"
        finally:
            employee_tasks._engine = None

        assert created.call_count == 2
        engines[0].dispose.assert_awaited()
        engines[1].dispose.assert_awaited()
        assert employee_tasks._engine is None


class TestAppTasksRunAsyncDispose:
    def test_run_async_source_disposes_engine(self):
        source = inspect.getsource(app_run_async)
        assert "asyncio.run" in source
        assert "asyncio.get_event_loop" not in source
        assert "dispose" in source

    def test_disposes_module_engine_on_same_loop(self):
        mock_engine = MagicMock()
        mock_engine.dispose = AsyncMock()

        async def _ok():
            return "ok"

        with patch("app.database.engine", mock_engine):
            assert app_run_async(_ok()) == "ok"

        mock_engine.dispose.assert_awaited()


class TestCommunicationHubRunDispose:
    def test_run_source_disposes_engine(self):
        source = inspect.getsource(hub_run)
        assert "asyncio.run" in source
        assert "asyncio.get_event_loop" not in source
        assert "dispose" in source

    def test_disposes_module_engine_on_same_loop(self):
        mock_engine = MagicMock()
        mock_engine.dispose = AsyncMock()

        async def _ok():
            return {"synced": 0}

        with patch("app.database.engine", mock_engine):
            assert hub_run(_ok()) == {"synced": 0}

        mock_engine.dispose.assert_awaited()
