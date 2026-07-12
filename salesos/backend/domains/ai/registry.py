"""PromptTemplate Registry — versioned prompt lifecycle."""
from __future__ import annotations

from domains.ai.models import PromptTemplate


class PromptRegistry:
    def __init__(self) -> None:
        self._templates: dict[str, list[PromptTemplate]] = {}
        self._active: dict[str, PromptTemplate] = {}

    def register(self, template: PromptTemplate) -> None:
        if template.id not in self._templates:
            self._templates[template.id] = []
        for existing in self._templates[template.id]:
            if existing.version == template.version:
                existing.template = template.template
                existing.variables = template.variables
                existing.output_schema = template.output_schema
                existing.domain = template.domain
                existing.updated_at = template.updated_at
                return
        self._templates[template.id].append(template)

    def get(self, id: str, version: str | None = None) -> PromptTemplate | None:
        versions = self._templates.get(id)
        if not versions:
            return None
        if version:
            for t in versions:
                if t.version == version:
                    return t
            return None
        return self._active.get(id) or versions[-1]

    def list(self, domain: str | None = None) -> list[PromptTemplate]:
        results = []
        for versions in self._templates.values():
            for t in versions:
                if domain is None or t.domain == domain:
                    results.append(t)
        return results

    def activate(self, id: str, version: str) -> PromptTemplate | None:
        template = self.get(id, version)
        if template is None:
            return None
        for v in self._templates.get(id, []):
            v.active = False
        template.active = True
        self._active[id] = template
        return template
