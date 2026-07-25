"""Tests for plugin registry."""

import pytest

from domains.marketplace.registry import PluginRegistry


SLACK_MANIFEST = {
    "id": "salesos-slack",
    "name": "Slack Integration",
    "version": "1.0.0",
    "description": "Send notifications to Slack",
    "author": "SalesOS",
    "permissions": ["notifications", "webhooks"],
    "hooks": ["after.decision.evaluated"],
}

SALESFORCE_MANIFEST = {
    "id": "salesos-salesforce",
    "name": "Salesforce Connector",
    "version": "1.0.0",
    "description": "Sync with Salesforce",
    "author": "SalesOS",
    "permissions": ["company:read", "company:write", "contact:read", "contact:write"],
    "hooks": ["after.company.created", "after.company.updated"],
}


class TestPluginRegistry:
    def setup_method(self):
        self.registry = PluginRegistry()

    def test_install_plugin(self):
        plugin = self.registry.install(SLACK_MANIFEST)
        assert plugin.plugin_id == "salesos-slack"
        assert plugin.manifest.name == "Slack Integration"
        assert self.registry.count() == 1

    def test_install_multiple(self):
        self.registry.install(SLACK_MANIFEST)
        self.registry.install(SALESFORCE_MANIFEST)
        assert self.registry.count() == 2

    def test_install_duplicate_raises(self):
        self.registry.install(SLACK_MANIFEST)
        with pytest.raises(ValueError, match="already installed"):
            self.registry.install(SLACK_MANIFEST)

    def test_install_invalid_manifest_raises(self):
        with pytest.raises(ValueError, match="Manifest validation failed"):
            self.registry.install({"id": "bad", "name": "Bad"})

    def test_uninstall_plugin(self):
        self.registry.install(SLACK_MANIFEST)
        self.registry.uninstall("salesos-slack")
        assert self.registry.count() == 0
        assert self.registry.get("salesos-slack") is None

    def test_uninstall_nonexistent_raises(self):
        with pytest.raises(ValueError, match="not installed"):
            self.registry.uninstall("nonexistent")

    def test_get_plugin(self):
        self.registry.install(SLACK_MANIFEST)
        plugin = self.registry.get("salesos-slack")
        assert plugin is not None
        assert plugin.plugin_id == "salesos-slack"

    def test_get_nonexistent(self):
        assert self.registry.get("nonexistent") is None

    def test_list_plugins(self):
        self.registry.install(SLACK_MANIFEST)
        self.registry.install(SALESFORCE_MANIFEST)
        plugins = self.registry.list()
        assert len(plugins) == 2

    def test_update_config(self):
        self.registry.install(SLACK_MANIFEST)
        plugin = self.registry.update_config("salesos-slack", {"webhook_url": "https://hooks.slack.com/test"})
        assert plugin.config["webhook_url"] == "https://hooks.slack.com/test"

    def test_update_config_nonexistent(self):
        with pytest.raises(ValueError, match="not installed"):
            self.registry.update_config("nonexistent", {})

    def test_activate_and_disable(self):
        self.registry.install(SLACK_MANIFEST)
        assert self.registry.is_active("salesos-slack") is True
        self.registry.disable("salesos-slack")
        assert self.registry.is_active("salesos-slack") is False
        self.registry.activate("salesos-slack")
        assert self.registry.is_active("salesos-slack") is True

    def test_install_with_config(self):
        plugin = self.registry.install(SLACK_MANIFEST, {"webhook_url": "https://hooks.slack.com/test"})
        assert plugin.config["webhook_url"] == "https://hooks.slack.com/test"

    def test_lifecycle_accessible(self):
        assert self.registry.lifecycle is not None
        self.registry.install(SLACK_MANIFEST)
        assert self.registry.lifecycle.is_active("salesos-slack")
