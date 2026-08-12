"""IL-2A: Signal to AgentTask Trigger - unit tests.

Tests:
  - Signal to task kind mapping (all 12 signal types)
  - DecisionCategory to task kind mapping
  - DecisionType eligibility + task kind contract (IL-2A)
  - decision.created subscriber handler (on_decision_created_event)
  - Idempotency key generation
  - Priority mapping
  - Duplicate prevention via schedule_task
  - Tenant isolation
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from runtime.agent_runtime.triggers import (
    SignalTaskMapper,
    trigger_tasks_from_decisions,
    trigger_tasks_from_signals,
    on_decision_created_event,
    DECISION_TYPE_TO_TASK_KIND,
    NON_TASK_GENERATING_DECISION_TYPES,
    SIGNAL_TO_TASK_KIND,
    DEFAULT_TASK_KIND,
)
from runtime.agent_runtime.queue import schedule_task
from runtime.decision_runtime.models import DecisionType
from app.database import get_current_tenant_id_context


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
        session = AsyncMock()
        stats = asyncio.run(trigger_tasks_from_decisions(session, [], "T1"))
        assert stats["created"] == 0
        assert stats["skipped"] == 0
        assert stats["errors"] == 0

    def test_skips_decisions_without_entity_id(self, monkeypatch):
        session = AsyncMock()
        monkeypatch.setattr(
            "runtime.agent_runtime.queue.schedule_task",
            AsyncMock(return_value=MagicMock()),
        )
        stats = asyncio.run(trigger_tasks_from_decisions(
            session,
            [{"category": "opportunity", "entity_type": "company", "entity_id": "", "intensity": 0.8}],
            "T1",
        ))
        assert stats["skipped"] == 1
        assert stats["created"] == 0

    def test_creates_task_for_valid_decision(self, monkeypatch):
        session = AsyncMock()
        schedule = AsyncMock(return_value=MagicMock())
        monkeypatch.setattr("runtime.agent_runtime.queue.schedule_task", schedule)
        stats = asyncio.run(trigger_tasks_from_decisions(
            session,
            [{"category": "opportunity", "entity_type": "company", "entity_id": "C123", "intensity": 0.9, "title": "Test"}],
            "T1",
        ))
        assert stats["created"] == 1
        assert stats["errors"] == 0
        schedule.assert_awaited_once()

    def test_handles_multiple_decisions(self, monkeypatch):
        session = AsyncMock()
        schedule = AsyncMock(return_value=MagicMock())
        monkeypatch.setattr("runtime.agent_runtime.queue.schedule_task", schedule)
        decisions = [
            {"category": "revenue", "entity_type": "company", "entity_id": "C1", "intensity": 0.9, "title": "D1"},
            {"category": "risk", "entity_type": "company", "entity_id": "C2", "intensity": 0.7, "title": "D2"},
            {"category": "strategy", "entity_type": "company", "entity_id": "C3", "intensity": 0.5, "title": "D3"},
        ]
        stats = asyncio.run(trigger_tasks_from_decisions(session, decisions, "T1"))
        assert stats["created"] == 3
        assert schedule.await_count == 3


class TestTriggerTasksFromSignals:
    def test_empty_signals(self):
        session = AsyncMock()
        stats = asyncio.run(trigger_tasks_from_signals(session, [], "T1"))
        assert stats["created"] == 0

    def test_creates_task_for_funding_signal(self, monkeypatch):
        session = AsyncMock()
        schedule = AsyncMock(return_value=MagicMock())
        monkeypatch.setattr("runtime.agent_runtime.queue.schedule_task", schedule)
        stats = asyncio.run(trigger_tasks_from_signals(
            session,
            [{"signal_type": "funding", "company_id": "C1", "tenant_id": "T1", "intensity": 0.95, "title": "Funding Round"}],
            "T1",
        ))
        assert stats["created"] == 1
        schedule.assert_awaited_once()

    def test_different_signals_different_kinds(self, monkeypatch):
        session = AsyncMock()
        kinds = []

        async def capture_schedule(**kwargs):
            kinds.append(kwargs.get("kind"))
            return MagicMock()

        monkeypatch.setattr("runtime.agent_runtime.queue.schedule_task", capture_schedule)
        signals = [
            {"signal_type": "leadership", "company_id": "C1", "tenant_id": "T1", "intensity": 0.8, "title": "S1"},
            {"signal_type": "competitor", "company_id": "C2", "tenant_id": "T1", "intensity": 0.8, "title": "S2"},
            {"signal_type": "regulatory", "company_id": "C3", "tenant_id": "T1", "intensity": 0.8, "title": "S3"},
        ]
        asyncio.run(trigger_tasks_from_signals(session, signals, "T1"))
        assert kinds == ["executive_change", "assess_icp", "verify_license"]


class TestMapperIntegration:
    def test_full_pipeline_mapping(self):
        mapper = SignalTaskMapper()
        assert mapper.task_kind_for_signal("funding") == "research_company"
        key = mapper.build_idempotency_key("tenant-1", "company", "comp-456", "research_company")
        assert key == "tenant-1:decision:company:comp-456:research_company"
        assert mapper.priority_for_signal_intensity(0.95) == 10


# ?? IL-2A: DecisionType eligibility + mapping contract ???????????????????????


class TestDecisionTypeEligibilityContract:
    def test_contract_covers_all_11_decision_types_exactly_once(self):
        all_types = {t.value for t in DecisionType}
        assert len(all_types) == 11
        actionable = set(DECISION_TYPE_TO_TASK_KIND)
        non_generating = set(NON_TASK_GENERATING_DECISION_TYPES)
        assert actionable == all_types - non_generating
        assert len(actionable) == 7
        assert len(non_generating) == 4

    def test_all_actionable_types_are_eligible_and_map_to_research(self):
        for dt in DECISION_TYPE_TO_TASK_KIND:
            assert SignalTaskMapper.should_create_agent_task(dt) is True
            assert SignalTaskMapper.task_kind_for_decision_type(dt) == "research_company"

    def test_non_generating_types_are_ineligible(self):
        for dt in NON_TASK_GENERATING_DECISION_TYPES:
            assert SignalTaskMapper.should_create_agent_task(dt) is False
            assert SignalTaskMapper.task_kind_for_decision_type(dt) is None

    def test_unknown_type_is_fail_closed(self):
        assert SignalTaskMapper.should_create_agent_task("unknown_type") is False
        assert SignalTaskMapper.task_kind_for_decision_type("unknown_type") is None
        assert SignalTaskMapper.should_create_agent_task("") is False
        assert SignalTaskMapper.task_kind_for_decision_type("") is None
        assert SignalTaskMapper.should_create_agent_task(None) is False
        assert SignalTaskMapper.task_kind_for_decision_type(None) is None

    def test_case_insensitive_eligibility(self):
        assert SignalTaskMapper.should_create_agent_task("RECOMMEND_DEMO") is True
        assert SignalTaskMapper.task_kind_for_decision_type("Recommend_Demo") == "research_company"


class _FakeEvent:
    def __init__(
        self,
        event_type="decision.created",
        tenant_id="T1",
        decision_id="D1",
        company_id="C1",
        decision_type="recommend_demo",
    ):
        self.event_type = event_type
        self.tenant_id = tenant_id
        self.data = {
            "decision_id": decision_id,
            "company_id": company_id,
            "decision_type": decision_type,
        }


class _FakeSession:
    def __init__(self):
        self.execute = AsyncMock(return_value=AsyncMock())
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
        self.close = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        # Mirror AsyncSession: rollback open transaction on error, then close.
        if exc_type is not None:
            await self.rollback()
        await self.close()
        return False


class _FakeSessionFactory:
    def __init__(self, session=None):
        self.session = session or _FakeSession()
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.session


class _FakeDecisionEngine:
    def __init__(self, decision=None):
        self.decision = decision
        self.lookup_calls = []

    def get_decision(self, decision_id, tenant_id):
        self.lookup_calls.append((decision_id, tenant_id))
        return self.decision


class TestOnDecisionCreatedEvent:
    def test_ignores_non_decision_created_event(self):
        event = _FakeEvent(event_type="decision.accepted")
        sf = _FakeSessionFactory()
        result = asyncio.run(on_decision_created_event(sf, event, _FakeDecisionEngine()))
        assert result["reason"] == "not_decision_created"
        assert sf.calls == 0

    def test_skips_event_without_decision_id(self):
        event = _FakeEvent(decision_id="")
        sf = _FakeSessionFactory()
        result = asyncio.run(on_decision_created_event(sf, event, _FakeDecisionEngine()))
        assert result["reason"] == "no_decision_id"
        assert sf.calls == 0

    def test_skips_when_decision_engine_missing(self):
        sf = _FakeSessionFactory()
        result = asyncio.run(on_decision_created_event(sf, _FakeEvent(), None))
        assert result["reason"] == "no_decision_engine"
        assert sf.calls == 0

    def test_skips_when_canonical_decision_not_found(self):
        engine = _FakeDecisionEngine(decision=None)
        session = _FakeSession()
        sf = _FakeSessionFactory(session)
        result = asyncio.run(on_decision_created_event(sf, _FakeEvent(), engine))
        assert result["reason"] == "decision_not_found"
        assert engine.lookup_calls == [("D1", "T1")]
        session.commit.assert_not_awaited()
        session.close.assert_awaited_once()

    def test_skips_non_task_generating_decision_type_from_canonical(self):
        engine = _FakeDecisionEngine(
            decision={
                "decision_type": "alert",
                "company_id": "C1",
                "confidence": 0.9,
                "priority": 80,
                "reasoning": "Alert only",
            }
        )
        session = _FakeSession()
        sf = _FakeSessionFactory(session)
        result = asyncio.run(on_decision_created_event(sf, _FakeEvent(), engine))
        assert result["reason"] == "not_task_generating"
        assert result["decision_type"] == "alert"
        session.commit.assert_not_awaited()
        session.close.assert_awaited_once()

    def test_skips_when_canonical_decision_has_no_company_id(self):
        engine = _FakeDecisionEngine(
            decision={
                "decision_type": "recommend_demo",
                "company_id": "",
                "confidence": 0.9,
                "priority": 80,
                "reasoning": "x",
            }
        )
        session = _FakeSession()
        sf = _FakeSessionFactory(session)
        result = asyncio.run(on_decision_created_event(sf, _FakeEvent(), engine))
        assert result["reason"] == "no_company_id"
        session.commit.assert_not_awaited()

    def test_eligibility_uses_canonical_type_not_event_payload(self, monkeypatch):
        """Event may say recommend_demo; canonical alert must win (no task)."""
        event = _FakeEvent(decision_type="recommend_demo")
        engine = _FakeDecisionEngine(
            decision={
                "decision_type": "alert",
                "company_id": "C1",
                "confidence": 0.5,
                "priority": 0,
                "reasoning": "noise",
            }
        )
        called = {"trigger": False}

        async def fake_trigger(session, decisions, tenant_id):
            called["trigger"] = True
            return {"created": 1, "skipped": 0, "errors": 0}

        monkeypatch.setattr(
            "runtime.agent_runtime.triggers.trigger_tasks_from_decisions", fake_trigger
        )
        result = asyncio.run(on_decision_created_event(_FakeSessionFactory(), event, engine))
        assert result["reason"] == "not_task_generating"
        assert called["trigger"] is False

    def test_trigger_receives_correct_payload_and_commits_once(self, monkeypatch):
        captured = {}
        guc_calls = []

        async def fake_trigger(session, decisions, tenant_id):
            captured["decisions"] = decisions
            captured["tenant_id"] = tenant_id
            return {"created": 1, "skipped": 0, "errors": 0}

        async def fake_guc(session, tenant_id=None):
            guc_calls.append(tenant_id)

        monkeypatch.setattr(
            "runtime.agent_runtime.triggers.trigger_tasks_from_decisions", fake_trigger
        )
        monkeypatch.setattr("app.database.apply_tenant_guc", fake_guc)

        engine = _FakeDecisionEngine(
            decision={
                "decision_type": "recommend_demo",
                "company_id": "C1",
                "confidence": 0.9,
                "priority": 95,
                "reasoning": "High intent + funding",
            }
        )
        session = _FakeSession()
        sf = _FakeSessionFactory(session)

        # Event payload deliberately wrong ù canonical must win
        event = _FakeEvent(decision_type="alert", company_id="WRONG")
        result = asyncio.run(on_decision_created_event(sf, event, engine))

        assert result["task_kind"] == "research_company"
        assert result["decision_type"] == "recommend_demo"
        assert result["reason"] == "created"
        d = captured["decisions"][0]
        assert d["task_kind"] == "research_company"
        assert d["entity_type"] == "company"
        assert d["entity_id"] == "C1"
        assert d["confidence"] == 0.9
        assert d["intensity"] == 0.95
        assert d["title"] == "High intent + funding"
        assert captured["tenant_id"] == "T1"
        assert guc_calls == ["T1"]
        session.commit.assert_awaited_once()
        session.close.assert_awaited_once()

    def test_looks_up_canonical_decision_before_trigger(self, monkeypatch):
        async def fake_trigger(session, decisions, tenant_id):
            return {"created": 1, "skipped": 0, "errors": 0}

        monkeypatch.setattr(
            "runtime.agent_runtime.triggers.trigger_tasks_from_decisions", fake_trigger
        )

        engine = _FakeDecisionEngine(
            decision={
                "decision_type": "recommend_call",
                "company_id": "C1",
                "confidence": 0.8,
                "priority": 50,
                "reasoning": "r",
            }
        )
        asyncio.run(on_decision_created_event(_FakeSessionFactory(), _FakeEvent(), engine))
        assert engine.lookup_calls == [("D1", "T1")]

    def test_tenant_context_is_applied_and_reset(self, monkeypatch):
        async def fake_trigger(session, decisions, tenant_id):
            assert get_current_tenant_id_context() == "T1"
            return {"created": 1, "skipped": 0, "errors": 0}

        monkeypatch.setattr(
            "runtime.agent_runtime.triggers.trigger_tasks_from_decisions", fake_trigger
        )

        engine = _FakeDecisionEngine(
            decision={
                "decision_type": "recommend_demo",
                "company_id": "C1",
                "confidence": 0.5,
                "priority": 0,
                "reasoning": "x",
            }
        )
        baseline = get_current_tenant_id_context()
        asyncio.run(on_decision_created_event(_FakeSessionFactory(), _FakeEvent(), engine))
        assert get_current_tenant_id_context() == baseline

    def test_exception_rolls_back_and_resets_context(self, monkeypatch):
        async def fake_trigger(session, decisions, tenant_id):
            raise RuntimeError("db boom")

        monkeypatch.setattr(
            "runtime.agent_runtime.triggers.trigger_tasks_from_decisions", fake_trigger
        )

        engine = _FakeDecisionEngine(
            decision={
                "decision_type": "recommend_demo",
                "company_id": "C1",
                "confidence": 0.5,
                "priority": 0,
                "reasoning": "x",
            }
        )
        baseline = get_current_tenant_id_context()
        session = _FakeSession()
        sf = _FakeSessionFactory(session)

        with pytest.raises(RuntimeError):
            asyncio.run(on_decision_created_event(sf, _FakeEvent(), engine))

        session.rollback.assert_awaited_once()
        session.close.assert_awaited_once()
        assert get_current_tenant_id_context() == baseline

    def test_idempotency_delegated_to_schedule_task(self, monkeypatch):
        """Current contract: schedule_task dedupes unfinished (tenant, kind, entity).

        Subscriber may invoke trigger twice; duplicate prevention is in queue.
        """
        calls = []

        async def fake_trigger(session, decisions, tenant_id):
            calls.append(decisions)
            return {"created": 1, "skipped": 0, "errors": 0}

        monkeypatch.setattr(
            "runtime.agent_runtime.triggers.trigger_tasks_from_decisions", fake_trigger
        )

        engine = _FakeDecisionEngine(
            decision={
                "decision_type": "recommend_demo",
                "company_id": "C1",
                "confidence": 0.5,
                "priority": 0,
                "reasoning": "x",
            }
        )
        asyncio.run(on_decision_created_event(_FakeSessionFactory(), _FakeEvent(), engine))
        asyncio.run(on_decision_created_event(_FakeSessionFactory(), _FakeEvent(), engine))
        assert len(calls) == 2
        assert calls[0] == calls[1]
