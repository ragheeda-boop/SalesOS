"""Prompt Registry v2 tests — version_hash, evaluation_criteria, A/B testing."""
from __future__ import annotations

import pytest

from intelligence.prompts.registry import PromptRegistry, PromptTemplate


@pytest.fixture
def registry():
    return PromptRegistry()


@pytest.fixture
def sample_template():
    return PromptTemplate(
        id="test-greeting",
        name="greeting",
        version="1.0",
        template="Hello {name}, welcome to {company}!",
        system="You are a friendly assistant.",
        evaluation_criteria={"accuracy": 0.9, "relevance": 0.8},
    )


def test_version_hash_auto_generated(sample_template):
    assert sample_template.version_hash != ""
    assert len(sample_template.version_hash) == 16


def test_version_hash_different_content():
    t1 = PromptTemplate(id="t1", name="t1", version="1.0", template="Hello {name}!", system="Be nice")
    t2 = PromptTemplate(id="t2", name="t2", version="1.0", template="Goodbye {name}!", system="Be nice")
    assert t1.version_hash != t2.version_hash


def test_version_hash_different_versions():
    t1 = PromptTemplate(id="t1", name="t1", version="1.0", template="Hello {name}!", system="Be nice")
    t2 = PromptTemplate(id="t1", name="t1", version="2.0", template="Hello {name}!", system="Be nice")
    assert t1.version_hash != t2.version_hash


def test_evaluation_criteria_on_template(sample_template):
    assert sample_template.evaluation_criteria["accuracy"] == 0.9
    assert sample_template.evaluation_criteria["relevance"] == 0.8


def test_evaluation_criteria_default():
    t = PromptTemplate(id="t1", name="t1", version="1.0", template="Test")
    assert t.evaluation_criteria == {}


def test_register_with_evaluation_criteria(registry):
    t = PromptTemplate(
        id="eval-test",
        name="eval-test",
        version="1.0",
        template="Analyze {data}",
        system="You are an analyst",
        evaluation_criteria={"precision": 0.95, "recall": 0.85},
    )
    registry.register(t)
    retrieved = registry.get("eval-test")
    assert retrieved.evaluation_criteria["precision"] == 0.95
    assert retrieved.evaluation_criteria["recall"] == 0.85


def test_version_hash_in_render_output(registry, sample_template):
    registry.register(sample_template)
    result = registry.render("test-greeting", name="Ahmed", company="SalesOS")
    assert "version_hash" in result
    assert result["version_hash"] == sample_template.version_hash


def test_version_hash_in_version_history(registry, sample_template):
    registry.register(sample_template, changelog="Initial")
    v2 = PromptTemplate(id="test-greeting", name="greeting", version="2.0", template="Hello {name}!", system="")
    registry.register(v2, changelog="Simplified")
    history = registry.get_versions("test-greeting")
    assert len(history) == 2
    assert history[0].version_hash != ""
    assert history[1].version_hash != ""
    assert history[0].version_hash != history[1].version_hash


def test_evaluation_criteria_in_version_history(registry, sample_template):
    registry.register(sample_template, changelog="Initial")
    history = registry.get_versions("test-greeting")
    assert history[0].evaluation_criteria["accuracy"] == 0.9


def test_version_hash_persistence():
    import tempfile, os, json
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        path = f.name
    try:
        registry = PromptRegistry(persist_path=path)
        t = PromptTemplate(id="p1", name="test", version="1.0", template="Hello {name}!", system="Be nice")
        registry.register(t)
        with open(path) as f:
            data = json.load(f)
        assert "version_hash" in data[0]
        assert data[0]["version_hash"] == t.version_hash
        assert "evaluation_criteria" in data[0]
    finally:
        os.unlink(path)


def test_ab_testing_set_agent_version(registry, sample_template):
    registry.register(sample_template)
    v2 = PromptTemplate(id="test-greeting", name="greeting", version="2.0", template="Hello {name}!", system="You are helpful.")
    registry.register(v2)

    registry.set_agent_active_version("sales-agent", "test-greeting", "1.0")
    assert registry.get_agent_active_version("sales-agent", "test-greeting") == "1.0"


def test_ab_testing_get_for_agent(registry, sample_template):
    registry.register(sample_template)
    v2 = PromptTemplate(id="test-greeting", name="greeting", version="2.0", template="Hello {name}!", system="You are helpful.")
    registry.register(v2)
    registry.activate("test-greeting", "2.0")

    template = registry.get_for_agent("test-greeting", agent_type="sales-agent")
    assert template.version == "2.0"

    registry.set_agent_active_version("support-agent", "test-greeting", "1.0")
    template = registry.get_for_agent("test-greeting", agent_type="support-agent")
    assert template.version == "1.0"


def test_ab_testing_multiple_agents(registry, sample_template):
    registry.register(sample_template)
    v2 = PromptTemplate(id="test-greeting", name="greeting", version="2.0", template="Hello {name}!", system="You are helpful.")
    registry.register(v2)

    registry.set_agent_active_version("agent-a", "test-greeting", "1.0")
    registry.set_agent_active_version("agent-b", "test-greeting", "2.0")

    assert registry.get_agent_active_version("agent-a", "test-greeting") == "1.0"
    assert registry.get_agent_active_version("agent-b", "test-greeting") == "2.0"


def test_ab_testing_fallback_to_active(registry, sample_template):
    registry.register(sample_template)
    registry.activate("test-greeting", "1.0")

    template = registry.get_for_agent("test-greeting")
    assert template is not None
    assert template.version == "1.0"


def test_update_preserves_version_hash(registry, sample_template):
    registry.register(sample_template)
    original_hash = sample_template.version_hash

    updated = PromptTemplate(
        id="test-greeting",
        name="greeting",
        version="1.0",
        template="Hello {name}, welcome to {company}!",
        system="You are a friendly assistant.",
    )
    registry.register(updated, changelog="Updated")
    retrieved = registry.get("test-greeting", version="1.0")
    assert retrieved.version_hash == original_hash
