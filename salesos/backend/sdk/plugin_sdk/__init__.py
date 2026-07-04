"""Plugin SDK — build plugins that extend SalesOS safely.

Every plugin must:
  1. Declare a manifest (id, version, permissions, hooks, widgets, dependencies)
  2. Register hooks only (no direct runtime access)
  3. Run in a sandbox (resource limits, API scoping)

The Plugin SDK provides:
  - Manifest builder
  - Hook registration
  - Sandbox config
  - Isolated storage access
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class PluginManifest:
    """Required metadata for every plugin."""
    id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    license: str = "MIT"
    permissions: list[str] = field(default_factory=list)
    hooks: list[str] = field(default_factory=list)  # Hook IDs this plugin subscribes to
    widgets: list[str] = field(default_factory=list)  # Widget IDs this plugin provides
    dependencies: list[str] = field(default_factory=list)  # Plugin IDs this depends on
    config_schema: Optional[dict] = None  # JSON Schema for plugin-level config
    resource_limits: dict = field(default_factory=lambda: {
        "max_calls_per_sec": 100,
        "max_memory_mb": 50,
        "max_timeout_ms": 5000,
    })
    icon: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "permissions": self.permissions,
            "hooks": self.hooks,
            "widgets": self.widgets,
            "dependencies": self.dependencies,
            "config_schema": self.config_schema,
            "resource_limits": self.resource_limits,
            "icon": self.icon,
            "tags": self.tags,
        }


@dataclass
class PluginInstance:
    """A loaded plugin instance (sandboxed)."""
    manifest: PluginManifest
    config: dict = field(default_factory=dict)
    enabled: bool = True
    storage: dict = field(default_factory=dict)  # Isolated key-value storage

    def to_dict(self) -> dict:
        return {
            "manifest": self.manifest.to_dict(),
            "config": self.config,
            "enabled": self.enabled,
        }


class PluginBuilder:
    """Build a plugin manifest step by step."""

    def __init__(self, plugin_id: str, name: str):
        self._manifest = PluginManifest(id=plugin_id, name=name)

    def version(self, version: str) -> "PluginBuilder":
        self._manifest.version = version
        return self

    def described(self, description: str) -> "PluginBuilder":
        self._manifest.description = description
        return self

    def by(self, author: str) -> "PluginBuilder":
        self._manifest.author = author
        return self

    def requires_permissions(self, *perms: str) -> "PluginBuilder":
        self._manifest.permissions = list(perms)
        return self

    def hooks_into(self, *hooks: str) -> "PluginBuilder":
        self._manifest.hooks = list(hooks)
        return self

    def provides_widgets(self, *widgets: str) -> "PluginBuilder":
        self._manifest.widgets = list(widgets)
        return self

    def depends_on(self, *plugins: str) -> "PluginBuilder":
        self._manifest.dependencies = list(plugins)
        return self

    def with_config(self, schema: dict) -> "PluginBuilder":
        self._manifest.config_schema = schema
        return self

    def with_limits(self, **limits) -> "PluginBuilder":
        self._manifest.resource_limits.update(limits)
        return self

    def build(self) -> PluginManifest:
        return self._manifest


def create_plugin(plugin_id: str, name: str) -> PluginBuilder:
    """Entry point: start building a new plugin."""
    return PluginBuilder(plugin_id, name)
