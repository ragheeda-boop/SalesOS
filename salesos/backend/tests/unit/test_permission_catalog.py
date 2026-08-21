"""Tests for tenant_studio.permission_catalog — catalog validation, no DB."""

from __future__ import annotations

import pytest

from app.modules.tenant_studio.permission_catalog import (
    FORBIDDEN_PERMISSION_KEYS,
    STUDIO_PERMISSION_CATALOG,
    StudioPermissionDef,
    get_permission_def,
    list_catalog,
)


# ── list_catalog ─────────────────────────────────────────────────────────────


class TestListCatalog:
    def test_returns_all_permissions(self):
        catalog = list_catalog()
        assert len(catalog) == 10

    def test_returns_studio_permission_def_instances(self):
        for p in list_catalog():
            assert isinstance(p, StudioPermissionDef)

    def test_keys_are_unique(self):
        keys = [p.key for p in list_catalog()]
        assert len(keys) == len(set(keys))

    def test_all_domains_prefixed(self):
        for p in list_catalog():
            assert p.domain.startswith("DOM-"), f"{p.key} domain {p.domain} missing DOM- prefix"

    def test_groups_are_non_empty(self):
        for p in list_catalog():
            assert p.group, f"{p.key} has empty group"


# ── get_permission_def ───────────────────────────────────────────────────────


class TestGetPermissionDef:
    def test_valid_key(self):
        p = get_permission_def("crm.companies.read")
        assert p is not None
        assert p.key == "crm.companies.read"
        assert p.domain == "DOM-001"
        assert p.group == "crm"

    def test_unknown_key(self):
        assert get_permission_def("nonexistent.key") is None

    def test_strips_whitespace(self):
        p = get_permission_def("  ai.rag.use  ")
        assert p is not None
        assert p.key == "ai.rag.use"

    def test_empty_string(self):
        assert get_permission_def("") is None


# ── StudioPermissionDef ─────────────────────────────────────────────────────


class TestStudioPermissionDef:
    def test_as_dict(self):
        p = StudioPermissionDef(
            key="test.key",
            name="Test",
            description="desc",
            domain="DOM-999",
            group="test",
            requires_publish=True,
        )
        d = p.as_dict()
        assert d["key"] == "test.key"
        assert d["requires_publish"] is True
        assert d["domain"] == "DOM-999"

    def test_frozen(self):
        p = StudioPermissionDef(
            key="k", name="n", description="d", domain="DOM-001"
        )
        with pytest.raises(AttributeError):
            p.key = "changed"


# ── FORBIDDEN_PERMISSION_KEYS ────────────────────────────────────────────────


class TestForbiddenKeys:
    def test_owner_keys_blocked(self):
        assert "owner.admin" in FORBIDDEN_PERMISSION_KEYS
        assert "owner.impersonate" in FORBIDDEN_PERMISSION_KEYS

    def test_wildcard_blocked(self):
        assert "*" in FORBIDDEN_PERMISSION_KEYS
        assert "all" in FORBIDDEN_PERMISSION_KEYS

    def test_admin_keys_blocked(self):
        assert "admin" in FORBIDDEN_PERMISSION_KEYS
        assert "manage_users" in FORBIDDEN_PERMISSION_KEYS
        assert "manage_billing" in FORBIDDEN_PERMISSION_KEYS
        assert "manage_plans" in FORBIDDEN_PERMISSION_KEYS
        assert "manage_roles" in FORBIDDEN_PERMISSION_KEYS

    def test_no_overlap_with_catalog(self):
        """Forbidden keys must not appear in the grantable catalog."""
        for key in FORBIDDEN_PERMISSION_KEYS:
            assert key not in STUDIO_PERMISSION_CATALOG, f"Forbidden key {key} in catalog"

    def test_count(self):
        assert len(FORBIDDEN_PERMISSION_KEYS) == 9


# ── Cross-cutting ────────────────────────────────────────────────────────────


class TestCrossCutting:
    def test_catalog_matches_dict(self):
        """list_catalog() order matches STUDIO_PERMISSION_CATALOG dict."""
        catalog_list = list_catalog()
        catalog_dict = STUDIO_PERMISSION_CATALOG
        assert len(catalog_list) == len(catalog_dict)
        for p in catalog_list:
            assert p.key in catalog_dict
            assert catalog_dict[p.key] is p
