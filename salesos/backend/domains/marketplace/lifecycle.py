"""Plugin lifecycle state machine.

States:  Install → Disable → Enable → Active → Uninstall
         Install → Active (auto-enable on install)
         Active → Disable (disable from active)
         Disable → Enable (enable from disabled)
         Any → Uninstall
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class PluginState(str, Enum):
    INSTALLED = "installed"
    DISABLED = "disabled"
    ENABLING = "enabling"
    ACTIVE = "active"
    UNINSTALLING = "uninstalling"
    UNINSTALLED = "uninstalled"


# Transition: (from_state, to_state) -> allowed
_ALLOWED_TRANSITIONS: dict[tuple[PluginState, PluginState], bool] = {
    (PluginState.INSTALLED, PluginState.ACTIVE): True,
    (PluginState.INSTALLED, PluginState.DISABLED): True,
    (PluginState.INSTALLED, PluginState.UNINSTALLING): True,
    (PluginState.ACTIVE, PluginState.DISABLED): True,
    (PluginState.ACTIVE, PluginState.UNINSTALLING): True,
    (PluginState.ACTIVE, PluginState.UNINSTALLED): True,
    (PluginState.DISABLED, PluginState.ACTIVE): True,
    (PluginState.DISABLED, PluginState.ENABLING): True,
    (PluginState.DISABLED, PluginState.UNINSTALLING): True,
    (PluginState.DISABLED, PluginState.UNINSTALLED): True,
    (PluginState.ENABLING, PluginState.ACTIVE): True,
    (PluginState.ENABLING, PluginState.DISABLED): True,
    (PluginState.UNINSTALLING, PluginState.UNINSTALLED): True,
}


@dataclass
class PluginLifecycleEvent:
    plugin_id: str
    from_state: PluginState | None
    to_state: PluginState
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "plugin_id": self.plugin_id,
            "from_state": self.from_state.value if self.from_state else None,
            "to_state": self.to_state.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


HookType = Callable[[str, dict], None]


class PluginLifecycle:
    """Manages plugin state transitions and lifecycle hooks."""

    def __init__(self):
        self._states: dict[str, PluginState] = {}
        self._history: list[PluginLifecycleEvent] = []
        self._hooks: dict[str, list[HookType]] = {
            "on_install": [],
            "on_enable": [],
            "on_disable": [],
            "on_uninstall": [],
        }

    # ── Lifecycle Hooks ──────────────────────────────────────

    def on_install(self, handler: HookType):
        self._hooks["on_install"].append(handler)

    def on_enable(self, handler: HookType):
        self._hooks["on_enable"].append(handler)

    def on_disable(self, handler: HookType):
        self._hooks["on_disable"].append(handler)

    def on_uninstall(self, handler: HookType):
        self._hooks["on_uninstall"].append(handler)

    def _run_hooks(self, hook_name: str, plugin_id: str, metadata: dict):
        for handler in self._hooks.get(hook_name, []):
            try:
                handler(plugin_id, metadata)
            except Exception:
                pass

    # ── State Management ─────────────────────────────────────

    def get_state(self, plugin_id: str) -> PluginState | None:
        return self._states.get(plugin_id)

    def initialize(self, plugin_id: str, auto_enable: bool = True) -> PluginLifecycleEvent:
        """Register a plugin after install. If auto_enable, goes to ACTIVE."""
        target = PluginState.ACTIVE if auto_enable else PluginState.DISABLED
        self._states[plugin_id] = target
        event = PluginLifecycleEvent(
            plugin_id=plugin_id,
            from_state=PluginState.INSTALLED,
            to_state=target,
            metadata={"auto_enable": auto_enable},
        )
        self._history.append(event)
        if target == PluginState.ACTIVE:
            self._run_hooks("on_enable", plugin_id, {"auto_enable": True})
        return event

    def transition(self, plugin_id: str, to_state: PluginState, metadata: dict | None = None) -> PluginLifecycleEvent:
        """Attempt a state transition. Raises ValueError if not allowed."""
        current = self._states.get(plugin_id)
        if current is None:
            raise ValueError(f"Plugin '{plugin_id}' is not installed")

        key = (current, to_state)

        if key not in _ALLOWED_TRANSITIONS or not _ALLOWED_TRANSITIONS[key]:
            raise ValueError(
                f"Invalid transition: {current.value} → {to_state.value} for plugin '{plugin_id}'"
            )

        self._states[plugin_id] = to_state
        event = PluginLifecycleEvent(
            plugin_id=plugin_id,
            from_state=current,
            to_state=to_state,
            metadata=metadata or {},
        )
        self._history.append(event)

        # Fire lifecycle hooks
        if to_state == PluginState.ACTIVE:
            self._run_hooks("on_enable", plugin_id, metadata or {})
        elif to_state == PluginState.DISABLED:
            self._run_hooks("on_disable", plugin_id, metadata or {})

        return event

    def activate(self, plugin_id: str, metadata: dict | None = None) -> PluginLifecycleEvent:
        return self.transition(plugin_id, PluginState.ACTIVE, metadata)

    def disable(self, plugin_id: str, metadata: dict | None = None) -> PluginLifecycleEvent:
        return self.transition(plugin_id, PluginState.DISABLED, metadata)

    def begin_uninstall(self, plugin_id: str, metadata: dict | None = None) -> PluginLifecycleEvent:
        return self.transition(plugin_id, PluginState.UNINSTALLING, metadata)

    def complete_uninstall(self, plugin_id: str, metadata: dict | None = None) -> PluginLifecycleEvent:
        event = self.transition(plugin_id, PluginState.UNINSTALLED, metadata)
        self._run_hooks("on_uninstall", plugin_id, metadata or {})
        self._states.pop(plugin_id, None)
        return event

    def history(self, plugin_id: str | None = None) -> list[PluginLifecycleEvent]:
        if plugin_id:
            return [e for e in self._history if e.plugin_id == plugin_id]
        return list(self._history)

    def list_active(self) -> list[str]:
        return [pid for pid, s in self._states.items() if s == PluginState.ACTIVE]

    def is_active(self, plugin_id: str) -> bool:
        return self._states.get(plugin_id) == PluginState.ACTIVE

    def is_installed(self, plugin_id: str) -> bool:
        return plugin_id in self._states
