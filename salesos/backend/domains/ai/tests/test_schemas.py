"""Tests for AI domain Pydantic schemas."""

from pydantic import ValidationError
import pytest

from domains.ai.schemas import ActivateRequest, EvaluateRequest, GenerateRequest, PromptCreate


def test_prompt_create_valid():
    req = PromptCreate(id="p1", name="Test", template="Hello {{name}}")
    assert req.id == "p1"
    assert req.version == "1.0"
    assert req.variables == []


def test_prompt_create_with_all_fields():
    req = PromptCreate(
        id="p2", name="Full", version="2.0",
        template="Dear {{title}} {{name}}",
        variables=["title", "name"],
        output_schema={"type": "string"},
        domain="sales",
    )
    assert req.version == "2.0"
    assert "title" in req.variables
    assert req.output_schema == {"type": "string"}


def test_prompt_create_empty_id():
    with pytest.raises(ValidationError):
        PromptCreate(id="", name="Test", template="test")


def test_prompt_create_empty_name():
    with pytest.raises(ValidationError):
        PromptCreate(id="p1", name="", template="test")


def test_prompt_create_blank_template():
    with pytest.raises(ValidationError):
        PromptCreate(id="p1", name="Test", template="")


def test_prompt_create_long_id():
    with pytest.raises(ValidationError):
        PromptCreate(id="x" * 101, name="Test", template="test")


def test_evaluate_request_valid():
    req = EvaluateRequest(prompt_id="p1", input="Q", output="A")
    assert req.prompt_id == "p1"
    assert req.expected is None


def test_evaluate_request_with_expected():
    req = EvaluateRequest(prompt_id="p1", input="Q", output="A", expected="A")
    assert req.expected == "A"


def test_evaluate_request_with_metrics():
    req = EvaluateRequest(prompt_id="p1", input="Q", output="A", metrics=["exact_match"])
    assert "exact_match" in req.metrics


def test_generate_request_valid():
    req = GenerateRequest(prompt_template_id="greet", variables={"name": "World"})
    assert req.provider == "openai"


def test_generate_request_custom_provider():
    req = GenerateRequest(prompt_template_id="greet", variables={}, provider="anthropic")
    assert req.provider == "anthropic"


def test_generate_request_with_model():
    req = GenerateRequest(prompt_template_id="greet", variables={}, model="claude-3")
    assert req.model == "claude-3"


def test_activate_request_valid():
    req = ActivateRequest(id="p1", version="2.0")
    assert req.id == "p1"
    assert req.version == "2.0"


def test_activate_request_empty():
    with pytest.raises(ValidationError):
        ActivateRequest(id="", version="")
