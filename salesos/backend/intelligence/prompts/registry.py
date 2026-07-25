from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
import yaml
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class PromptTemplate:
    id: str
    name: str
    version: str
    template: str
    system: str = ""
    model: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_tokens: int | None = None
    output_schema: str | None = None
    placeholders: list[str] = field(default_factory=list)
    domain: str = "general"
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    active: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evaluation_tags: list[str] = field(default_factory=list)
    evaluation_criteria: dict[str, Any] = field(default_factory=dict)
    version_hash: str = ""
    author: str = "system"

    def __post_init__(self):
        if not self.placeholders:
            self.placeholders = re.findall(r"\{(\w+)\}", self.template)
        if not self.version_hash:
            self.version_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        raw = f"{self.template}|{self.system}|{self.version}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass
class PromptVersion:
    version: str
    template: str
    system: str
    model: str
    temperature: float
    max_tokens: int | None
    output_schema: str | None
    changelog: str = ""
    version_hash: str = ""
    evaluation_criteria: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PromptValidationError(ValueError):
    pass


class PromptNotFoundError(KeyError):
    pass


class PromptRegistry:
    """Enhanced Prompt Registry with persistence, versioning, validation, categories, and evaluation tags.

    Supports:
    - Versioning with full history tracking
    - Template validation (placeholder completeness, schema validation)
    - Categories and tags for organization
    - Evaluation tags for A/B testing and regression tracking
    - Active version management
    - YAML import/export
    """

    def __init__(self, yaml_dir: str | None = None, persist_path: str | None = None):
        self._templates: dict[str, list[PromptTemplate]] = {}
        self._active: dict[str, PromptTemplate] = {}
        self._version_history: dict[str, list[PromptVersion]] = {}
        self._categories: dict[str, list[str]] = {}
        self._persist_path = persist_path
        self._agent_version_override: dict[str, dict[str, str]] = {}

        if yaml_dir and os.path.isdir(yaml_dir):
            self._load_from_yaml(yaml_dir)

        if persist_path and os.path.isfile(persist_path):
            self._load_from_file(persist_path)

    def register(self, template: PromptTemplate, changelog: str = "") -> PromptTemplate:
        self._validate_template(template)

        if template.id not in self._templates:
            self._templates[template.id] = []

        for existing in self._templates[template.id]:
            if existing.version == template.version:
                existing.template = template.template
                existing.system = template.system
                existing.model = template.model
                existing.temperature = template.temperature
                existing.max_tokens = template.max_tokens
                existing.output_schema = template.output_schema
                existing.domain = template.domain
                existing.category = template.category
                existing.tags = template.tags
                existing.metadata = template.metadata
                existing.evaluation_tags = template.evaluation_tags
                existing.evaluation_criteria = template.evaluation_criteria
                existing.version_hash = template.version_hash or template._compute_hash()
                existing.updated_at = datetime.now(timezone.utc)
                existing.placeholders = template.placeholders
                self._add_version_history(template, changelog or "Updated")
                self._persist()
                return existing

        template.updated_at = datetime.now(timezone.utc)
        self._templates[template.id].append(template)
        self._templates[template.id].sort(key=lambda t: t.version, reverse=True)

        self._add_category(template.category, template.id)
        self._add_version_history(template, changelog or "Created")
        self._persist()
        return template

    def get(self, id: str, version: str | None = None) -> PromptTemplate | None:
        versions = self._templates.get(id)
        if not versions:
            return None
        if version:
            for t in versions:
                if t.version == version:
                    return t
            return None
        return self._active.get(id) or versions[0]

    def get_by_name(self, name: str, version: str | None = None) -> PromptTemplate | None:
        for versions in self._templates.values():
            for t in versions:
                if t.name == name:
                    if version is None or t.version == version:
                        return t
        return None

    def list(self, domain: str | None = None, category: str | None = None, tag: str | None = None) -> list[PromptTemplate]:
        results = []
        for versions in self._templates.values():
            for t in versions:
                if domain is not None and t.domain != domain:
                    continue
                if category is not None and t.category != category:
                    continue
                if tag is not None and tag not in t.tags:
                    continue
                results.append(t)
        return results

    def list_active(self) -> list[PromptTemplate]:
        return list(self._active.values())

    def activate(self, id: str, version: str) -> PromptTemplate | None:
        template = self.get(id, version)
        if template is None:
            return None
        for v in self._templates.get(id, []):
            v.active = False
        template.active = True
        self._active[id] = template
        self._persist()
        return template

    def set_agent_active_version(self, agent_type: str, prompt_id: str, version: str) -> None:
        if agent_type not in self._agent_version_override:
            self._agent_version_override[agent_type] = {}
        self._agent_version_override[agent_type][prompt_id] = version

    def get_agent_active_version(self, agent_type: str, prompt_id: str) -> str | None:
        return self._agent_version_override.get(agent_type, {}).get(prompt_id)

    def get_for_agent(self, prompt_id: str, agent_type: str | None = None) -> PromptTemplate | None:
        if agent_type:
            version = self.get_agent_active_version(agent_type, prompt_id)
            if version:
                return self.get(prompt_id, version)
        return self.get(prompt_id)

    def get_versions(self, id: str) -> list[PromptVersion]:
        return self._version_history.get(id, [])

    def get_categories(self) -> dict[str, list[str]]:
        return dict(self._categories)

    def render(self, id: str, version: str | None = None, **kwargs: Any) -> dict[str, Any]:
        template = self.get(id, version)
        if not template:
            raise PromptNotFoundError(f"Prompt '{id}' not found")

        self._validate_placeholders(template, kwargs)

        try:
            user_prompt = template.template
            for key, value in kwargs.items():
                user_prompt = user_prompt.replace(f"{{{key}}}", str(value))
        except KeyError as exc:
            raise PromptValidationError(f"Missing placeholder: {exc}") from exc

        system_prompt = template.system
        for key, value in kwargs.items():
            system_prompt = system_prompt.replace(f"{{{key}}}", str(value))

        return {
            "id": template.id,
            "name": template.name,
            "version": template.version,
            "version_hash": template.version_hash,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "config": {
                "model": template.model,
                "temperature": template.temperature,
                "max_tokens": template.max_tokens,
                "output_schema": template.output_schema,
            },
        }

    def search(self, query: str) -> list[PromptTemplate]:
        query_lower = query.lower()
        results = []
        for versions in self._templates.values():
            for t in versions:
                if (query_lower in t.name.lower()
                        or query_lower in t.template.lower()
                        or query_lower in t.domain.lower()
                        or query_lower in t.category.lower()
                        or any(query_lower in tag.lower() for tag in t.tags)):
                    results.append(t)
        return results

    def validate(self, id: str, version: str | None = None) -> list[str]:
        template = self.get(id, version)
        if not template:
            return [f"Prompt '{id}' not found"]

        errors = []
        if not template.template.strip():
            errors.append("Template is empty")
        if not template.placeholders:
            pass
        for ph in template.placeholders:
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", ph):
                errors.append(f"Invalid placeholder name: {ph}")
        return errors

    def _validate_template(self, template: PromptTemplate) -> None:
        if not template.id.strip():
            raise PromptValidationError("Prompt ID is required")
        if not template.name.strip():
            raise PromptValidationError("Prompt name is required")
        if not template.template.strip():
            raise PromptValidationError("Prompt template content is required")

    def _validate_placeholders(self, template: PromptTemplate, kwargs: dict[str, Any]) -> None:
        missing = [ph for ph in template.placeholders if ph not in kwargs]
        if missing and template.placeholders:
            raise PromptValidationError(f"Missing placeholders: {missing}")

    def _add_category(self, category: str, prompt_id: str) -> None:
        if category not in self._categories:
            self._categories[category] = []
        if prompt_id not in self._categories[category]:
            self._categories[category].append(prompt_id)

    def _add_version_history(self, template: PromptTemplate, changelog: str) -> None:
        if template.id not in self._version_history:
            self._version_history[template.id] = []
        self._version_history[template.id].append(PromptVersion(
            version=template.version,
            template=template.template,
            system=template.system,
            model=template.model,
            temperature=template.temperature,
            max_tokens=template.max_tokens,
            output_schema=template.output_schema,
            changelog=changelog,
            version_hash=template.version_hash or template._compute_hash(),
            evaluation_criteria=template.evaluation_criteria,
        ))

    def _load_from_yaml(self, yaml_dir: str) -> None:
        for filename in os.listdir(yaml_dir):
            if filename.endswith((".yaml", ".yml")):
                path = os.path.join(yaml_dir, filename)
                with open(path, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                for name, cfg in data.items():
                    template = PromptTemplate(
                        id=cfg.get("id", name),
                        name=name,
                        version=str(cfg.get("version", 1)),
                        template=cfg.get("user", ""),
                        system=cfg.get("system", ""),
                        model=cfg.get("model", "gpt-4o-mini"),
                        temperature=cfg.get("temperature", 0.3),
                        max_tokens=cfg.get("max_tokens"),
                        output_schema=cfg.get("output_schema"),
                        domain=cfg.get("domain", "general"),
                        category=cfg.get("category", "general"),
                        tags=cfg.get("tags", []),
                        evaluation_tags=cfg.get("evaluation_tags", []),
                        evaluation_criteria=cfg.get("evaluation_criteria", {}),
                        metadata=cfg.get("metadata", {}),
                        author=cfg.get("author", "system"),
                    )
                    self.register(template, changelog=f"Imported from {filename}")

    def _load_from_file(self, path: str) -> None:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                template = PromptTemplate(**item)
                self._templates.setdefault(template.id, []).append(template)
                if template.active:
                    self._active[template.id] = template
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    def _persist(self) -> None:
        if not self._persist_path:
            return
        try:
            data = []
            for versions in self._templates.values():
                for t in versions:
                    data.append({
                        "id": t.id,
                        "name": t.name,
                        "version": t.version,
                        "template": t.template,
                        "system": t.system,
                        "model": t.model,
                        "temperature": t.temperature,
                        "max_tokens": t.max_tokens,
                        "output_schema": t.output_schema,
                        "placeholders": t.placeholders,
                        "domain": t.domain,
                        "category": t.category,
                        "tags": t.tags,
                        "active": t.active,
                        "metadata": t.metadata,
                        "evaluation_tags": t.evaluation_tags,
                        "evaluation_criteria": t.evaluation_criteria,
                        "version_hash": t.version_hash,
                        "author": t.author,
                    })
            os.makedirs(os.path.dirname(self._persist_path), exist_ok=True)
            with open(self._persist_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except (OSError, IOError):
            pass
