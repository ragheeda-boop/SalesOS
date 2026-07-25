"""Tests for manifest schema validation."""

import pytest

from domains.marketplace.manifest_schema import (
    PluginManifest,
    check_import_restrictions,
    validate_manifest,
)


class TestManifestValidation:
    def test_valid_manifest(self):
        data = {
            "id": "test-plugin",
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "SalesOS",
        }
        errors = validate_manifest(data)
        assert errors == []

    def test_missing_required_field(self):
        data = {
            "id": "test-plugin",
            "name": "Test Plugin",
            "version": "1.0.0",
        }
        errors = validate_manifest(data)
        assert len(errors) > 0
        assert "description" in errors[0] or "Schema validation" in errors[0]

    def test_invalid_version_format(self):
        data = {
            "id": "test-plugin",
            "name": "Test Plugin",
            "version": "abc",
            "description": "A test plugin",
            "author": "SalesOS",
        }
        errors = validate_manifest(data)
        assert len(errors) > 0

    def test_invalid_plugin_id(self):
        data = {
            "id": "ab",
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "SalesOS",
        }
        errors = validate_manifest(data)
        assert len(errors) > 0

    def test_valid_with_all_fields(self):
        data = {
            "id": "my-plugin-v2",
            "name": "My Plugin V2",
            "version": "2.1.0",
            "description": "A comprehensive plugin with all fields",
            "author": "SalesOS Team",
            "license": "Apache-2.0",
            "icon": "https://example.com/icon.svg",
            "tags": ["analytics", "dashboard"],
            "permissions": ["search", "timeline", "graph"],
            "hooks": ["after.company.created", "after.company.updated"],
            "dependencies": [],
            "config_schema": {"type": "object", "properties": {}},
            "resource_limits": {"max_calls_per_sec": 50, "max_memory_mb": 100},
        }
        errors = validate_manifest(data)
        assert errors == []

    def test_invalid_permission(self):
        data = {
            "id": "test-plugin",
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "SalesOS",
            "permissions": ["invalid_permission_xyz"],
        }
        errors = validate_manifest(data)
        assert len(errors) > 0

    def test_duplicate_dependencies(self):
        data = {
            "id": "test-plugin",
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "SalesOS",
            "dependencies": ["dep-a", "dep-a"],
        }
        errors = validate_manifest(data)
        assert any("duplicate" in e.lower() for e in errors)

    def test_timeout_exceeds_limit(self):
        data = {
            "id": "test-plugin",
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "SalesOS",
            "resource_limits": {"max_timeout_ms": 60000},
        }
        errors = validate_manifest(data)
        assert len(errors) > 0

    def test_manifest_from_dataclass(self):
        manifest = PluginManifest(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="SalesOS",
        )
        d = manifest.to_dict()
        assert d["id"] == "test-plugin"
        assert d["name"] == "Test Plugin"
        assert d["version"] == "1.0.0"


class TestImportRestrictions:
    def test_allowed_imports(self):
        code = """
import json
import math
from datetime import datetime
from sdk.plugin_sdk import PluginManifest
"""
        errors = check_import_restrictions(code)
        assert errors == []

    def test_disallowed_import(self):
        code = """
import os
import json
"""
        errors = check_import_restrictions(code)
        assert len(errors) == 1
        assert "os" in errors[0]

    def test_disallowed_from_import(self):
        code = """
from flask import Flask
from datetime import datetime
"""
        errors = check_import_restrictions(code)
        assert len(errors) == 1
        assert "flask" in errors[0].lower()

    def test_relative_import_deep(self):
        code = """
from ...something import x
"""
        errors = check_import_restrictions(code)
        assert len(errors) == 2
        assert "relative import" in errors[0].lower()
        assert "not in the allowed module whitelist" in errors[1].lower()

    def test_syntax_error(self):
        code = "this is not valid python @@@"
        errors = check_import_restrictions(code)
        assert len(errors) > 0

    def test_empty_code(self):
        errors = check_import_restrictions("")
        assert errors == []

    def test_multiple_disallowed(self):
        code = """
import os
import sys
import subprocess
"""
        errors = check_import_restrictions(code)
        assert len(errors) == 3


class TestManifestFromDict:
    def test_from_dict_roundtrip(self):
        data = {
            "id": "test-plugin",
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "SalesOS",
            "license": "MIT",
            "tags": ["test"],
            "permissions": ["search"],
        }
        manifest = PluginManifest.from_dict(data)
        assert manifest.id == "test-plugin"
        assert manifest.name == "Test Plugin"
        assert manifest.permissions == ["search"]
        assert manifest.tags == ["test"]

    def test_from_dict_ignores_extra(self):
        data = {
            "id": "test-plugin",
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "SalesOS",
            "unknown_field": "should be ignored",
        }
        manifest = PluginManifest.from_dict(data)
        assert manifest.id == "test-plugin"
