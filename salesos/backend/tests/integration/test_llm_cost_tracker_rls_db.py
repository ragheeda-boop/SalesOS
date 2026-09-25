"""AI Foundation F2 cost tracking / budget enforcement against a real
FORCE-RLS database under the restricted application role.

Two independent defects, both making per-tenant LLM budget enforcement a
no-op even for a correctly-configured CostTracker:

1. ``intelligence/providers/cost_tracker.py`` opened its own sessions and never
   pinned ``app.tenant_id``. ``tenant_llm_budgets`` and ``llm_cost_entries``
   are FORCE-RLS, so every budget read saw zero rows (treated as "no budget,
   allow"), and every INSERT failed its WITH CHECK.
2. ``LLMService.chat()`` ran the pre-call budget check against the effective
   (default-bound) tenant but gated cost recording / budget deduction on the
   explicit ``tenant_id`` argument. Agents call ``chat()`` without it (they
   rely on the per-request default binding), so spend was never recorded or
   deducted and the budget could never be exhausted.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from app.database import async_session, engine
from intelligence.agents.llm import LLMService
from intelligence.providers.cost_tracker import CostTracker


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


def _llm(tenant_id: str, tracker: CostTracker) -> LLMService:
    svc = LLMService(default_tenant_id=tenant_id, cost_tracker=tracker)
    response = SimpleNamespace(
        content="ok",
        model="test-model",
        usage={"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
        finish_reason=SimpleNamespace(value="stop"),
        cost=0.02,  # 2 cents
    )
    svc._reliable_provider = SimpleNamespace(
        provider_name="test", model_name="test-model",
        chat=AsyncMock(return_value=response),
    )
    svc._policy_gate = SimpleNamespace(
        check_input=lambda **k: SimpleNamespace(allowed=True, findings=[], sanitized_text="")
    )
    return svc


@pytest.mark.asyncio
async def test_budget_is_persisted_and_readable_under_rls():
    tracker = CostTracker(async_session)
    tenant = str(uuid.uuid4())
    await tracker.set_budget(tenant, monthly_budget_cents=500, enforced=True)

    budget = await tracker.get_budget(tenant)
    assert budget is not None
    assert budget.monthly_budget_cents == 500
    assert budget.is_enforced is True

    # Another tenant sees nothing.
    assert await tracker.get_budget(str(uuid.uuid4())) is None


@pytest.mark.asyncio
async def test_default_bound_tenant_spend_is_recorded_and_budget_blocks():
    tracker = CostTracker(async_session)
    tenant = str(uuid.uuid4())
    other = str(uuid.uuid4())
    await tracker.set_budget(tenant, monthly_budget_cents=1, enforced=True)

    svc = _llm(tenant, tracker)
    msgs = [{"role": "user", "content": "q"}]

    first = await svc.chat(system="s", messages=msgs)  # no explicit tenant_id
    assert first.finish_reason == "stop"

    records = await tracker.get_records(tenant_id=tenant)
    assert len(records) == 1
    assert records[0].tenant_id == tenant

    budget = await tracker.get_budget(tenant)
    assert budget.period_spend_cents == 2

    second = await svc.chat(system="s", messages=msgs)
    assert second.finish_reason == "error"
    assert any("Budget exceeded" in f for f in second.policy_findings)

    # Tenant isolation: the other tenant sees none of it.
    assert await tracker.get_records(tenant_id=other) == []
    assert await tracker.get_spend(other) == 0.0
