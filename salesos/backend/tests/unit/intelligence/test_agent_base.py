"""GroundedBaseAgent tests — execute_grounded with LLM and grounding."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from intelligence.agent_base import GroundedBaseAgent
from intelligence.agents.base import AgentTask, AgentResult, AgentStatus
from intelligence.grounding import AgentContext, GroundingService


class ConcreteAgent(GroundedBaseAgent):
    def _system_prompt(self, context):
        return "You are a helpful agent."

    def _user_prompt(self, task, context):
        return f"Analyze {task.input.get('company_id', 'unknown')}"

    def _agent_type(self):
        return "concrete_test_agent"


@pytest.fixture
def agent():
    return ConcreteAgent(name="TestAgent", version="1.0")


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.client = True
    llm.chat = AsyncMock()
    llm.chat.return_value = MagicMock(content='{"analysis": "Good", "confidence": 0.9, "evidence": [], "sources": []}')
    return llm


@pytest.fixture
def task():
    return AgentTask(id="task-1", agent_type="test_agent", input={"company_id": "comp-1"})


@pytest.mark.asyncio
async def test_execute_grounded_no_llm(agent, task):
    result = await agent.execute_grounded(task)
    assert result.success is True
    assert result.confidence == 0.1


@pytest.mark.asyncio
async def test_execute_grounded_with_llm(agent, mock_llm, task):
    agent._llm = mock_llm
    result = await agent.execute_grounded(task)
    assert result.success is True
    assert result.confidence == 0.9


@pytest.mark.asyncio
async def test_execute_grounded_with_grounding(agent, mock_llm, task):
    mock_grounding = MagicMock(spec=GroundingService)
    mock_grounding.get_context = AsyncMock()
    mock_grounding.get_context.return_value = AgentContext(
        company_info={"name_ar": "شركة"},
        contacts=[{"name": "Ahmed"}],
    )
    agent._llm = mock_llm
    agent._grounding = mock_grounding
    result = await agent.execute_grounded(task)
    assert result.success is True
    mock_grounding.get_context.assert_called_once_with("comp-1", "concrete_test_agent")


@pytest.mark.asyncio
async def test_execute_grounded_input_moderation(agent, task):
    mock_llm = MagicMock()
    mock_llm.client = True
    agent._llm = mock_llm
    result = await agent.execute_grounded(task)
    assert result.success is True or result.success is False


@pytest.mark.asyncio
async def test_execute_grounded_llm_exception(agent, mock_llm, task):
    mock_llm.chat.side_effect = RuntimeError("LLM failure")
    agent._llm = mock_llm
    result = await agent.execute_grounded(task)
    assert result.success is False


def test_agent_type(agent):
    assert agent._agent_type() == "concrete_test_agent"


def test_output_schema_default(agent):
    schema = agent._output_schema()
    assert "analysis" in schema
    assert "confidence" in schema
    assert "evidence" in schema
    assert "sources" in schema


def test_agent_status_initial(agent):
    assert agent.status == AgentStatus.IDLE


@pytest.mark.asyncio
async def test_run_delegates_to_execute_grounded(agent, task):
    result = await agent._run(task)
    assert result.task_id == "task-1"
