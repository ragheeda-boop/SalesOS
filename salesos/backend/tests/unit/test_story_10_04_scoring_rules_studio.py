"""STORY-10-04 — Scoring Rules Studio: override + fail-safe fallback."""

from __future__ import annotations

import pytest

from app.modules.tenant_studio.scoring_rules import (
    PLATFORM_DEFAULT_WEIGHTS,
    ScoringBoost,
    ScoringRule,
    ScoringRuleError,
    build_scoring_rule,
)
from app.modules.tenant_studio.scoring_rules_engine import (
    evaluate_score,
    get_effective_dimension_weights,
    platform_default_score,
)
from app.modules.tenant_studio.scoring_rules_store import MemScoringRulesStore

_DIMS = {
    "buying_intent": 0.8,
    "engagement": 0.5,
    "fit": 0.4,
    "urgency": 0.2,
    "relationship": 0.1,
    "market_signal": 0.3,
}


def test_platform_default_score_deterministic() -> None:
    result = platform_default_score(_DIMS)
    assert result.source == "platform_default"
    assert result.fallback_used is False
    assert 0.0 <= result.score <= 1.0
    # Expected weighted mean against PLATFORM_DEFAULT_WEIGHTS
    tw = sum(PLATFORM_DEFAULT_WEIGHTS.values())
    expected = sum(_DIMS[d] * w for d, w in PLATFORM_DEFAULT_WEIGHTS.items()) / tw
    assert result.score == round(expected, 4)


def test_tenant_rule_overrides_platform_default() -> None:
    store = MemScoringRulesStore()
    rule = store.upsert(
        tenant_id="t1",
        name="Intent-heavy",
        target_type="company",
        dimension_weights={
            "buying_intent": 1.0,
            "engagement": 0.0,
            "fit": 0.0,
            "urgency": 0.0,
            "relationship": 0.0,
            "market_signal": 0.0,
        },
    )
    platform = platform_default_score(_DIMS)
    tenant = store.evaluate(
        tenant_id="t1",
        target_type="company",
        dimension_scores=_DIMS,
    )
    assert tenant.source == "tenant_rule"
    assert tenant.rule_id == rule.id
    assert tenant.score == 0.8
    assert tenant.score != platform.score


def test_tenant_boost_applied() -> None:
    store = MemScoringRulesStore()
    store.upsert(
        tenant_id="t1",
        name="Gov boost",
        target_type="lead",
        dimension_weights={"fit": 1.0},
        boosts=[{"field": "sector", "op": "eq", "value": "gov", "delta": 0.15}],
    )
    base = store.evaluate(
        tenant_id="t1",
        target_type="lead",
        dimension_scores={"fit": 0.5},
        attributes={"sector": "private"},
    )
    boosted = store.evaluate(
        tenant_id="t1",
        target_type="lead",
        dimension_scores={"fit": 0.5},
        attributes={"sector": "gov"},
    )
    assert base.score == 0.5
    assert boosted.score == 0.65


def test_fail_safe_fallback_on_rule_error() -> None:
    """AC: tenant rule error → platform default (fail-safe, not fail-open)."""
    broken = ScoringRule(
        id="broken",
        tenant_id="t1",
        name="Broken",
        target_type="opportunity",
        dimension_weights={"buying_intent": 0.0},  # sum == 0 → eval error
        boosts=[],
        active=True,
    )
    result = evaluate_score(dimension_scores=_DIMS, rule=broken)
    assert result.fallback_used is True
    assert result.source == "platform_default"
    assert result.fallback_reason
    assert "weights" in (result.fallback_reason or "").lower() or result.score >= 0
    platform = platform_default_score(_DIMS)
    assert result.score == platform.score


def test_fail_safe_on_boost_eval_error() -> None:
    rule = ScoringRule(
        id="bad-boost",
        tenant_id="t1",
        name="Bad boost",
        target_type="company",
        dimension_weights={"fit": 1.0},
        boosts=[ScoringBoost(field="employees", op="gte", value="not-a-number", delta=0.2)],
        active=True,
    )
    result = evaluate_score(
        dimension_scores={"fit": 0.4},
        rule=rule,
        attributes={"employees": "also-not-numeric"},
    )
    assert result.fallback_used is True
    assert result.source == "platform_default"


def test_get_effective_weights_fail_safe() -> None:
    weights, fell, reason = get_effective_dimension_weights(
        ScoringRule(
            id="x",
            tenant_id="t1",
            name="x",
            target_type="company",
            dimension_weights={"fit": 0.0},
            active=True,
        )
    )
    assert fell is True
    assert reason
    assert weights == PLATFORM_DEFAULT_WEIGHTS


def test_unknown_dimension_rejected_at_define() -> None:
    with pytest.raises(ScoringRuleError, match="unknown dimension"):
        build_scoring_rule(
            tenant_id="t1",
            name="bad",
            target_type="company",
            dimension_weights={"not_a_dim": 1.0},
        )


def test_tenant_isolation() -> None:
    store = MemScoringRulesStore()
    a = store.upsert(
        tenant_id="tenant-a",
        name="A",
        target_type="company",
        dimension_weights={"fit": 1.0},
    )
    assert store.get(a.id, tenant_id="tenant-b") is None
    assert store.get_active_for_target(tenant_id="tenant-b", target_type="company") is None
    assert store.list_for_tenant(tenant_id="tenant-b") == []
