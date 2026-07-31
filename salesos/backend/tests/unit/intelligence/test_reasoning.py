"""Reasoning pipeline tests — analyze, reason, conclude, full pipeline."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from intelligence.reasoning import ReasoningPipeline
from intelligence.schemas import AgentAnalysis


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.chat = AsyncMock()
    llm.chat.return_value = MagicMock(content="Analysis result", usage={"total_tokens": 100})
    return llm


@pytest.fixture
def pipeline(mock_llm):
    return ReasoningPipeline(mock_llm)


@pytest.mark.asyncio
async def test_analyze(pipeline):
    result = await pipeline.analyze({"company": "SalesOS", "revenue": "1M"})
    assert "analysis" in result
    assert result["analysis"] == "Analysis result"


@pytest.mark.asyncio
async def test_reason(pipeline):
    result = await pipeline.reason({"analysis": "Data looks good", "raw_data": {"score": 95}})
    assert "reasoning" in result
    assert result["reasoning"] == "Analysis result"


@pytest.mark.asyncio
async def test_conclude(pipeline):
    result = await pipeline.conclude({"reasoning": "Strong evidence"})
    assert isinstance(result, AgentAnalysis)
    assert result.confidence == 0.8
    assert len(result.evidence) > 0


@pytest.mark.asyncio
async def test_full_pipeline(pipeline):
    result = await pipeline.full_pipeline({"company": "Test"})
    assert isinstance(result, AgentAnalysis)
    assert result.sources == ["llm_reasoning"]


def test_format_data_dict():
    pipeline = ReasoningPipeline(MagicMock())
    formatted = pipeline._format_data({"key": "value", "nested": {"a": 1}})
    assert "key: value" in formatted
    assert "nested:" in formatted


def test_format_data_list():
    pipeline = ReasoningPipeline(MagicMock())
    formatted = pipeline._format_data({"items": [{"name": "A"}, {"name": "B"}]})
    assert "items:" in formatted
    assert "[2 items]" in formatted


def test_format_data_simple_list():
    pipeline = ReasoningPipeline(MagicMock())
    formatted = pipeline._format_data({"tags": ["a", "b", "c"]})
    assert "tags:" in formatted


def test_format_data_scalar():
    pipeline = ReasoningPipeline(MagicMock())
    formatted = pipeline._format_data({"count": 42})
    assert "count: 42" in formatted


def test_format_data_empty():
    pipeline = ReasoningPipeline(MagicMock())
    formatted = pipeline._format_data({})
    assert formatted == ""


@pytest.mark.asyncio
async def test_analyze_empty_data(pipeline):
    result = await pipeline.analyze({})
    assert "analysis" in result


@pytest.mark.asyncio
async def test_conclude_with_minimal_reasoning(pipeline, mock_llm):
    mock_llm.chat.return_value = MagicMock(content="Minimal")
    result = await pipeline.conclude({"reasoning": "Short"})
    assert isinstance(result, AgentAnalysis)
