"""Top-level intelligence CostTracker tests — estimate, track, budget, enforcement."""

import pytest
from intelligence.cost_tracker import CostTracker, BudgetEnforcement, CostEstimate


def test_estimate_cost_gpt4o_mini():
    tracker = CostTracker()
    cost = tracker.estimate_cost("gpt-4o-mini", 1000, 500)
    assert cost > 0
    assert cost < 1.0


def test_estimate_cost_gpt4o():
    tracker = CostTracker()
    cost = tracker.estimate_cost("gpt-4o", 2000, 1000)
    assert cost > 0


def test_estimate_cost_unknown_model():
    tracker = CostTracker()
    cost = tracker.estimate_cost("unknown-model", 1000, 500)
    assert cost > 0


def test_estimate_cost_zero_tokens():
    tracker = CostTracker()
    cost = tracker.estimate_cost("gpt-4o", 0, 0)
    assert cost == 0.0


def test_track_usage():
    tracker = CostTracker()
    usage = {"prompt_tokens": 100, "completion_tokens": 50}
    estimate = tracker.track_usage("gpt-4o-mini", usage)
    assert estimate.total_tokens == 150
    assert estimate.estimated_cost > 0


def test_track_usage_with_tenant():
    tracker = CostTracker()
    tracker.set_budget("tenant-1", 100.0)
    usage = {"prompt_tokens": 1000, "completion_tokens": 500}
    estimate = tracker.track_usage("gpt-4o-mini", usage, tenant_id="tenant-1")
    assert estimate.total_tokens == 1500


def test_set_and_get_budget():
    tracker = CostTracker()
    tracker.set_budget("tenant-1", 50.0)
    assert tracker.get_spend("tenant-1") == 0.0


def test_budget_not_exceeded():
    tracker = CostTracker()
    tracker.set_budget("tenant-1", 100.0)
    usage = {"prompt_tokens": 100, "completion_tokens": 50}
    tracker.track_usage("gpt-4o-mini", usage, tenant_id="tenant-1")
    assert tracker.is_budget_exceeded("tenant-1") is False


def test_budget_exceeded():
    tracker = CostTracker()
    tracker.set_budget("tenant-1", 0.001)
    usage = {"prompt_tokens": 100000, "completion_tokens": 50000}
    tracker.track_usage("gpt-4o", usage, tenant_id="tenant-1")
    assert tracker.is_budget_exceeded("tenant-1") is True


def test_get_spend_no_budget():
    tracker = CostTracker()
    assert tracker.get_spend("nonexistent") == 0.0


def test_budget_exceeded_no_budget():
    tracker = CostTracker()
    assert tracker.is_budget_exceeded("nonexistent") is False


def test_track_usage_total_tokens_from_usage():
    tracker = CostTracker()
    usage = {"total_tokens": 500}
    estimate = tracker.track_usage("gpt-4o-mini", usage)
    assert estimate.total_tokens == 500


def test_track_usage_empty_usage():
    tracker = CostTracker()
    estimate = tracker.track_usage("gpt-4o-mini", {})
    assert estimate.total_tokens == 0
    assert estimate.estimated_cost == 0.0


def test_update_existing_budget():
    tracker = CostTracker()
    tracker.set_budget("tenant-1", 50.0)
    tracker.set_budget("tenant-1", 100.0)
    assert tracker.get_spend("tenant-1") == 0.0


def test_cost_estimate_dataclass():
    ce = CostEstimate(prompt_tokens=100, completion_tokens=50, total_tokens=150, estimated_cost=0.01, model="gpt-4o")
    assert ce.prompt_tokens == 100
    assert ce.model == "gpt-4o"


def test_budget_enforcement_dataclass():
    be = BudgetEnforcement(tenant_id="t1", monthly_budget=100.0)
    assert be.is_exceeded is False
    assert be.current_spend == 0.0
