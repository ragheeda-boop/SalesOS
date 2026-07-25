"""Plugin registry — store of installed plugins with manifest validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from domains.marketplace.lifecycle import PluginLifecycle
from domains.marketplace.manifest_schema import PluginManifest, validate_manifest


@dataclass
class InstalledPlugin:
    plugin_id: str
    manifest: PluginManifest
    config: dict = field(default_factory=dict)
    installed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "manifest": self.manifest.to_dict(),
            "config": self.config,
            "installed_at": self.installed_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class PluginRegistry:
    """Registry of all installed plugins with deduplication and validation."""

    def __init__(self):
        self._plugins: dict[str, InstalledPlugin] = {}
        self._lifecycle = PluginLifecycle()

    @property
    def lifecycle(self) -> PluginLifecycle:
        return self._lifecycle

    def install(self, manifest_data: dict, config: dict | None = None) -> InstalledPlugin:
        """Validate manifest and install a plugin. Returns the installed plugin."""
        errors = validate_manifest(manifest_data)
        if errors:
            raise ValueError(f"Manifest validation failed: {'; '.join(errors)}")

        plugin_id = manifest_data["id"]
        if plugin_id in self._plugins:
            raise ValueError(f"Plugin '{plugin_id}' is already installed")

        manifest = PluginManifest.from_dict(manifest_data)
        plugin = InstalledPlugin(
            plugin_id=plugin_id,
            manifest=manifest,
            config=config or {},
        )
        self._plugins[plugin_id] = plugin
        self._lifecycle.initialize(plugin_id)
        return plugin

    def uninstall(self, plugin_id: str) -> None:
        """Uninstall a plugin."""
        if plugin_id not in self._plugins:
            raise ValueError(f"Plugin '{plugin_id}' is not installed")
        self._lifecycle.complete_uninstall(plugin_id)
        del self._plugins[plugin_id]

    def get(self, plugin_id: str) -> InstalledPlugin | None:
        return self._plugins.get(plugin_id)

    def list(self) -> list[InstalledPlugin]:
        return list(self._plugins.values())

    def update_config(self, plugin_id: str, config: dict) -> InstalledPlugin:
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_id}' is not installed")
        plugin.config = config
        plugin.updated_at = datetime.now(timezone.utc)
        return plugin

    def activate(self, plugin_id: str) -> None:
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_id}' is not installed")
        self._lifecycle.activate(plugin_id)

    def disable(self, plugin_id: str) -> None:
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_id}' is not installed")
        self._lifecycle.disable(plugin_id)

    def is_active(self, plugin_id: str) -> bool:
        return self._lifecycle.is_active(plugin_id)

    def count(self) -> int:
        return len(self._plugins)
