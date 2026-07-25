"""Tests for plugin sandboxing — widget iframe isolation and permission gate."""

from domains.marketplace.manifest_schema import PluginManifest
from domains.marketplace.sandbox import (
    BackendPluginSandbox,
    PermissionGate,
    WidgetSandbox,
)


class TestWidgetSandbox:
    def test_render_widget_generates_html(self):
        manifest = PluginManifest(
            id="test-widget",
            name="Test Widget",
            version="1.0.0",
            description="A test widget",
            author="SalesOS",
            permissions=[],
        )
        sandbox = WidgetSandbox(allowed_origin="http://localhost:3000")
        widget = sandbox.render_widget(
            plugin_id="test-widget",
            manifest=manifest,
            config={"color": "blue"},
            plugin_code='document.getElementById("plugin-root").innerHTML = "<h1>Hello</h1>";',
        )
        assert widget.plugin_id == "test-widget"
        assert "test-widget" in widget.html_content
        assert "plugin-root" in widget.html_content
        assert "postMessage" in widget.html_content
        assert "CSP" in widget.html_content or "Content-Security-Policy" in widget.html_content

    def test_render_widget_no_code(self):
        manifest = PluginManifest(
            id="empty-widget",
            name="Empty Widget",
            version="1.0.0",
            description="An empty widget",
            author="SalesOS",
        )
        sandbox = WidgetSandbox()
        widget = sandbox.render_widget("empty-widget", manifest)
        assert widget.plugin_id == "empty-widget"


class TestBackendPluginSandbox:
    def test_safe_code(self):
        sandbox = BackendPluginSandbox()
        code = """
import json
from datetime import datetime
from sdk.plugin_sdk import PluginManifest
"""
        assert sandbox.is_code_safe(code)

    def test_unsafe_code(self):
        sandbox = BackendPluginSandbox()
        code = """
import os
import subprocess
"""
        assert not sandbox.is_code_safe(code)
        errors = sandbox.validate_source(code)
        assert len(errors) == 2

    def test_empty_code(self):
        sandbox = BackendPluginSandbox()
        assert sandbox.is_code_safe("")

    def test_invalid_syntax(self):
        sandbox = BackendPluginSandbox()
        errors = sandbox.validate_source("not valid python @@@")
        assert len(errors) > 0


class TestPermissionGate:
    def setup_method(self):
        self.gate = PermissionGate()

    def test_get_required_permissions(self):
        manifest = PluginManifest(
            id="test", name="Test", version="1.0.0",
            description="", author="SalesOS",
            permissions=["search", "timeline", "graph"],
        )
        perms = self.gate.get_required_permissions(manifest)
        assert perms == ["search", "timeline", "graph"]

    def test_approve_and_check(self):
        self.gate.approve("plugin-1", ["search", "timeline"])
        assert self.gate.is_approved("plugin-1", "search")
        assert self.gate.is_approved("plugin-1", "timeline")
        assert not self.gate.is_approved("plugin-1", "graph")

    def test_revoke_permission(self):
        self.gate.approve("plugin-1", ["search", "timeline"])
        self.gate.revoke("plugin-1", "search")
        assert not self.gate.is_approved("plugin-1", "search")
        assert self.gate.is_approved("plugin-1", "timeline")

    def test_has_all_permissions(self):
        manifest = PluginManifest(
            id="test", name="Test", version="1.0.0",
            description="", author="SalesOS",
            permissions=["search", "timeline"],
        )
        assert not self.gate.has_all_permissions("test", manifest)
        self.gate.approve("test", ["search", "timeline"])
        assert self.gate.has_all_permissions("test", manifest)

    def test_list_approved(self):
        self.gate.approve("plugin-1", ["search", "graph"])
        approved = self.gate.list_approved("plugin-1")
        assert "search" in approved
        assert "graph" in approved
        assert "timeline" not in approved

    def test_revoke_nonexistent(self):
        self.gate.approve("plugin-1", ["search"])
        self.gate.revoke("plugin-1", "nonexistent")
        assert self.gate.is_approved("plugin-1", "search")
