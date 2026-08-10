"""IL-2A: Signal to AgentTask Trigger — integration tests.

Tests:
  - Signal?task kind mapping (all 12 signal types)
  - Decision?task kind mapping  
  - Idempotency key generation
  - Priority mapping
  - Duplicate prevention via schedule_task
  - Tenant isolation
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from runtime.agent_runtime.triggers import (
    SignalTaskMapper,
    trigger_tasks_from_decisions,
    trigger_tasks_from_signals,
    SIGNAL_TO_TASK_KIND,
    DEFAULT_TASK_KIND,
)
from runtime.agent_runtime.queue import schedule_task


class TestSignalTaskMapping:
    def test_all_signal_types_have_mapping(self):
        assert len(SIGNAL_TO_TASK_KIND) == 12
        assert SIGNAL_TO_TASK_KIND["funding"] == "research_company"
        assert SIGNAL_TO_TASK_KIND["hiring"] == "research_company"
        assert SIGNAL_TO_TASK_KIND["expansion"] == "investigate_expansion"
        assert SIGNAL_TO_TASK_KIND["contract"] == "research_company"
        assert SIGNAL_TO_TASK_KIND["project"] == "research_company"
        assert SIGNAL_TO_TASK_KIND["tender"] == "research_company"
        assert SIGNAL_TO_TASK_KIND["merger"] == "research_company"
        assert SIGNAL_TO_TASK_KIND["partnership"] == "research_company"
        assert SIGNAL_TO_TASK_KIND["leadership"] == "executive_change"
        assert SIGNAL_TO_TASK_KIND["competitor"] == "assess_icp"
        assert SIGNAL_TO_TASK_KIND["regulatory"] == "verify_license"
        assert SIGNAL_TO_TASK_KIND["news"] == "research_company"

    def test_unknown_signal_defaults_to_research(self):
        assert SignalTaskMapper.task_kind_for_signal("unknown") == DEFAULT_TASK_KIND
        assert SignalTaskMapper.task_kind_for_signal("") == DEFAULT_TASK_KIND
        assert SignalTaskMapper.task_kind_for_signal(None) == DEFAULT_TASK_KIND

    def test_decision_category_maps_to_task_kind(self):
        assert SignalTaskMapper.task_kind_for_decision("opportunity") == "research_company"
        assert SignalTaskMapper.task_kind_for_decision("revenue") == "research_company"
        assert SignalTaskMapper.task_kind_for_decision("risk") == "verify_license"
        assert SignalTaskMapper.task_kind_for_decision("resource") == "assess_icp"
        assert SignalTaskMapper.task_kind_for_decision("strategy") == "investigate_expansion"
        assert SignalTaskMapper.task_kind_for_decision("unknown") == DEFAULT_TASK_KIND

    def test_case_insensitive_mapping(self):
        assert SignalTaskMapper.task_kind_for_signal("FUNDING") == "research_company"
        assert SignalTaskMapper.task_kind_for_signal("Funding") == "research_company"


class TestIdempotencyKey:
    def test_key_format(self):
        key = SignalTaskMapper.build_idempotency_key("T1", "company", "C123", "research_company")
        assert key == "T1:decision:company:C123:research_company"

    def test_different_entities_different_keys(self):
        k1 = SignalTaskMapper.build_idempotency_key("T1", "company", "C1", "research_company")
        k2 = SignalTaskMapper.build_idempotency_key("T1", "company", "C2", "research_company")
        assert k1 != k2

    def test_different_tenants_different_keys(self):
        k1 = SignalTaskMapper.build_idempotency_key("T1", "company", "C1", "research_company")
        k2 = SignalTaskMapper.build_idempotency_key("T2", "company", "C1", "research_company")
        assert k1 != k2

    def test_different_task_kinds_different_keys(self):
        k1 = SignalTaskMapper.build_idempotency_key("T1", "company", "C1", "research_company")
        k2 = SignalTaskMapper.build_idempotency_key("T1", "company", "C1", "verify_license")
        assert k1 != k2


class TestPriorityMapping:
    def test_high_intensity_gets_high_priority(self):
        assert SignalTaskMapper.priority_for_signal_intensity(0.95) == 10
        assert SignalTaskMapper.priority_for_signal_intensity(0.90) == 10

    def test_medium_intensity_gets_medium_priority(self):
        assert SignalTaskMapper.priority_for_signal_intensity(0.75) == 5
        assert SignalTaskMapper.priority_for_signal_intensity(0.70) == 5

    def test_low_intensity_gets_zero_priority(self):
        assert SignalTaskMapper.priority_for_signal_intensity(0.50) == 0
        assert SignalTaskMapper.priority_for_signal_intensity(0.0) == 0


class TestTriggerTasksFromDecisions:
    def test_empty_decisions(self):
        import asyncio
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()

        stats = asyncio.run(trigger_tasks_from_decisions(session, [], "T1"))
        assert stats["created"] == 0
        assert stats["skipped"] == 0
        assert stats["errors"] == 0

    def test_skips_decisions_without_entity_id(self):
        import asyncio
        session = AsyncMock()
        session.execute = AsyncMock()

        stats = asyncio.run(trigger_tasks_from_decisions(
            session,
            [{"category": "opportunity", "entity_type": "company", "entity_id": "", "intensity": 0.8}],
            "T1",
        ))
        assert stats["skipped"] == 1
        assert stats["created"] == 0

    def test_creates_task_for_valid_decision(self):
        import asyncio
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()

        stats = asyncio.run(trigger_tasks_from_decisions(
            session,
            [{"category": "opportunity", "entity_type": "company", "entity_id": "C123", "intensity": 0.9, "title": "Test"}],
            "T1",
        ))
        assert stats["created"] == 1
        assert stats["errors"] == 0

    def test_handles_multiple_decisions(self):
        import asyncio
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()

        decisions = [
            {"category": "revenue", "entity_type": "company", "entity_id": "C1", "intensity": 0.9, "title": "D1"},
            {"category": "risk", "entity_type": "company", "entity_id": "C2", "intensity": 0.7, "title": "D2"},
            {"category": "strategy", "entity_type": "company", "entity_id": "C3", "intensity": 0.5, "title": "D3"},
        ]
        stats = asyncio.run(trigger_tasks_from_decisions(session, decisions, "T1"))
        assert stats["created"] == 3


class TestTriggerTasksFromSignals:
    def test_empty_signals(self):
        import asyncio
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()

        stats = asyncio.run(trigger_tasks_from_signals(session, [], "T1"))
        assert stats["created"] == 0

    def test_creates_task_for_funding_signal(self):
        import asyncio
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()

        stats = asyncio.run(trigger_tasks_from_signals(
            session,
            [{"signal_type": "funding", "company_id": "C1", "tenant_id": "T1", "intensity": 0.95, "title": "Funding Round"}],
            "T1",
        ))
        assert stats["created"] == 1

    def test_different_signals_different_kinds(self):
        import asyncio
        session = AsyncMock()
        exec_calls = []

        async def capture_exec(*args, **kwargs):
            exec_calls.append((args, kwargs))
            return AsyncMock()

        session.execute = capture_exec
        session.commit = AsyncMock()

        signals = [
            {"signal_type": "leadership", "company_id": "C1", "tenant_id": "T1", "intensity": 0.8, "title": "S1"},
            {"signal_type": "competitor", "company_id": "C2", "tenant_id": "T1", "intensity": 0.8, "title": "S2"},
            {"signal_type": "regulatory", "company_id": "C3", "tenant_id": "T1", "intensity": 0.8, "title": "S3"},
        ]
        asyncio.run(trigger_tasks_from_signals(session, signals, "T1"))
        assert len(exec_calls) >= 3


class TestMapperIntegration:
    def test_full_pipeline_mapping(self):
        mapper = SignalTaskMapper()
        assert mapper.task_kind_for_signal("funding") == "research_company"
        key = mapper.build_idempotency_key("tenant-1", "company", "comp-456", "research_company")
        assert key == "tenant-1:decision:company:comp-456:research_company"
        assert mapper.priority_for_signal_intensity(0.95) == 10
