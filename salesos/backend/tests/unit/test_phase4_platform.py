"""Phase 4 Platform-grade Engineering tests.

Tests for:
- P4-1: EventRuntime persistent DLQ (Postgres-backed)
- P4-2: Capability registry validation pytest wrapper
- P4-4: DRY health check helper
- P4-5: EXHAUSTED task alerting
- P4-6: Backup Dockerfile path fix
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# P4-1: Persistent DLQ
# ---------------------------------------------------------------------------

class TestPersistentDeadLetterQueue:
    def test_import(self):
        from runtime.event_runtime.persistent_dlq import PersistentDeadLetterQueue
        assert PersistentDeadLetterQueue is not None

    def test_event_runtime_inits_persistent_dlq_when_session_factory(self):
        from runtime.event_runtime import EventRuntime
        mock_factory = MagicMock()
        runtime = EventRuntime(session_factory=mock_factory)
        assert runtime._persistent_dlq is not None

    def test_event_runtime_no_persistent_dlq_when_no_factory(self):
        from runtime.event_runtime import EventRuntime
        runtime = EventRuntime(session_factory=None)
        assert runtime._persistent_dlq is None

    def test_persistent_dlq_add_calls_session(self):
        from runtime.event_runtime.persistent_dlq import PersistentDeadLetterQueue
        mock_session = AsyncMock()
        mock_factory = MagicMock()
        mock_factory.return_value = AsyncMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        dlq = PersistentDeadLetterQueue(mock_factory)

        async def _run():
            await dlq.add(
                entry_id="test-id",
                tenant_id="t-123",
                event_id="e-456",
                event_type="test.event",
                subscriber_name="test_sub",
                error="test error",
                attempts=3,
            )

        asyncio.get_event_loop().run_until_complete(_run())
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_persistent_dlq_list_all(self):
        from runtime.event_runtime.persistent_dlq import PersistentDeadLetterQueue
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result
        mock_factory = MagicMock()
        mock_factory.return_value = AsyncMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        dlq = PersistentDeadLetterQueue(mock_factory)

        async def _run():
            return await dlq.list_all("t-123")

        result = asyncio.get_event_loop().run_until_complete(_run())
        assert result == []

    def test_persistent_dlq_count(self):
        from runtime.event_runtime.persistent_dlq import PersistentDeadLetterQueue
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (5,)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_factory = MagicMock()
        mock_factory.return_value = AsyncMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        dlq = PersistentDeadLetterQueue(mock_factory)

        async def _run():
            return await dlq.count("t-123")

        count = asyncio.get_event_loop().run_until_complete(_run())
        assert count == 5

    def test_persistent_dlq_handles_persist_failure_gracefully(self):
        from runtime.event_runtime.persistent_dlq import PersistentDeadLetterQueue
        mock_factory = MagicMock()
        mock_factory.return_value = AsyncMock()
        mock_factory.return_value.__aenter__ = AsyncMock(side_effect=Exception("DB down"))
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        dlq = PersistentDeadLetterQueue(mock_factory)

        async def _run():
            await dlq.add(
                entry_id="test-id",
                tenant_id="t-123",
                event_id="e-456",
                event_type="test.event",
                subscriber_name="test_sub",
                error="test error",
                attempts=3,
            )

        # Should not raise
        asyncio.get_event_loop().run_until_complete(_run())


# ---------------------------------------------------------------------------
# P4-2: Capability Registry Validation
# ---------------------------------------------------------------------------

class TestCapabilityRegistryValidation:
    def test_import(self):
        from tests.unit.test_capability_registry_validation import TestCapabilityRegistryValidation
        assert TestCapabilityRegistryValidation is not None

    def test_validation_script_exists(self):
        from pathlib import Path
        script = Path(__file__).resolve().parents[2] / "scripts" / "validate_capability_registries.py"
        assert script.exists(), f"Validation script not found at {script}"


# ---------------------------------------------------------------------------
# P4-4: DRY Health Check Helper
# ---------------------------------------------------------------------------

class TestDRYHealthCheck:
    def test_check_kafka_status_in_memory(self):
        from app.main import _check_kafka_status
        mock_state = MagicMock()
        mock_state.event_runtime = MagicMock()
        result = _check_kafka_status(mock_state)
        assert result == "in_memory"

    def test_check_kafka_status_not_configured(self):
        from app.main import _check_kafka_status
        mock_state = MagicMock()
        mock_state.event_runtime = None
        result = _check_kafka_status(mock_state)
        assert result == "not_configured"

    def test_check_kafka_status_kafka_connected(self):
        from app.main import _check_kafka_status
        from sdk.events.kafka_bus import KafkaEventBus
        mock_state = MagicMock()
        mock_kafka = MagicMock(spec=KafkaEventBus)
        mock_kafka.is_kafka_available = True
        mock_state.event_runtime = mock_kafka
        result = _check_kafka_status(mock_state)
        assert result == "connected"

    def test_check_kafka_status_kafka_fallback(self):
        from app.main import _check_kafka_status
        from sdk.events.kafka_bus import KafkaEventBus
        mock_state = MagicMock()
        mock_kafka = MagicMock(spec=KafkaEventBus)
        mock_kafka.is_kafka_available = False
        mock_state.event_runtime = mock_kafka
        result = _check_kafka_status(mock_state)
        assert result == "fallback_in_memory"


# ---------------------------------------------------------------------------
# P4-5: EXHAUSTED Task Alerting
# ---------------------------------------------------------------------------

class TestExhaustedAlerting:
    def test_retire_exhausted_logs_warnings(self):
        from runtime.agent_runtime.queue import retire_exhausted
        from unittest.mock import patch
        mock_session = AsyncMock()
        mock_row = MagicMock()
        mock_row.id = "task-1"
        mock_row.kind = "research_company"
        mock_row.entity_type = "company"
        mock_row.entity_id = "comp-1"
        mock_row.attempts = 3
        mock_row.max_attempts = 3
        mock_row.outcome = "timeout after 3 retries"
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute = AsyncMock(return_value=mock_result)

        async def _run():
            return await retire_exhausted(mock_session, "t-123")

        with patch("runtime.agent_runtime.queue.logger") as mock_logger:
            count = asyncio.get_event_loop().run_until_complete(_run())
            assert count == 1
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert call_args[0][0] == "agent_task_exhausted"
            extra = call_args[1]["extra"]
            assert extra["task_id"] == "task-1"
            assert extra["kind"] == "research_company"

    def test_retire_exhausted_returns_zero_when_no_exhausted(self):
        from runtime.agent_runtime.queue import retire_exhausted
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        async def _run():
            return await retire_exhausted(mock_session, "t-123")

        count = asyncio.get_event_loop().run_until_complete(_run())
        assert count == 0


# ---------------------------------------------------------------------------
# P4-6: Backup Dockerfile
# ---------------------------------------------------------------------------

class TestBackupDockerfile:
    def test_dockerfile_references_correct_paths(self):
        from pathlib import Path
        dockerfile = Path(__file__).resolve().parents[2] / ".." / ".." / "infra" / "docker" / "backup" / "Dockerfile"
        if not dockerfile.exists():
            dockerfile = Path(__file__).resolve().parents[2].parent.parent / "infra" / "docker" / "backup" / "Dockerfile"
        if not dockerfile.exists():
            pytest.skip("Backup Dockerfile not found at any expected path")
        content = dockerfile.read_text()
        assert "infra/scripts/backup-db.sh" in content
        assert "infra/scripts/restore-db.sh" in content
        assert "COPY scripts/" not in content


# ---------------------------------------------------------------------------
# P4-1: Migration file exists
# ---------------------------------------------------------------------------

class TestDLQMigration:
    def test_migration_file_exists(self):
        from pathlib import Path
        migration = Path(__file__).resolve().parents[2] / "app" / "alembic" / "versions" / "g1h2i3j4k5l6_phase4_dlq_persistence.py"
        assert migration.exists(), f"DLQ migration not found at {migration}"

    def test_migration_has_correct_revision_chain(self):
        from pathlib import Path
        migration = Path(__file__).resolve().parents[2] / "app" / "alembic" / "versions" / "g1h2i3j4k5l6_phase4_dlq_persistence.py"
        if not migration.exists():
            pytest.skip("Migration not found")
        content = migration.read_text()
        assert 'revision = "g1h2i3j4k5l6"' in content
        assert 'down_revision = "f6a7b8c9d0e1"' in content
        assert "event_dead_letters" in content
        assert "ENABLE ROW LEVEL SECURITY" in content
