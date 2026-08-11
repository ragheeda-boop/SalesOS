"""ResearchAgent execute_grounded shim — not live GA research AI."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from intelligence.agents.base import AgentResult, AgentTask
from intelligence.agents.research import ResearchAgent


def _task(**extra) -> AgentTask:
    payload = {"company_id": "comp-1", "company_name": "Acme", "tenant_id": "t-1"}
    payload.update(extra)
    return AgentTask(id="task-1", agent_type="ResearchAgent", input=payload)


@pytest.mark.asyncio
async def test_execute_grounded_exists_and_delegates_without_llm():
    agent = ResearchAgent(llm=None)
    result = await agent.execute_grounded(_task())

    assert isinstance(result, AgentResult)
    assert result.success is True
    assert result.task_id == "task-1"
    assert result.agent_type == "research"
    assert result.output.get("research_depth") == "minimal"
    assert result.output.get("company_id") == "comp-1"


@pytest.mark.asyncio
async def test_execute_grounded_merges_kwargs_into_task_input():
    agent = ResearchAgent(llm=None)
    result = await agent.execute_grounded(_task(), topic="licenses")

    assert result.success is True
    assert result.output.get("company_id") == "comp-1"


@pytest.mark.asyncio
async def test_execute_grounded_llm_service_without_client_uses_fallback():
    """LLMService has no .client — must not AttributeError or open HTTP."""
    llm = MagicMock(spec=["chat"])
    llm.chat = AsyncMock(side_effect=AssertionError("must not call LLM HTTP"))
    agent = ResearchAgent(llm=llm)

    result = await agent.execute_grounded(_task())

    assert result.success is True
    assert result.output.get("research_depth") == "minimal"
    llm.chat.assert_not_called()


@pytest.mark.asyncio
async def test_execute_grounded_with_legacy_client_still_uses_execute_path():
    llm = MagicMock()
    llm.client = object()
    llm.chat = AsyncMock(return_value=MagicMock(content="ok"))
    agent = ResearchAgent(llm=llm)

    result = await agent.execute_grounded(_task())

    assert result.success is True
    assert result.output.get("research_depth") == "llm"
    assert result.output.get("summary") == "ok"
    llm.chat.assert_called_once()
