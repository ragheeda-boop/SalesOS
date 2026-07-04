"""Extension API — hook system for extending every flow in the platform.

Hooks are named extension points:
  Before* — called before an operation (can reject/modify)
  After* — called after an operation (cannot reject)

Each plugin registers hooks. Multiple hooks per point = chain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from sdk.plugin_sdk import PluginManifest


@dataclass
class HookContext:
    """Context passed to every hook handler."""
    hook_name: str
    plugin_id: str
    tenant_id: str
    user_id: str
    payload: dict = field(default_factory=dict)
    result: Any = None
    errors: list[str] = field(default_factory=list)
    abort: bool = False

    def to_dict(self) -> dict:
        return {
            "hook_name": self.hook_name,
            "plugin_id": self.plugin_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "payload_keys": list(self.payload.keys()),
            "error_count": len(self.errors),
            "abort": self.abort,
        }


@dataclass
class HookDefinition:
    """Definition of a registered hook."""
    name: str
    plugin_id: str
    handler: Callable
    priority: int = 0  # Higher = runs first
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "plugin_id": self.plugin_id,
            "priority": self.priority,
            "description": self.description,
        }


# ── Hook Registry ─────────────────────────────────────────────

class HookRegistry:
    """Central registry of all extension hooks."""

    _hooks: dict[str, list[HookDefinition]] = {}
    _plugins: dict[str, PluginManifest] = {}

    @classmethod
    def register_plugin(cls, manifest: PluginManifest):
        cls._plugins[manifest.id] = manifest

    @classmethod
    def register_hook(cls, hook: HookDefinition):
        cls._hooks.setdefault(hook.name, []).append(hook)
        cls._hooks[hook.name].sort(key=lambda h: h.priority, reverse=True)

    @classmethod
    def execute(cls, hook_name: str, tenant_id: str = "",
                user_id: str = "", payload: Optional[dict] = None) -> HookContext:
        """Execute all handlers for a hook. Returns the accumulated context."""
        ctx = HookContext(
            hook_name=hook_name,
            plugin_id="system",
            tenant_id=tenant_id,
            user_id=user_id,
            payload=payload or {},
        )

        handlers = cls._hooks.get(hook_name, [])
        for hook in handlers:
            if ctx.abort:
                break
            plugin = cls._plugins.get(hook.plugin_id)
            if plugin and not plugin.enabled:
                continue  # Skip disabled plugins
            try:
                result = hook.handler(ctx)
                ctx.result = result
            except Exception as e:
                ctx.errors.append(f"[{hook.plugin_id}] {str(e)}")

        return ctx

    @classmethod
    def get_hooks(cls, hook_name: Optional[str] = None) -> list[HookDefinition]:
        if hook_name:
            return cls._hooks.get(hook_name, [])
        all_hooks = []
        for hooks in cls._hooks.values():
            all_hooks.extend(hooks)
        return all_hooks

    @classmethod
    def get_plugins(cls) -> list[PluginManifest]:
        return list(cls._plugins.values())

    @classmethod
    def hook_names(cls) -> list[str]:
        return sorted(cls._hooks.keys())


# ── Built-in Hook Points ──────────────────────────────────────

BUILTIN_HOOKS = [
    # Company lifecycle
    "before.company.created",
    "after.company.created",
    "before.company.updated",
    "after.company.updated",
    "before.company.merged",
    "after.company.merged",
    "before.company.enriched",
    "after.company.enriched",
    "before.company.deleted",
    "after.company.deleted",
    # Entity Resolution
    "before.entity.resolved",
    "after.entity.resolved",
    "before.golden_record.created",
    "after.golden_record.created",
    # Decision Engine
    "before.decision.evaluated",
    "after.decision.evaluated",
    "before.decision.executed",
    "after.decision.executed",
    "before.recommendation.made",
    "after.recommendation.made",
    # Search
    "before.search.executed",
    "after.search.executed",
    # Widget
    "before.widget.render",
    "after.widget.render",
    # Data Fabric
    "before.data.ingested",
    "after.data.ingested",
    "before.data.normalized",
    "after.data.normalized",
    # Actions
    "before.action.executed",
    "after.action.executed",
    # Timeline
    "after.event.recorded",
    # AI
    "before.ai.query",
    "after.ai.query",
]


def init_hooks():
    """Declare all built-in hook points. No handlers — just registration."""
    pass
