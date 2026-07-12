from __future__ import annotations

import os
import yaml
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PromptTemplate:
    name: str
    version: int
    template: str
    system: str
    model: str
    temperature: float
    output_schema: str
    placeholders: list[str] = field(default_factory=list)

    def __post_init__(self):
        import re
        self.placeholders = re.findall(r"\{(\w+)\}", self.template)


class PromptNotFoundError(KeyError):
    pass


class PromptRegistry:
    def __init__(self, yaml_dir: str | None = None):
        self._templates: dict[str, list[PromptTemplate]] = {}
        if yaml_dir and os.path.isdir(yaml_dir):
            self._load_from_yaml(yaml_dir)

    def register(self, template: PromptTemplate):
        self._templates.setdefault(template.name, []).append(template)
        self._templates[template.name].sort(key=lambda t: t.version, reverse=True)

    def get(self, name: str, version: int | str = "latest") -> PromptTemplate:
        versions = self._templates.get(name)
        if not versions:
            raise PromptNotFoundError(f"Prompt '{name}' not found")
        if version == "latest":
            return versions[0]
        for t in versions:
            if t.version == version:
                return t
        raise PromptNotFoundError(f"Prompt '{name}' version {version} not found")

    def list_versions(self, name: str) -> list[int]:
        versions = self._templates.get(name)
        if not versions:
            raise PromptNotFoundError(f"Prompt '{name}' not found")
        return [t.version for t in versions]

    def render(self, name: str, version: int | str = "latest", **kwargs) -> dict:
        template = self.get(name, version=version)
        user_prompt = template.template.format(**kwargs)
        return {
            "system_prompt": template.system,
            "user_prompt": user_prompt,
            "config": {
                "model": template.model,
                "temperature": template.temperature,
                "output_schema": template.output_schema,
            },
        }

    def _load_from_yaml(self, yaml_dir: str):
        for filename in os.listdir(yaml_dir):
            if filename.endswith((".yaml", ".yml")):
                path = os.path.join(yaml_dir, filename)
                with open(path, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                for name, cfg in data.items():
                    self.register(PromptTemplate(
                        name=name,
                        version=cfg.get("version", 1),
                        template=cfg.get("user", ""),
                        system=cfg.get("system", ""),
                        model=cfg.get("model", "gpt-4o-mini"),
                        temperature=cfg.get("temperature", 0.3),
                        output_schema=cfg.get("output_schema", "agent_analysis"),
                    ))
