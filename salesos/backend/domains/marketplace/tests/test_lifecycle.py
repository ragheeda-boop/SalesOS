"""Tests for plugin lifecycle state machine."""

import pytest

from domains.marketplace.lifecycle import PluginLifecycle, PluginState


class TestPluginLifecycle:
    def setup_method(self):
        self.lifecycle = PluginLifecycle()

    def test_initial_state_is_none(self):
        assert self.lifecycle.get_state("nonexistent") is None

    def test_initialize_goes_to_active(self):
        event = self.lifecycle.initialize("plugin-1")
        assert event.to_state == PluginState.ACTIVE
        assert self.lifecycle.get_state("plugin-1") == PluginState.ACTIVE

    def test_initialize_without_auto_enable(self):
        event = self.lifecycle.initialize("plugin-1", auto_enable=False)
        assert event.to_state == PluginState.DISABLED
        assert self.lifecycle.get_state("plugin-1") == PluginState.DISABLED

    def test_activate_from_installed(self):
        self.lifecycle.initialize("plugin-1", auto_enable=False)
        event = self.lifecycle.activate("plugin-1")
        assert event.to_state == PluginState.ACTIVE

    def test_disable_active_plugin(self):
        self.lifecycle.initialize("plugin-1")
        event = self.lifecycle.disable("plugin-1")
        assert event.to_state == PluginState.DISABLED
        assert self.lifecycle.get_state("plugin-1") == PluginState.DISABLED

    def test_enable_from_disabled(self):
        self.lifecycle.initialize("plugin-1", auto_enable=False)
        event = self.lifecycle.activate("plugin-1")
        assert event.to_state == PluginState.ACTIVE

    def test_uninstall_from_active(self):
        self.lifecycle.initialize("plugin-1")
        event = self.lifecycle.begin_uninstall("plugin-1")
        assert event.to_state == PluginState.UNINSTALLING

        event = self.lifecycle.complete_uninstall("plugin-1")
        assert event.to_state == PluginState.UNINSTALLED
        assert self.lifecycle.get_state("plugin-1") is None

    def test_invalid_transition_raises(self):
        self.lifecycle.initialize("plugin-1")
        with pytest.raises(ValueError, match="Invalid transition"):
            self.lifecycle.transition("plugin-1", PluginState.INSTALLED)

    def test_invalid_transition_from_nonexistent(self):
        with pytest.raises(ValueError, match="not installed"):
            self.lifecycle.transition("nonexistent", PluginState.ACTIVE)

    def test_history_records_events(self):
        self.lifecycle.initialize("plugin-1")
        self.lifecycle.disable("plugin-1")
        self.lifecycle.activate("plugin-1")

        history = self.lifecycle.history("plugin-1")
        assert len(history) == 3

    def test_history_all(self):
        self.lifecycle.initialize("plugin-1")
        self.lifecycle.initialize("plugin-2")
        assert len(self.lifecycle.history()) == 2

    def test_list_active(self):
        self.lifecycle.initialize("plugin-1")
        self.lifecycle.initialize("plugin-2", auto_enable=False)
        active = self.lifecycle.list_active()
        assert "plugin-1" in active
        assert "plugin-2" not in active

    def test_is_active(self):
        self.lifecycle.initialize("plugin-1")
        assert self.lifecycle.is_active("plugin-1") is True
        self.lifecycle.disable("plugin-1")
        assert self.lifecycle.is_active("plugin-1") is False

    def test_is_installed(self):
        assert self.lifecycle.is_installed("plugin-1") is False
        self.lifecycle.initialize("plugin-1")
        assert self.lifecycle.is_installed("plugin-1") is True

    def test_lifecycle_hooks_fired(self):
        hooks = {"on_enable": [], "on_disable": [], "on_uninstall": []}

        def track_enable(pid, meta):
            hooks["on_enable"].append(pid)

        def track_disable(pid, meta):
            hooks["on_disable"].append(pid)

        def track_uninstall(pid, meta):
            hooks["on_uninstall"].append(pid)

        self.lifecycle.on_enable(track_enable)
        self.lifecycle.on_disable(track_disable)
        self.lifecycle.on_uninstall(track_uninstall)

        self.lifecycle.initialize("plugin-1")
        assert "plugin-1" in hooks["on_enable"]

        self.lifecycle.disable("plugin-1")
        assert "plugin-1" in hooks["on_disable"]

        self.lifecycle.begin_uninstall("plugin-1")
        self.lifecycle.complete_uninstall("plugin-1")
        assert "plugin-1" in hooks["on_uninstall"]

    def test_hooks_do_not_block_on_exception(self):
        def failing_hook(pid, meta):
            raise RuntimeError("hook failed")

        self.lifecycle.on_enable(failing_hook)
        # Should not raise
        self.lifecycle.initialize("plugin-1")
        assert self.lifecycle.is_active("plugin-1")
