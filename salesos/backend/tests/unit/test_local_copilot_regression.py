"""Local Copilot / AI regression tests (2026-08 audit loop).

Covers the root causes fixed for local Copilot operation:
1. PermissionRegistry default roles never registered at import -> RBAC 403s.
2. Agents gated LLM calls on non-existent ``self._llm.client`` -> silent fallback.
3. Quota admission semantics for ai_tokens (limit<=0 hard deny).

Unit-level: no database required.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import sdk.permissions as perms
from sdk.permissions import (
    PermissionAction,
    PermissionEnforcer,
    PermissionRegistry,
    Role,
)
from sdk.exceptions import PermissionDeniedError


# ---------------------------------------------------------------------------
# 1. RBAC: default roles registered once at import, idempotent on re-run
# ---------------------------------------------------------------------------


def test_default_roles_defined():
    roles = perms.PermissionRegistry.default_roles()
    assert {"admin", "manager", "user"} <= set(roles.keys())


def test_registry_registration_is_idempotent():
    before = len(PermissionRegistry._roles)
    perms._register_default_roles()
    after = len(PermissionRegistry._roles)
    assert before == after


def test_admin_role_has_copilot_read():
    admin = PermissionRegistry.get_role("admin")
    assert admin is not None
    keys = {p.key for p in admin.permissions}
    assert "copilot.read" in keys


def test_user_role_lacks_copilot_admin():
    user = PermissionRegistry.get_role("user")
    assert user is not None
    assert not PermissionRegistry.has_permission("user", "copilot", PermissionAction.ADMIN)


def test_enforcer_admin_copilot_read_passes():
    PermissionEnforcer.check("admin", "copilot", "read")


def test_enforcer_user_copilot_admin_denied():
    with pytest.raises(PermissionDeniedError):
        PermissionEnforcer.check("user", "copilot", "admin")


# ---------------------------------------------------------------------------
# 2. Agents call LLMService directly (no legacy .client attribute)
# ---------------------------------------------------------------------------


class _RecordingLLM:
    """Minimal stand-in exposing only the real chat() surface."""

    def __init__(self):
        self.chat = AsyncMock(
            return_value=SimpleNamespace(
                content="تحليل تجريبي",
                model="test-model",
                usage={"prompt_tokens": 1, "completion_tokens": 2},
            )
        )


def _task(agent_type: str, payload: dict):
    from intelligence.agents.base import AgentTask

    return AgentTask(id="t1", agent_type=agent_type, input=payload)


def test_no_agent_references_llm_client_attribute():
    from pathlib import Path

    import intelligence.agents as agents_pkg

    pkg_dir = Path(agents_pkg.__file__).parent
    offenders = [p.name for p in pkg_dir.glob("*.py") if "_llm.client" in p.read_text(encoding="utf-8")]
    assert offenders == [], f"agents still reference _llm.client: {offenders}"


async def test_forecast_agent_uses_llm_when_present():
    from intelligence.agents.forecast import ForecastAgent

    llm = _RecordingLLM()
    agent = ForecastAgent(llm)
    result = await agent.execute(_task("forecast", {"pipeline_value": 5_000_000}))
    assert llm.chat.await_count == 1
    assert result.success is True
    assert result.output.get("analysis") == "تحليل تجريبي"


async def test_forecast_agent_falls_back_without_llm():
    from intelligence.agents.forecast import ForecastAgent

    agent = ForecastAgent(None)
    result = await agent.execute(_task("forecast", {}))
    assert result.success is True
    assert result.confidence < 0.5  # honest low-confidence fallback


# ---------------------------------------------------------------------------
# 3. Quota admission semantics for ai_tokens
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "limit,used,expected",
    [
        (0, 0, True),  # zero/unset quota => hard deny even with zero usage
        (10_000, 0, False),
        (10_000, 9_999, False),
        (10_000, 10_000, True),
        (10_000, 11_000, True),
    ],
)
def test_ai_tokens_quota_semantics(limit, used, expected):
    from app.modules.admin.quota_enforcement import (
        QuotaLimit,
        evaluate_quota_violations,
    )

    violations = evaluate_quota_violations(
        limits={"ai_tokens": QuotaLimit(metric="ai_tokens", limit=limit)},
        usage={"ai_tokens": used},
        metrics=("ai_tokens",),
    )
    assert any(v.metric == "ai_tokens" for v in violations) is expected
