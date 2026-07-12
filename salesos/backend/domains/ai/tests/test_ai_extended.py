"""Extended AI domain tests — service, registry, providers, grounding, guardrails."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from domains.ai.evaluator import (
    AIEvaluator,
    confidence_threshold,
    contains_keyword,
    exact_match,
    json_valid,
    length_check,
)
from domains.ai.models import AIModel, AIEvaluation, PromptTemplate
from domains.ai.registry import PromptRegistry
from domains.ai.service import AIService, AIProvider, DecisionPlatformProvider, OpenAIProvider


# ── PromptRegistry ──────────────────────────────────────────────────────────


def test_registry_register_and_get():
    reg = PromptRegistry()
    t = PromptTemplate(id="p1", name="Test", version="1.0", template="Hello {{name}}")
    reg.register(t)
    got = reg.get("p1")
    assert got is not None
    assert got.template == "Hello {{name}}"


def test_registry_get_nonexistent():
    reg = PromptRegistry()
    assert reg.get("missing") is None


def test_registry_get_specific_version():
    reg = PromptRegistry()
    reg.register(PromptTemplate(id="p1", name="Test", version="1.0", template="v1"))
    reg.register(PromptTemplate(id="p1", name="Test", version="2.0", template="v2"))
    assert reg.get("p1", version="1.0").template == "v1"
    assert reg.get("p1", version="2.0").template == "v2"
    assert reg.get("p1", version="3.0") is None


def test_registry_get_returns_latest_when_no_version():
    reg = PromptRegistry()
    reg.register(PromptTemplate(id="p1", name="Test", version="1.0", template="v1"))
    reg.register(PromptTemplate(id="p1", name="Test", version="2.0", template="v2"))
    got = reg.get("p1")
    assert got.template == "v2"


def test_registry_activate():
    reg = PromptRegistry()
    reg.register(PromptTemplate(id="p1", name="Test", version="1.0", template="v1"))
    reg.register(PromptTemplate(id="p1", name="Test", version="2.0", template="v2"))
    activated = reg.activate("p1", "1.0")
    assert activated is not None
    assert activated.active is True
    # get() now returns the activated version
    got = reg.get("p1")
    assert got.template == "v1"


def test_registry_activate_nonexistent():
    reg = PromptRegistry()
    assert reg.activate("missing", "1.0") is None


def test_registry_list_all():
    reg = PromptRegistry()
    reg.register(PromptTemplate(id="p1", name="A", version="1.0", template="a", domain="sales"))
    reg.register(PromptTemplate(id="p2", name="B", version="1.0", template="b", domain="support"))
    all_templates = reg.list()
    assert len(all_templates) == 2


def test_registry_list_by_domain():
    reg = PromptRegistry()
    reg.register(PromptTemplate(id="p1", name="A", version="1.0", template="a", domain="sales"))
    reg.register(PromptTemplate(id="p2", name="B", version="1.0", template="b", domain="support"))
    sales = reg.list(domain="sales")
    assert len(sales) == 1
    assert sales[0].domain == "sales"


def test_registry_update_existing_version():
    reg = PromptRegistry()
    reg.register(PromptTemplate(id="p1", name="Test", version="1.0", template="old"))
    reg.register(PromptTemplate(id="p1", name="Test", version="1.0", template="new"))
    got = reg.get("p1", version="1.0")
    assert got.template == "new"
    # Only one version exists
    assert len(reg.list()) == 1


# ── AIService ───────────────────────────────────────────────────────────────


class FakeProvider(AIProvider):
    async def generate(self, prompt, model=None, **kwargs):
        return f"Generated: {prompt}"


@pytest.mark.asyncio
async def test_ai_service_generate():
    registry = PromptRegistry()
    registry.register(PromptTemplate(id="greet", name="Greet", version="1.0", template="Hello {{name}}"))
    svc = AIService(registry=registry)
    svc.register_provider("fake", FakeProvider())

    result = await svc.generate("greet", {"name": "World"}, provider="fake")
    assert result == "Generated: Hello World"


@pytest.mark.asyncio
async def test_ai_service_generate_missing_template():
    svc = AIService()
    with pytest.raises(ValueError, match="not found"):
        await svc.generate("nonexistent", {})


@pytest.mark.asyncio
async def test_ai_service_generate_missing_provider():
    registry = PromptRegistry()
    registry.register(PromptTemplate(id="p1", name="P", version="1.0", template="test"))
    svc = AIService(registry=registry)
    with pytest.raises(ValueError, match="not registered"):
        await svc.generate("p1", {}, provider="nonexistent")


@pytest.mark.asyncio
async def test_ai_service_explain_no_provider():
    svc = AIService()
    result = await svc.explain("decision-1")
    assert "unavailable" in result.lower() or "not registered" in result.lower() or "unavailable" in result


@pytest.mark.asyncio
async def test_ai_service_explain_with_provider():
    svc = AIService()
    svc.register_provider("decision_platform", FakeProvider())
    result = await svc.explain("decision-1")
    assert "Generated:" in result


# ── OpenAIProvider ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_openai_provider_no_api_key():
    provider = OpenAIProvider(api_key=None)
    result = await provider.generate("test")
    assert result == ""


@pytest.mark.asyncio
async def test_openai_provider_no_client():
    provider = OpenAIProvider(api_key=None)
    assert provider.client is None


# ── DecisionPlatformProvider ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_decision_platform_provider_no_engine():
    provider = DecisionPlatformProvider(decision_engine=None)
    result = await provider.generate("test prompt")
    assert result == ""


@pytest.mark.asyncio
async def test_decision_platform_provider_with_engine():
    engine = AsyncMock()
    engine.evaluate.return_value = {"explanation": "Because X"}
    provider = DecisionPlatformProvider(decision_engine=engine)
    result = await provider.generate("explain", context={"id": "1"})
    assert result == "Because X"
    engine.evaluate.assert_called_once()


@pytest.mark.asyncio
async def test_decision_platform_provider_engine_returns_string():
    engine = AsyncMock()
    engine.evaluate.return_value = "simple string result"
    provider = DecisionPlatformProvider(decision_engine=engine)
    result = await provider.generate("test")
    assert result == "simple string result"


@pytest.mark.asyncio
async def test_decision_platform_provider_engine_exception():
    engine = AsyncMock()
    engine.evaluate.side_effect = RuntimeError("Engine error")
    provider = DecisionPlatformProvider(decision_engine=engine)
    result = await provider.generate("test")
    assert result == ""


# ── Built-in evaluator metrics (additional) ─────────────────────────────────


def test_exact_match_whitespace():
    assert exact_match("  hello  ", "hello") == 1.0


def test_exact_match_different():
    assert exact_match("hello", "world") == 0.0


def test_contains_keyword_case_insensitive():
    assert contains_keyword("Hello WORLD", "world") == 1.0


def test_contains_keyword_not_found():
    assert contains_keyword("hello", "xyz") == 0.0


def test_length_check_within_range():
    assert length_check("hi", min_len=1, max_len=10) == 1.0


def test_length_check_too_long():
    assert length_check("a" * 100, min_len=1, max_len=10) == 0.0


def test_length_check_exact_min():
    assert length_check("a", min_len=1) == 1.0


def test_length_check_below_min():
    assert length_check("", min_len=1) == 0.0


def test_json_valid_nested():
    assert json_valid('{"a": {"b": [1, 2, 3]}}') == 1.0


def test_json_valid_array():
    assert json_valid('[1, 2, 3]') == 1.0


def test_json_valid_invalid():
    assert json_valid("{not json}") == 0.0


def test_confidence_threshold_at_boundary():
    assert confidence_threshold('{"confidence": 0.7}', threshold=0.7) == 1.0


def test_confidence_threshold_missing_field():
    assert confidence_threshold('{"score": 0.9}', threshold=0.5) == 0.0


def test_confidence_threshold_non_json():
    assert confidence_threshold("not json", threshold=0.5) == 0.0


# ── AIEvaluator batch and aggregation ───────────────────────────────────────


def test_evaluate_batch_empty():
    evaluator = AIEvaluator()
    results = evaluator.evaluate_batch([])
    assert results == []


def test_evaluate_default_metrics():
    evaluator = AIEvaluator()
    result = evaluator.evaluate(
        prompt_id="p1", input="Q", output="Hello world",
    )
    assert len(result.metrics) > 0
    assert result.score >= 0.0


def test_get_metrics_multiple_prompts():
    evaluator = AIEvaluator()
    evaluator.evaluate(prompt_id="p1", input="Q", output="A", expected="A", metrics=["exact_match"])
    evaluator.evaluate(prompt_id="p2", input="Q", output="B", expected="B", metrics=["exact_match"])
    m1 = evaluator.get_metrics("p1")
    m2 = evaluator.get_metrics("p2")
    assert m1["total_evaluations"] == 1
    assert m2["total_evaluations"] == 1


def test_evaluate_with_all_metrics():
    evaluator = AIEvaluator()
    result = evaluator.evaluate(
        prompt_id="p-all", input="Q",
        output='{"confidence": 0.9, "data": "test"}',
        expected="test",
    )
    assert len(result.metrics) >= 4


# ── AIModel ─────────────────────────────────────────────────────────────────


def test_ai_model_dataclass():
    m = AIModel(provider="openai", model_name="gpt-4o", capabilities=["text", "code"])
    assert m.provider == "openai"
    assert "text" in m.capabilities


# ── PromptTemplate ──────────────────────────────────────────────────────────


def test_prompt_template_dataclass():
    t = PromptTemplate(id="p1", name="Greet", version="1.0", template="Hello {{name}}", variables=["name"], domain="sales")
    assert t.id == "p1"
    assert t.active is False
    assert "name" in t.variables


# ── AIService template rendering ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ai_service_multiple_variables():
    registry = PromptRegistry()
    registry.register(PromptTemplate(
        id="complex", name="Complex", version="1.0",
        template="Dear {{title}} {{name}}, your score is {{score}}",
    ))
    svc = AIService(registry=registry)
    svc.register_provider("fake", FakeProvider())
    result = await svc.generate("complex", {"title": "Mr", "name": "Ahmed", "score": "95"}, provider="fake")
    assert "Mr" in result
    assert "Ahmed" in result
    assert "95" in result


@pytest.mark.asyncio
async def test_ai_service_explain_returns_provider_result():
    registry = PromptRegistry()
    svc = AIService(registry=registry)

    class ExplainProvider(AIProvider):
        async def generate(self, prompt, model=None, **kwargs):
            return f"Explanation for {prompt}"

    svc.register_provider("decision_platform", ExplainProvider())
    result = await svc.explain("decision-42")
    assert "decision-42" in result
