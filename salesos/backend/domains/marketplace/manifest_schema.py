"""Plugin manifest schema and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import jsonschema


MANIFEST_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["id", "name", "version", "description", "author"],
    "properties": {
        "id": {"type": "string", "pattern": r"^[a-zA-Z][a-zA-Z0-9_-]{2,63}$"},
        "name": {"type": "string", "minLength": 1, "maxLength": 128},
        "version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"},
        "description": {"type": "string", "maxLength": 2000},
        "author": {"type": "string", "minLength": 1, "maxLength": 128},
        "license": {"type": "string", "default": "MIT"},
        "icon": {"type": "string", "format": "uri", "maxLength": 512},
        "tags": {"type": "array", "items": {"type": "string", "maxLength": 32}},
        "permissions": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "search", "timeline", "graph", "storage",
                    "notifications", "webhooks", "ai:query",
                    "company:read", "company:write",
                    "contact:read", "contact:write",
                    "decision:read", "decision:write",
                ],
            },
        },
        "hooks": {
            "type": "array",
            "items": {"type": "string", "maxLength": 128},
        },
        "widgets": {
            "type": "array",
            "items": {"type": "string", "maxLength": 128},
        },
        "dependencies": {
            "type": "array",
            "items": {"type": "string"},
        },
        "config_schema": {
            "type": "object",
            "description": "JSON Schema for plugin-level configuration",
        },
        "resource_limits": {
            "type": "object",
            "properties": {
                "max_calls_per_sec": {"type": "integer", "minimum": 1, "default": 100},
                "max_memory_mb": {"type": "integer", "minimum": 1, "default": 50},
                "max_timeout_ms": {"type": "integer", "minimum": 100, "default": 5000},
            },
        },
    },
}


ALLOWED_IMPORT_MODULES: set[str] = {
    "json", "math", "datetime", "typing", "uuid", "re",
    "dataclasses", "enum", "collections", "itertools",
    "sdk.plugin_sdk",
    "runtime.extension_api",
    "runtime.plugin_sandbox",
}


@dataclass
class PluginManifest:
    id: str
    name: str
    version: str
    description: str
    author: str
    license: str = "MIT"
    icon: str | None = None
    tags: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    hooks: list[str] = field(default_factory=list)
    widgets: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    config_schema: dict | None = None
    resource_limits: dict = field(default_factory=lambda: {
        "max_calls_per_sec": 100,
        "max_memory_mb": 50,
        "max_timeout_ms": 5000,
    })

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "icon": self.icon,
            "tags": self.tags,
            "permissions": self.permissions,
            "hooks": self.hooks,
            "widgets": self.widgets,
            "dependencies": self.dependencies,
            "config_schema": self.config_schema,
            "resource_limits": self.resource_limits,
        }

    @classmethod
    def from_dict(cls, data: dict) -> PluginManifest:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def validate_manifest(manifest_data: dict) -> list[str]:
    """Validate manifest against JSON schema. Returns list of errors (empty = valid)."""
    errors: list[str] = []
    try:
        jsonschema.validate(instance=manifest_data, schema=MANIFEST_JSON_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        errors.append(f"Schema validation failed: {e.message}")
        return errors

    # Check dependency resolution
    deps = manifest_data.get("dependencies", [])
    if len(deps) != len(set(deps)):
        errors.append("Duplicate dependencies found")

    # Check resource limits
    limits = manifest_data.get("resource_limits", {})
    if limits.get("max_timeout_ms", 5000) > 30000:
        errors.append("max_timeout_ms cannot exceed 30000")

    return errors


def check_import_restrictions(source_code: str) -> list[str]:
    """Check plugin source code against import whitelist.

    Backend plugins can only import from ALLOWED_IMPORT_MODULES.
    Wildcard imports and relative imports beyond one level are forbidden.
    """
    import ast
    errors: list[str] = []

    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        errors.append(f"Syntax error in plugin source: {e}")
        return errors

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if alias.name not in ALLOWED_IMPORT_MODULES and top not in ALLOWED_IMPORT_MODULES:
                    errors.append(f"Import '{alias.name}' is not in the allowed module whitelist")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level and node.level > 1:
                errors.append(f"Relative imports beyond one level are forbidden: {'.' * node.level}{node.module}")
            if node.module:
                top = node.module.split(".")[0]
                if node.module not in ALLOWED_IMPORT_MODULES and top not in ALLOWED_IMPORT_MODULES:
                    errors.append(f"Import from '{node.module}' is not in the allowed module whitelist")

    return errors
