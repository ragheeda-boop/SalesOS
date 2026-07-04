"""Feature Registry — tracks all modules, dependencies, and permissions.

Every module registers itself here. Enables the Internal Developer Platform
to generate documentation, validate dependencies, and check permissions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ModuleStatus(Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DEPRECATED = "deprecated"


@dataclass
class FeatureDependency:
    module: str
    version: str = ">=1.0.0"
    optional: bool = False


@dataclass
class FeatureModule:
    name: str
    label: str
    label_ar: str
    description: str
    description_ar: str
    version: str
    status: ModuleStatus = ModuleStatus.PLANNED
    dependencies: list[FeatureDependency] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    api_prefix: str = ""
    sprint: int = 1
    owner: str = ""
    tags: list[str] = field(default_factory=list)


class FeatureRegistry:
    """Global registry for all product features/modules."""

    _modules: dict[str, FeatureModule] = {}
    _graph: dict[str, set[str]] = {}

    @classmethod
    def register(cls, module: FeatureModule) -> None:
        cls._modules[module.name] = module
        cls._graph[module.name] = {d.module for d in module.dependencies if not d.optional}

    @classmethod
    def get(cls, name: str) -> FeatureModule | None:
        return cls._modules.get(name)

    @classmethod
    def all(cls) -> dict[str, FeatureModule]:
        return dict(cls._modules)

    @classmethod
    def dependency_order(cls) -> list[str]:
        """Topological sort — modules with no deps first."""
        visited: set[str] = set()
        result: list[str] = []

        def _visit(name: str) -> None:
            if name in visited:
                return
            visited.add(name)
            deps = cls._graph.get(name, set())
            for dep in deps:
                _visit(dep)
            result.append(name)

        for name in cls._modules:
            if name not in visited:
                _visit(name)
        return result
