"""Tests for AI governance — cost tracker, circuit breaker, cache, metrics."""

import pytest
import time
from datetime import datetime, timezone, timedelta

from domains.employee.ai_governance import (
    AICostTracker, AICircuitBreaker, AIResponseCache, AIMetrics,
    PROMPT_REGISTRY, PROMPT_VERSION, MODEL_PRICING,
)


class TestAICostTracker:
    def test_initial_usage_zero(self):
        tracker = AICostTracker()
        assert tracker.daily_usage == 0.0
        assert tracker.monthly_usage == 0.0

    def test_records_cost_correctly(self):
        tracker = AICostTracker()
        tracker.record_usage("gpt-4o-mini", 1000, 500)
        assert tracker.daily_usage > 0

    def test_within_budget_allows_calls(self):
        tracker = AICostTracker(daily_budget_usd=100)
        assert tracker.can_call() is True

    def test_exceeding_daily_budget_blocks(self):
        tracker = AICostTracker(daily_budget_usd=0.01)
        tracker.record_usage("gpt-4o", 100000, 50000)
        assert tracker.can_call() is False

    def test_monthly_remaining_decreases(self):
        tracker = AICostTracker(monthly_budget_usd=10)
        tracker.record_usage("gpt-4o-mini", 10000, 5000)
        assert tracker.monthly_remaining < 10.0


class TestAICircuitBreaker:
    def test_initial_state_closed(self):
        cb = AICircuitBreaker()
        assert cb.allow_request() is True

    def test_opens_after_max_failures(self):
        cb = AICircuitBreaker(max_failures=3)
        assert cb.allow_request() is True
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open is True
        assert cb.allow_request() is False

    def test_resets_after_timeout(self):
        cb = AICircuitBreaker(max_failures=2, reset_timeout_seconds=0)
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open is True
        time.sleep(0.1)
        assert cb.allow_request() is True

    def test_success_resets_state(self):
        cb = AICircuitBreaker(max_failures=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.allow_request() is True


class TestAIResponseCache:
    def test_cache_miss(self):
        cache = AIResponseCache()
        assert cache.get("meeting_summary", {"title": "Q3"}) is None

    def test_cache_hit(self):
        cache = AIResponseCache()
        params = {"title": "Q3 Review"}
        result = {"summary": "Discussed targets"}
        cache.set("meeting_summary", params, result)
        assert cache.get("meeting_summary", params) == result

    def test_cache_eviction_on_max_size(self):
        cache = AIResponseCache(max_size=3)
        for i in range(5):
            cache.set("test", {"id": i}, {"result": i})
        assert cache.size <= 3

    def test_cache_clear(self):
        cache = AIResponseCache()
        cache.set("test", {"a": 1}, {"b": 2})
        cache.clear()
        assert cache.size == 0


class TestAIMetrics:
    def test_initial_metrics_zero(self):
        m = AIMetrics()
        assert m.total_calls == 0
        assert m.success_rate == 0.0

    def test_records_success_and_failure(self):
        m = AIMetrics()
        m.record_call("gpt-4o-mini", 100, 50, 200, True)
        m.record_call("gpt-4o-mini", 100, 50, 300, False)
        assert m.total_calls == 2
        assert m.success_rate == 50.0

    def test_tracks_cost(self):
        m = AIMetrics()
        m.record_call("gpt-4o-mini", 1000, 500, 100, True)
        assert m.total_cost_usd > 0

    def test_snapshot_has_all_fields(self):
        m = AIMetrics()
        m.record_call("gpt-4o-mini", 500, 200, 150, True)
        snap = m.snapshot()
        for field in ["total_calls", "successful", "failed", "success_rate",
                       "cached_hits", "cache_hit_rate", "total_tokens_in",
                       "total_tokens_out", "total_cost_usd", "avg_latency_ms"]:
            assert field in snap


class TestPromptRegistry:
    def test_all_prompts_have_version(self):
        for name, prompt in PROMPT_REGISTRY.items():
            assert "version" in prompt, f"{name} missing version"
            assert "template" in prompt, f"{name} missing template"
            assert "max_tokens" in prompt, f"{name} missing max_tokens"
            assert "model" in prompt, f"{name} missing model"

    def test_prompt_registry_version_defined(self):
        assert PROMPT_VERSION == "1.0.0"

    def test_five_prompts_registered(self):
        assert len(PROMPT_REGISTRY) >= 5


class TestModelPricing:
    def test_all_registered_models_have_pricing(self):
        models_used = {p["model"] for p in PROMPT_REGISTRY.values()}
        for m in models_used:
            assert m in MODEL_PRICING, f"Model {m} not in MODEL_PRICING"

    def test_pricing_has_input_output(self):
        for model, pricing in MODEL_PRICING.items():
            assert "input" in pricing
            assert "output" in pricing
            assert pricing["input"] > 0
            assert pricing["output"] > 0
