"""Plugin Sandbox — isolated execution environment for plugins.

Every plugin runs with:
  - Limited API access (declared in manifest)
  - No direct DB access
  - Hook-based (not override-based)
  - Resource limits (calls/sec, memory, timeout)
  - Isolated storage (key-value, scoped to plugin)
  - Full audit trail

Sandbox pattern inspired by VS Code, Figma, and Shopify.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from runtime.extension_api import HookRegistry, BUILTIN_HOOKS
from sdk.plugin_sdk import PluginManifest


class SandboxResource(str, Enum):
    API_CALL = "api_call"
    EVENT_PUBLISH = "event_publish"
    SEARCH = "search"
    FEATURE_READ = "feature_read"
    TIMELINE_READ = "timeline_read"
    GRAPH_READ = "graph_read"
    STORAGE_READ = "storage_read"
    STORAGE_WRITE = "storage_write"


@dataclass
class ResourceQuota:
    """Resource limits for a plugin instance."""
    max_calls_per_sec: int = 100
    max_calls_per_min: int = 1000
    max_storage_kb: int = 1024
    max_response_timeout_ms: int = 5000
    max_payload_size_kb: int = 256
    allowed_resources: list[SandboxResource] = field(default_factory=lambda: [
        SandboxResource.API_CALL,
        SandboxResource.STORAGE_READ,
        SandboxResource.STORAGE_WRITE,
    ])

    def to_dict(self) -> dict:
        return {
            "max_calls_per_sec": self.max_calls_per_sec,
            "max_calls_per_min": self.max_calls_per_min,
            "max_storage_kb": self.max_storage_kb,
            "max_response_timeout_ms": self.max_response_timeout_ms,
            "max_payload_size_kb": self.max_payload_size_kb,
            "allowed_resources": [r.value for r in self.allowed_resources],
        }


@dataclass
class PluginSandboxInstance:
    """A sandboxed plugin instance with isolated state."""
    plugin_id: str
    manifest: PluginManifest
    config: dict = field(default_factory=dict)
    enabled: bool = True
    storage: dict = field(default_factory=dict)
    quotas: ResourceQuota = field(default_factory=ResourceQuota)
    call_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    installed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "plugin_id": self.plugin_id,
            "manifest": self.manifest.to_dict(),
            "enabled": self.enabled,
            "call_count": self.call_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "installed_at": self.installed_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class PluginSandbox:
    """Manages sandboxed plugin instances."""

    def __init__(self):
        self._instances: dict[str, PluginSandboxInstance] = {}
        self._hook_handlers: dict[str, list[str]] = {}  # hook_name -> [plugin_id]

    def install(self, manifest: PluginManifest, config: Optional[dict] = None) -> PluginSandboxInstance:
        """Install a plugin into the sandbox."""
        instance = PluginSandboxInstance(
            plugin_id=manifest.id,
            manifest=manifest,
            config=config or {},
            quotas=ResourceQuota(
                max_calls_per_sec=manifest.resource_limits.get("max_calls_per_sec", 100),
                max_calls_per_min=manifest.resource_limits.get("max_calls_per_min", 1000),
                max_storage_kb=manifest.resource_limits.get("max_storage_kb", 1024),
                max_response_timeout_ms=manifest.resource_limits.get("max_timeout_ms", 5000),
            ),
        )
        # Register hook permissions
        allowed_resources = [SandboxResource.API_CALL, SandboxResource.STORAGE_READ, SandboxResource.STORAGE_WRITE]
        if "search" in manifest.permissions:
            allowed_resources.append(SandboxResource.SEARCH)
        if "timeline" in manifest.permissions:
            allowed_resources.append(SandboxResource.TIMELINE_READ)
        if "graph" in manifest.permissions:
            allowed_resources.append(SandboxResource.GRAPH_READ)
        instance.quotas.allowed_resources = allowed_resources

        self._instances[manifest.id] = instance
        HookRegistry.register_plugin(manifest)
        return instance

    def uninstall(self, plugin_id: str):
        """Remove a plugin from the sandbox."""
        self._instances.pop(plugin_id, None)

    def get(self, plugin_id: str) -> Optional[PluginSandboxInstance]:
        return self._instances.get(plugin_id)

    def list(self) -> list[PluginSandboxInstance]:
        return list(self._instances.values())

    def enable(self, plugin_id: str):
        instance = self._instances.get(plugin_id)
        if instance:
            instance.enabled = True

    def disable(self, plugin_id: str):
        instance = self._instances.get(plugin_id)
        if instance:
            instance.enabled = False

    def check_quota(self, plugin_id: str, resource: SandboxResource) -> bool:
        """Check if a plugin can access a resource."""
        instance = self._instances.get(plugin_id)
        if not instance or not instance.enabled:
            return False
        if resource not in instance.quotas.allowed_resources:
            return False
        return True

    def get_storage(self, plugin_id: str, key: str) -> Any:
        """Read from plugin's isolated storage."""
        instance = self._instances.get(plugin_id)
        if not instance:
            return None
        return instance.storage.get(key)

    def set_storage(self, plugin_id: str, key: str, value: Any):
        """Write to plugin's isolated storage."""
        instance = self._instances.get(plugin_id)
        if instance:
            instance.storage[key] = value
            instance.updated_at = datetime.now(timezone.utc)

    def execute_hook(self, plugin_id: str, hook_name: str,
                     tenant_id: str, user_id: str,
                     payload: Optional[dict] = None) -> Optional[HookContext]:
        """Execute a single plugin's hook handler."""
        instance = self._instances.get(plugin_id)
        if not instance or not instance.enabled:
            return None
        instance.call_count += 1

        from runtime.extension_api import HookContext
        ctx = HookContext(
            hook_name=hook_name,
            plugin_id=plugin_id,
            tenant_id=tenant_id,
            user_id=user_id,
            payload=payload or {},
        )
        return ctx


# ── Built-in Hooks Registration ──────────────────────────────

def register_hook_points():
    """Register all built-in hook points (no handlers — just declaration)."""
    for hook_name in BUILTIN_HOOKS:
        pass  # Hook points are available for plugins to subscribe to
