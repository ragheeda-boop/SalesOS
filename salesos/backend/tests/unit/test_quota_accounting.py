"""Central ai_tokens quota accounting — single point in LLMService.chat().

Contract under test:
- successful call   -> usage_meters event recorded with ACTUAL provider tokens
- failed call       -> nothing recorded
- unbound/no tenant -> nothing recorded
- tenant isolation  -> recorded under the effective tenant only
- exhaustion        -> ai_tokens violation carries HTTP 429 mapping
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from intelligence.agents.llm import LLMService

TENANT_A = "a0000000-0000-4000-a000-000000000001"
TENANT_B = "b0000000-0000-4000-a000-000000000001"


class _FakeSession:
    def __init__(self):
        self.rows = []
        self.commits = 0

    def add(self, row):
        self.rows.append(row)

    async def flush(self):
        pass

    async def commit(self):
        self.commits += 1


def _meter_factory():
    sessions: list[_FakeSession] = []

    @asynccontextmanager
    async def factory():
        s = _FakeSession()
        sessions.append(s)
        yield s

    return factory, sessions


def _service(factory, *, usage=None, fail=False, tenant=TENANT_A):
    svc = LLMService(
        default_tenant_id=tenant,
        usage_meter_factory=factory,
    )
    response = SimpleNamespace(
        content="ok",
        model="test-model",
        usage=usage if usage is not None else {
            "prompt_tokens": 12,
            "completion_tokens": 34,
            "total_tokens": 46,
        },
        finish_reason=SimpleNamespace(value="stop"),
        cost=0.0,
    )
    provider = SimpleNamespace(
        provider_name="test",
        model_name="test-model",
        chat=AsyncMock(side_effect=RuntimeError("provider down")) if fail
        else AsyncMock(return_value=response),
    )
    svc._reliable_provider = provider
    # Neutral policy gate (allowlist policies are exercised elsewhere).
    svc._policy_gate = SimpleNamespace(
        check_input=lambda **k: SimpleNamespace(
            allowed=True, findings=[], sanitized_text=""
        )
    )
    return svc


@pytest.mark.asyncio
async def test_success_records_actual_provider_tokens():
    factory, sessions = _meter_factory()
    svc = _service(factory)
    resp = await svc.chat(system="s", messages=[{"role": "user", "content": "q"}])
    assert resp.finish_reason == "stop"
    assert len(sessions) == 1
    assert len(sessions[0].rows) == 1
    row = sessions[0].rows[0]
    assert str(row.tenant_id) == TENANT_A
    assert row.metric_key == "ai_tokens"
    assert row.quantity == 46.0  # provider-reported total, not an estimate
    assert sessions[0].commits >= 1


@pytest.mark.asyncio
async def test_total_falls_back_to_prompt_plus_completion():
    factory, sessions = _meter_factory()
    svc = _service(factory, usage={"prompt_tokens": 5, "completion_tokens": 7})
    await svc.chat(system="s", messages=[{"role": "user", "content": "q"}])
    assert sessions[0].rows[0].quantity == 12.0


@pytest.mark.asyncio
async def test_failed_call_records_nothing():
    factory, sessions = _meter_factory()
    svc = _service(factory, fail=True)
    with pytest.raises(RuntimeError):
        await svc.chat(system="s", messages=[{"role": "user", "content": "q"}])
    assert sessions == []


@pytest.mark.asyncio
async def test_zero_usage_records_nothing():
    factory, sessions = _meter_factory()
    svc = _service(factory, usage={"prompt_tokens": 0, "completion_tokens": 0})
    await svc.chat(system="s", messages=[{"role": "user", "content": "q"}])
    assert sessions == []


@pytest.mark.asyncio
async def test_explicit_tenant_overrides_bound_default():
    factory, sessions = _meter_factory()
    svc = _service(factory)  # bound to TENANT_A
    await svc.chat(
        system="s",
        messages=[{"role": "user", "content": "q"}],
        tenant_id=TENANT_B,
    )
    assert len(sessions[0].rows) == 1
    assert str(sessions[0].rows[0].tenant_id) == TENANT_B


@pytest.mark.asyncio
async def test_unbound_tenant_records_nothing():
    factory, sessions = _meter_factory()
    svc = _service(factory, tenant=None)
    await svc.chat(system="s", messages=[{"role": "user", "content": "q"}])
    assert sessions == []


def test_exhausted_ai_tokens_maps_429():
    from app.modules.admin.quota_enforcement import (
        QuotaLimit,
        evaluate_quota_violations,
    )

    violations = evaluate_quota_violations(
        limits={"ai_tokens": QuotaLimit(metric="ai_tokens", limit=100)},
        usage={"ai_tokens": 150},
        metrics=("ai_tokens",),
    )
    assert len(violations) == 1
    assert violations[0].status_code == 429
