"""Prompt Registry tests — versioning, validation, categories, persistence."""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from intelligence.prompts.registry import PromptRegistry, PromptTemplate, PromptVersion, PromptValidationError, PromptNotFoundError


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
        model="gpt-4o-mini",
        temperature=0.3,
        domain="sales",
        category="onboarding",
        tags=["greeting", "welcome"],
    )


# ── Registration ───────────────────────────────────────────────────────────


def test_register_and_get(registry, sample_template):
    registry.register(sample_template)
    retrieved = registry.get("test-greeting")
    assert retrieved is not None
    assert retrieved.name == "greeting"
    assert retrieved.template == "Hello {name}, welcome to {company}!"


def test_register_nonexistent_get(registry):
    assert registry.get("nonexistent") is None


def test_register_duplicate_version(registry, sample_template):
    registry.register(sample_template)
    updated = PromptTemplate(
        id="test-greeting",
        name="greeting",
        version="1.0",
        template="Updated template {name}!",
        system="You are a friendly assistant.",
    )
    registry.register(updated)
    retrieved = registry.get("test-greeting", version="1.0")
    assert retrieved.template == "Updated template {name}!"
    assert len(registry.list()) == 1


# ── Versioning ────────────────────────────────────────────────────────────


def test_versioning(registry, sample_template):
    registry.register(sample_template)
    v2 = PromptTemplate(
        id="test-greeting",
        name="greeting",
        version="2.0",
        template="Hello {name}!",
        system="You are a helpful assistant.",
    )
    registry.register(v2)
    assert registry.get("test-greeting", version="1.0").template == "Hello {name}, welcome to {company}!"
    assert registry.get("test-greeting", version="2.0").template == "Hello {name}!"
    assert registry.get("test-greeting").version == "2.0"


def test_get_nonexistent_version(registry, sample_template):
    registry.register(sample_template)
    assert registry.get("test-greeting", version="99.0") is None


def test_get_versions_history(registry, sample_template):
    registry.register(sample_template, changelog="Initial version")
    v2 = PromptTemplate(id="test-greeting", name="greeting", version="2.0", template="Hello {name}!", system="")
    registry.register(v2, changelog="Simplified template")
    history = registry.get_versions("test-greeting")
    assert len(history) == 2
    assert history[0].changelog == "Initial version"
    assert history[1].changelog == "Simplified template"


# ── Activation ────────────────────────────────────────────────────────────


def test_activate(registry, sample_template):
    registry.register(sample_template)
    v2 = PromptTemplate(id="test-greeting", name="greeting", version="2.0", template="Hello {name}!", system="")
    registry.register(v2)
    activated = registry.activate("test-greeting", "1.0")
    assert activated is not None
    assert activated.version == "1.0"
    assert activated.active is True
    assert registry.get("test-greeting").version == "1.0"


def test_activate_nonexistent(registry):
    assert registry.activate("missing", "1.0") is None


# ── Listing ────────────────────────────────────────────────────────────────


def test_list_all(registry, sample_template):
    registry.register(sample_template)
    registry.register(PromptTemplate(id="p2", name="farewell", version="1.0", template="Bye {name}!", system="", domain="support"))
    all_templates = registry.list()
    assert len(all_templates) == 2


def test_list_by_domain(registry, sample_template):
    registry.register(sample_template)
    registry.register(PromptTemplate(id="p2", name="farewell", version="1.0", template="Bye {name}!", system="", domain="support"))
    sales = registry.list(domain="sales")
    assert len(sales) == 1
    assert sales[0].domain == "sales"


def test_list_by_category(registry, sample_template):
    registry.register(sample_template)
    registry.register(PromptTemplate(id="p2", name="farewell", version="1.0", template="Bye!", system="", category="offboarding"))
    onboarding = registry.list(category="onboarding")
    assert len(onboarding) == 1


def test_list_by_tag(registry, sample_template):
    registry.register(sample_template)
    registry.register(PromptTemplate(id="p2", name="farewell", version="1.0", template="Bye!", system="", tags=["farewell"]))
    greeting = registry.list(tag="greeting")
    assert len(greeting) == 1


def test_list_active(registry, sample_template):
    registry.register(sample_template)
    registry.activate("test-greeting", "1.0")
    active = registry.list_active()
    assert len(active) == 1
    assert active[0].id == "test-greeting"


# ── Render ─────────────────────────────────────────────────────────────────


def test_render(registry, sample_template):
    registry.register(sample_template)
    result = registry.render("test-greeting", name="Ahmed", company="SalesOS")
    assert "Ahmed" in result["user_prompt"]
    assert "SalesOS" in result["user_prompt"]
    assert result["config"]["model"] == "gpt-4o-mini"


def test_render_missing_placeholder(registry, sample_template):
    registry.register(sample_template)
    with pytest.raises(PromptValidationError):
        registry.render("test-greeting", name="Ahmed")


def test_render_nonexistent(registry):
    with pytest.raises(PromptNotFoundError):
        registry.render("nonexistent")


# ── Validation ─────────────────────────────────────────────────────────────


def test_validate_valid(registry, sample_template):
    registry.register(sample_template)
    errors = registry.validate("test-greeting")
    assert errors == []


def test_validate_nonexistent(registry):
    errors = registry.validate("nonexistent")
    assert len(errors) == 1


def test_validate_empty_template():
    registry = PromptRegistry()
    registry._templates["empty"] = [PromptTemplate(id="empty", name="empty", version="1.0", template="  ")]
    errors = registry.validate("empty")
    assert len(errors) == 1


def test_register_empty_id():
    registry = PromptRegistry()
    with pytest.raises(PromptValidationError):
        registry.register(PromptTemplate(id="", name="test", version="1.0", template="hi"))


def test_register_empty_name():
    registry = PromptRegistry()
    with pytest.raises(PromptValidationError):
        registry.register(PromptTemplate(id="t1", name="", version="1.0", template="hi"))


# ── Get By Name ────────────────────────────────────────────────────────────


def test_get_by_name(registry, sample_template):
    registry.register(sample_template)
    t = registry.get_by_name("greeting")
    assert t is not None
    assert t.id == "test-greeting"


def test_get_by_name_nonexistent(registry):
    assert registry.get_by_name("nonexistent") is None


# ── Search ─────────────────────────────────────────────────────────────────


def test_search(registry, sample_template):
    registry.register(sample_template)
    results = registry.search("greeting")
    assert len(results) == 1

    results = registry.search("welcome")
    assert len(results) == 1

    results = registry.search("nonexistent")
    assert len(results) == 0


# ── Categories ─────────────────────────────────────────────────────────────


def test_categories(registry, sample_template):
    registry.register(sample_template)
    registry.register(PromptTemplate(id="p2", name="farewell", version="1.0", template="Bye!", system="", category="offboarding"))
    categories = registry.get_categories()
    assert "onboarding" in categories
    assert "offboarding" in categories


# ── Persistence ────────────────────────────────────────────────────────────


def test_persist_and_load():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        path = f.name

    try:
        registry = PromptRegistry(persist_path=path)
        registry.register(PromptTemplate(id="p1", name="test", version="1.0", template="Hello {name}!", system="Be nice"))
        registry.activate("p1", "1.0")

        registry2 = PromptRegistry(persist_path=path)
        loaded = registry2.get("p1")
        assert loaded is not None
        assert loaded.name == "test"
        assert loaded.template == "Hello {name}!"
    finally:
        os.unlink(path)


# ── Evaluation Tags ────────────────────────────────────────────────────────


def test_evaluation_tags(registry):
    t = PromptTemplate(
        id="eval-test",
        name="eval-test",
        version="1.0",
        template="Test",
        system="",
        evaluation_tags=["regression-v1", "accuracy-test"],
    )
    registry.register(t)
    retrieved = registry.get("eval-test")
    assert "regression-v1" in retrieved.evaluation_tags


# ── Metadata ───────────────────────────────────────────────────────────────


def test_metadata(registry):
    t = PromptTemplate(
        id="meta-test",
        name="meta-test",
        version="1.0",
        template="Test",
        system="",
        metadata={"author": "AI Team", "reviewed": True},
    )
    registry.register(t)
    retrieved = registry.get("meta-test")
    assert retrieved.metadata["author"] == "AI Team"
    assert retrieved.metadata["reviewed"] is True


# ── Placeholder extraction ────────────────────────────────────────────────


def test_placeholder_extraction():
    t = PromptTemplate(id="t1", name="test", version="1.0", template="Hello {name}, your {role} is {status}")
    assert "name" in t.placeholders
    assert "role" in t.placeholders
    assert "status" in t.placeholders
    assert len(t.placeholders) == 3
