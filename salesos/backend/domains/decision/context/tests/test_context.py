"""Tests for Decision Context Domain."""

import pytest

from domains.decision.context.models import DecisionContext, DecisionFactor, Policy
from domains.decision.context.service import DecisionService
from domains.decision.context.in_memory_repo import InMemoryDecisionRepository


def test_decision_factor():
    f = DecisionFactor(source_layer="knowledge", source_domain="forecast", key="forecast_drop",
                       value=0.22, label="Forecast dropped 22%", severity="warning")
    assert f.source_layer == "knowledge"
    assert f.severity == "warning"


def test_decision_context_severity():
    ctx = DecisionContext(id="c1", tenant_id="t1", target_id="opp-1", target_type="opportunity", factors=[
        DecisionFactor(source_layer="knowledge", source_domain="forecast", key="forecast_drop",
                       value=0.22, severity="warning"),
        DecisionFactor(source_layer="fact", source_domain="pipeline", key="stage_aging",
                       value=14, severity="critical"),
    ])
    assert len(ctx.critical_factors) == 1
    assert len(ctx.warnings) == 1
    assert ctx.has_critical()


def test_decision_context_no_pricing():
    """Context must not carry commercial data — only factors from other layers."""
    ctx = DecisionContext(id="c1", tenant_id="t1", target_id="opp-1", target_type="opportunity")
    assert not hasattr(ctx, "grand_total")
    assert not hasattr(ctx, "value")


@pytest.mark.asyncio
async def test_build_context():
    repo = InMemoryDecisionRepository()
    svc = DecisionService(repo)

    ctx = await svc.build_context("t1", "opp-1", factors=[
        svc.create_factor("knowledge", "forecast", "forecast_drop", 0.22, "Forecast dropped 22%", "warning"),
        svc.create_factor("fact", "pipeline", "stage_aging", 14, "14 days in stage", "critical"),
    ])
    assert ctx.target_id == "opp-1"
    assert len(ctx.factors) == 2
    assert ctx.has_critical()


@pytest.mark.asyncio
async def test_add_factor():
    repo = InMemoryDecisionRepository()
    svc = DecisionService(repo)

    ctx = await svc.build_context("t1", "opp-1")
    ctx = await svc.add_factor(ctx.id, svc.create_factor("measurement", "analytics", "revenue_variance", 0.15))
    assert len(ctx.factors) == 1


@pytest.mark.asyncio
async def test_policy_management():
    repo = InMemoryDecisionRepository()
    svc = DecisionService(repo)

    policy = Policy(id="p1", name="Discount Approval", description="Discounts over 30% require executive approval",
                    rule="if discount > 30% then requires executive approval", category="approval")
    await svc.add_policy("t1", policy)

    policies = await svc.list_policies("t1")
    assert len(policies) == 1
    assert policies[0].category == "approval"


@pytest.mark.asyncio
async def test_get_latest_context():
    repo = InMemoryDecisionRepository()
    svc = DecisionService(repo)

    await svc.build_context("t1", "opp-1", factors=[svc.create_factor("fact", "pipeline", "stage_aging", 5)])
    await svc.build_context("t1", "opp-1", factors=[svc.create_factor("fact", "pipeline", "stage_aging", 14)])

    latest = await svc.get_latest_context("opp-1", "opportunity")
    assert latest is not None
    assert latest.factors[0].value == 14
