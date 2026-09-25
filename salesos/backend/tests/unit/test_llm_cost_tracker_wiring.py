"""AI Foundation F2 runtime wiring + fail-open budget check (report 96)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import intelligence.providers.cost_tracker as ct
from intelligence.agents.llm import LLMService


def _svc(tracker) -> LLMService:
    svc = LLMService(default_tenant_id="t-1", cost_tracker=tracker)
    svc._reliable_provider = SimpleNamespace(
        provider_name="test", model_name="test-model",
        chat=AsyncMock(return_value=SimpleNamespace(
            content="ok", model="test-model", usage={"prompt_tokens": 1, "completion_tokens": 1},
            finish_reason=SimpleNamespace(value="stop"), cost=0.0,
        )),
    )
    svc._policy_gate = SimpleNamespace(
        check_input=lambda **k: SimpleNamespace(allowed=True, findings=[], sanitized_text="")
    )
    return svc


@pytest.mark.asyncio
async def test_budget_store_outage_does_not_block_the_call():
    tracker = SimpleNamespace(
        check_budget=AsyncMock(side_effect=ConnectionError("db down")),
        track=AsyncMock(), deduct_budget=AsyncMock(),
    )
    resp = await _svc(tracker).chat(system="s", messages=[{"role": "user", "content": "q"}])
    assert resp.finish_reason == "stop"
    tracker.check_budget.assert_awaited_once()


@pytest.mark.asyncio
async def test_exceeded_budget_still_blocks():
    tracker = SimpleNamespace(
        check_budget=AsyncMock(return_value=SimpleNamespace(
            would_exceed=True, monthly_budget=1.0, current_spend=2.0)),
        track=AsyncMock(), deduct_budget=AsyncMock(),
    )
    resp = await _svc(tracker).chat(system="s", messages=[{"role": "user", "content": "q"}])
    assert resp.finish_reason == "error"
    tracker.track.assert_not_awaited()


@pytest.mark.asyncio
async def test_boot_initializes_process_wide_tracker(monkeypatch):
    from app.boot import startup

    monkeypatch.setattr(ct, "_cost_tracker", None)
    app = SimpleNamespace(state=SimpleNamespace())
    await startup._init_llm_cost_tracker(app, MagicMock())
    assert ct.get_cost_tracker() is app.state.llm_cost_tracker
    # A per-request LLMService now picks it up without being passed one.
    assert LLMService()._cost_tracker is app.state.llm_cost_tracker
