"""Tests for tenant_studio.custom_roles — validation + serialization, no DB."""

from __future__ import annotations

import pytest

from app.modules.tenant_studio.custom_roles import (
    CustomRole,
    CustomRoleError,
    build_custom_role,
)


# ── build_custom_role ────────────────────────────────────────────────────────


class TestBuildCustomRoleSuccess:
    def test_valid_input(self):
        role = build_custom_role(
            tenant_id="t-123",
            name="Sales Manager",
            permissions=["crm.companies.read", "crm.opportunities.manage"],
        )
        assert role.tenant_id == "t-123"
        assert role.name == "Sales Manager"
        assert len(role.permissions) == 2
        assert role.schema_version == 1

    def test_with_description(self):
        role = build_custom_role(
            tenant_id="t-1",
            name="Role",
            permissions=["ai.rag.use"],
            description="A test role",
        )
        assert role.description == "A test role"

    def test_with_role_id(self):
        role = build_custom_role(
            tenant_id="t-1",
            name="Role",
            permissions=["k"],
            role_id="custom-42",
        )
        assert role.id == "custom-42"

    def test_strips_whitespace(self):
        role = build_custom_role(
            tenant_id="  t-1  ",
            name="  My Role  ",
            permissions=["k"],
        )
        assert role.tenant_id == "t-1"
        assert role.name == "My Role"

    def test_schema_version_floor(self):
        role = build_custom_role(
            tenant_id="t-1",
            name="R",
            permissions=["k"],
            schema_version=0,
        )
        assert role.schema_version == 1

    def test_permissions_copied(self):
        perms = ["a", "b"]
        role = build_custom_role(tenant_id="t-1", name="R", permissions=perms)
        perms.append("c")
        assert len(role.permissions) == 2


class TestBuildCustomRoleErrors:
    def test_empty_tenant_id(self):
        with pytest.raises(CustomRoleError, match="tenant_id required"):
            build_custom_role(tenant_id="", name="R", permissions=["k"])

    def test_whitespace_tenant_id(self):
        with pytest.raises(CustomRoleError, match="tenant_id required"):
            build_custom_role(tenant_id="   ", name="R", permissions=["k"])

    def test_none_tenant_id(self):
        with pytest.raises(CustomRoleError, match="tenant_id required"):
            build_custom_role(tenant_id=None, name="R", permissions=["k"])

    def test_empty_name(self):
        with pytest.raises(CustomRoleError, match="name required"):
            build_custom_role(tenant_id="t-1", name="", permissions=["k"])

    def test_whitespace_name(self):
        with pytest.raises(CustomRoleError, match="name required"):
            build_custom_role(tenant_id="t-1", name="  ", permissions=["k"])

    def test_empty_permissions(self):
        with pytest.raises(CustomRoleError, match="permissions required"):
            build_custom_role(tenant_id="t-1", name="R", permissions=[])


# ── CustomRole.as_dict ──────────────────────────────────────────────────────


class TestCustomRoleAsDict:
    def test_as_dict_roundtrip(self):
        role = build_custom_role(
            tenant_id="t-1",
            name="Analyst",
            permissions=["ai.rag.use", "gtm.signals.read"],
            description="Data analyst",
            role_id="cr-01",
        )
        d = role.as_dict()
        assert d["id"] == "cr-01"
        assert d["tenant_id"] == "t-1"
        assert d["name"] == "Analyst"
        assert d["description"] == "Data analyst"
        assert d["permissions"] == ["ai.rag.use", "gtm.signals.read"]
        assert d["schema_version"] == 1

    def test_permissions_is_copy(self):
        role = CustomRole(
            id="", tenant_id="", name="R", permissions=["x"]
        )
        d = role.as_dict()
        d["permissions"].append("y")
        assert len(role.permissions) == 1
