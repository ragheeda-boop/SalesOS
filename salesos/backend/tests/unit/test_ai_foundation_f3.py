"""AI Foundation F3 -- Observability tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from intelligence.providers.observability import (
    AIObservability,
    ai_observability,
    format_extra,
    log_context,
)


class TestFormatExtra:
    def test_returns_dict_with_values(self):
        result = format_extra(event="test", count=1)
        assert result == {"event": "test", "count": 1}

    def test_filters_none_values(self):
        result = format_extra(event="test", data=None, extra=None)
        assert result == {"event": "test"}
        assert "data" not in result
        assert "extra" not in result

    def test_empty_kwargs(self):
        result = format_extra()
        assert result == {}


class TestLogContext:
    def test_returns_logger(self):
        logger = log_context("test.module")
        assert logger.name == "test.module"


class TestAIObservabilityCalls:
    def test_record_llm_call_updates_counters(self):
        obs = AIObservability()
        obs.record_llm_call("openai", "gpt-4o", "chat", "success", 100.0)
        obs.record_llm_call("openai", "gpt-4o", "chat", "success", 200.0)
        snap = obs.snapshot()
        assert ("openai", "gpt-4o", "chat", "success") in snap["calls"]

    def test_record_tokens_accumulates(self):
        obs = AIObservability()
        obs.record_tokens("openai", "gpt-4o", 100, 50)
        obs.record_tokens("openai", "gpt-4o", 50, 25)
        snap = obs.snapshot()
        assert snap["tokens"][("openai", "gpt-4o", "prompt")] == 150
        assert snap["tokens"][("openai", "gpt-4o", "completion")] == 75

    def test_record_cost_accumulates(self):
        obs = AIObservability()
        obs.record_cost("openai", "gpt-4o", 0.001)
        obs.record_cost("openai", "gpt-4o", 0.002)
        snap = obs.snapshot()
        assert snap["cost"][("openai", "gpt-4o")] == pytest.approx(0.003)

    def test_record_policy_block(self):
        obs = AIObservability()
        obs.record_policy_block("harmful_input")
        obs.record_policy_block("harmful_input")
        obs.record_policy_block("model_tier")
        snap = obs.snapshot()
        assert snap["policy_blocks"]["harmful_input"] == 2
        assert snap["policy_blocks"]["model_tier"] == 1

    def test_record_budget_rejection(self):
        obs = AIObservability()
        obs.record_budget_rejection("t1")
        obs.record_budget_rejection("t1")
        obs.record_budget_rejection("t2")
        snap = obs.snapshot()
        assert snap["budget_rejections"]["t1"] == 2
        assert snap["budget_rejections"]["t2"] == 1

    def test_record_circuit_breaker(self):
        obs = AIObservability()
        obs.record_circuit_breaker("openai", "open")
        obs.record_circuit_breaker("openai", "half_open")
        obs.record_circuit_breaker("openai", "closed")
        snap = obs.snapshot()
        assert snap["cb_transitions"][("openai", "open")] == 1
        assert snap["cb_transitions"][("openai", "half_open")] == 1
        assert snap["cb_transitions"][("openai", "closed")] == 1


class TestAIObservabilitySnapshot:
    def test_empty_snapshot(self):
        obs = AIObservability()
        snap = obs.snapshot()
        assert snap["calls"] == {}
        assert snap["tokens"] == {}
        assert snap["cost"] == {}
        assert snap["policy_blocks"] == {}
        assert snap["budget_rejections"] == {}
        assert snap["cb_transitions"] == {}
        assert snap["uptime_seconds"] >= 0

    def test_methods_exist(self):
        obs = AIObservability()
        assert hasattr(obs, "record_llm_call")
        assert hasattr(obs, "record_tokens")
        assert hasattr(obs, "record_cost")
        assert hasattr(obs, "record_policy_block")
        assert hasattr(obs, "record_budget_rejection")
        assert hasattr(obs, "record_circuit_breaker")
        assert hasattr(obs, "snapshot")
        assert hasattr(obs, "generate")


class TestAIObservabilityGenerate:
    def test_generates_prometheus_format(self):
        obs = AIObservability()
        obs.record_llm_call("openai", "gpt-4o", "chat", "success", 100.0)
        output = obs.generate()
        assert "salesos_ai_calls_total" in output
        assert 'provider="openai"' in output
        assert 'model="gpt-4o"' in output
        assert 'operation="chat"' in output
        assert 'status="success"' in output

    def test_generates_histogram(self):
        obs = AIObservability()
        obs.record_llm_call("openai", "gpt-4o-mini", "chat", "success", 500.0)
        output = obs.generate()
        assert "salesos_ai_call_latency_seconds_bucket" in output
        assert "salesos_ai_call_latency_seconds_count" in output
        assert "salesos_ai_call_latency_seconds_sum" in output

    def test_generates_policy_blocks(self):
        obs = AIObservability()
        obs.record_policy_block("harmful_input")
        output = obs.generate()
        assert "salesos_ai_policy_blocks_total" in output
        assert 'reason="harmful_input"' in output

    def test_generates_budget_rejections(self):
        obs = AIObservability()
        obs.record_budget_rejection("t1")
        output = obs.generate()
        assert "salesos_ai_budget_rejections_total" in output
        assert 'tenant_id="t1"' in output

    def test_generates_circuit_breaker(self):
        obs = AIObservability()
        obs.record_circuit_breaker("openai", "open")
        output = obs.generate()
        assert "salesos_ai_circuit_breaker_transitions" in output
        assert 'provider="openai"' in output
        assert 'transition="open"' in output

    def test_generates_tokens(self):
        obs = AIObservability()
        obs.record_tokens("anthropic", "claude-3-5-sonnet", 200, 100)
        output = obs.generate()
        assert "salesos_ai_tokens_total" in output
        assert 'type="prompt"' in output
        assert 'type="completion"' in output

    def test_generates_cost(self):
        obs = AIObservability()
        obs.record_cost("openai", "gpt-4o", 0.005)
        output = obs.generate()
        assert "salesos_ai_cost_total" in output


class TestAIObservabilityThreadSafety:
    def test_concurrent_records(self):
        obs = AIObservability()
        import threading
        threads = []
        def record():
            for _ in range(100):
                obs.record_llm_call("openai", "gpt-4o", "chat", "success", 50.0)
                obs.record_tokens("openai", "gpt-4o", 10, 5)
                obs.record_cost("openai", "gpt-4o", 0.001)
        for _ in range(5):
            t = threading.Thread(target=record)
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        snap = obs.snapshot()
        total_calls = sum(snap["calls"].values())
        assert total_calls == 500


class TestGlobalSingleton:
    def test_ai_observability_exists(self):
        from intelligence.providers.observability import ai_observability
        assert isinstance(ai_observability, AIObservability)

    def test_global_state_persists(self):
        from intelligence.providers.observability import ai_observability as a
        a.record_llm_call("test", "test-model", "test-op", "success", 10.0)
        from intelligence.providers.observability import ai_observability as b
        snap = b.snapshot()
        assert ("test", "test-model", "test-op", "success") in snap["calls"]


class TestRequestIdPropagation:
    def test_chat_request_has_request_id(self):
        from intelligence.providers.base import ChatRequest
        req = ChatRequest(messages=[{"role": "user", "content": "hi"}], request_id="rid-123")
        assert req.request_id == "rid-123"

    def test_chat_request_request_id_defaults_none(self):
        from intelligence.providers.base import ChatRequest
        req = ChatRequest()
        assert req.request_id is None

    def test_embedding_request_has_request_id(self):
        from intelligence.providers.base import EmbeddingRequest
        req = EmbeddingRequest(text="hello", request_id="rid-456")
        assert req.request_id == "rid-456"
