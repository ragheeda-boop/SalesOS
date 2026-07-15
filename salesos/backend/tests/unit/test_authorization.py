import pytest

from sdk.permissions import (
    Permission,
    PermissionAction,
    PermissionEnforcer,
    PermissionRegistry,
    Role,
)
from sdk.exceptions import PermissionDeniedError


class TestRoleHierarchy:
    def setup_method(self):
        PermissionRegistry._permissions.clear()
        PermissionRegistry._roles.clear()

    def test_admin_has_all_permissions(self):
        roles = PermissionRegistry.default_roles()
        admin_perms = roles.get("admin", [])
        assert any(p.resource == "company" and p.action == PermissionAction.DELETE for p in admin_perms)
        assert any(p.resource == "monitoring" and p.action == PermissionAction.ADMIN for p in admin_perms)
        assert any(p.resource == "billing" and p.action == PermissionAction.EXPORT for p in admin_perms)

    def test_manager_permissions_correct(self):
        roles = PermissionRegistry.default_roles()
        manager_perms = roles.get("manager", [])
        assert Permission("company", PermissionAction.CREATE) in manager_perms
        assert Permission("company", PermissionAction.READ) in manager_perms
        assert Permission("company", PermissionAction.UPDATE) in manager_perms
        assert Permission("company", PermissionAction.DELETE) not in manager_perms
        assert Permission("pipeline", PermissionAction.READ) in manager_perms
        assert Permission("pipeline", PermissionAction.UPDATE) in manager_perms

    def test_user_permissions_correct(self):
        roles = PermissionRegistry.default_roles()
        user_perms = roles.get("user", [])
        assert Permission("company", PermissionAction.READ) in user_perms
        assert Permission("company", PermissionAction.CREATE) not in user_perms
        assert Permission("company", PermissionAction.UPDATE) not in user_perms
        assert Permission("opportunity", PermissionAction.CREATE) in user_perms
        assert Permission("opportunity", PermissionAction.READ) in user_perms
        assert Permission("opportunity", PermissionAction.UPDATE) in user_perms

    def test_api_role_limited_permissions(self):
        roles = PermissionRegistry.default_roles()
        api_perms = roles.get("api", [])
        assert Permission("company", PermissionAction.READ) in api_perms
        assert Permission("company", PermissionAction.CREATE) in api_perms
        assert Permission("contact", PermissionAction.READ) in api_perms
        assert Permission("opportunity", PermissionAction.READ) not in api_perms
        assert Permission("user", PermissionAction.READ) not in api_perms

    def test_auditor_role_read_only(self):
        roles = PermissionRegistry.default_roles()
        auditor_perms = roles.get("auditor", [])
        assert Permission("company", PermissionAction.READ) in auditor_perms
        assert Permission("audit", PermissionAction.READ) in auditor_perms
        assert Permission("company", PermissionAction.CREATE) not in auditor_perms
        assert Permission("contact", PermissionAction.READ) not in auditor_perms


class TestPermissionRegistry:
    def setup_method(self):
        PermissionRegistry._permissions.clear()
        PermissionRegistry._roles.clear()

    def test_register_and_check_permission(self):
        perm = Permission("test_resource", PermissionAction.READ)
        PermissionRegistry.register(perm)
        role = Role("tester", permissions={perm})
        PermissionRegistry.register_role(role)
        assert PermissionRegistry.has_permission("tester", "test_resource", PermissionAction.READ)
        assert not PermissionRegistry.has_permission("tester", "test_resource", PermissionAction.CREATE)

    def test_register_module_permissions(self):
        PermissionRegistry.register_module_permissions("my_module", [PermissionAction.READ, PermissionAction.CREATE])
        assert PermissionRegistry._permissions.get("my_module.read") is not None
        assert PermissionRegistry._permissions.get("my_module.create") is not None
        assert PermissionRegistry._permissions.get("my_module.delete") is None

    def test_unknown_role_returns_false(self):
        assert not PermissionRegistry.has_permission("nonexistent", "company", PermissionAction.READ)


class TestPermissionEnforcer:
    def setup_method(self):
        PermissionRegistry._permissions.clear()
        PermissionRegistry._roles.clear()
        roles_data = PermissionRegistry.default_roles()
        for name, perms in roles_data.items():
            PermissionRegistry.register_role(Role(name, permissions=set(perms)))

    def test_admin_can_access_admin_resource(self):
        PermissionEnforcer.check("admin", "billing", PermissionAction.ADMIN)

    def test_admin_can_delete_company(self):
        PermissionEnforcer.check("admin", "company", PermissionAction.DELETE)

    def test_manager_can_create_company(self):
        PermissionEnforcer.check("manager", "company", PermissionAction.CREATE)

    def test_manager_cannot_delete_company(self):
        with pytest.raises(PermissionDeniedError):
            PermissionEnforcer.check("manager", "company", PermissionAction.DELETE)

    def test_user_cannot_create_company(self):
        with pytest.raises(PermissionDeniedError):
            PermissionEnforcer.check("user", "company", PermissionAction.CREATE)

    def test_user_can_read_company(self):
        PermissionEnforcer.check("user", "company", PermissionAction.READ)

    def test_auditor_cannot_create_company(self):
        with pytest.raises(PermissionDeniedError):
            PermissionEnforcer.check("auditor", "company", PermissionAction.CREATE)

    def test_auditor_can_read_audit(self):
        PermissionEnforcer.check("auditor", "audit", PermissionAction.READ)

    def test_api_role_can_create_company(self):
        PermissionEnforcer.check("api", "company", PermissionAction.CREATE)

    def test_api_role_cannot_delete_company(self):
        with pytest.raises(PermissionDeniedError):
            PermissionEnforcer.check("api", "company", PermissionAction.DELETE)

    def test_enforcer_with_string_action(self):
        PermissionEnforcer.check("admin", "company", "delete")
        with pytest.raises(PermissionDeniedError):
            PermissionEnforcer.check("user", "company", "delete")


class TestPermissionActionEnum:
    def test_all_actions_defined(self):
        expected = {"create", "read", "update", "delete", "export", "import", "admin"}
        actual = {a.value for a in PermissionAction}
        assert actual == expected

    def test_permission_key_format(self):
        perm = Permission("company", PermissionAction.CREATE)
        assert perm.key == "company.create"
        perm2 = Permission("monitoring", PermissionAction.ADMIN)
        assert perm2.key == "monitoring.admin"


class TestRolePermissionAttribute:
    def test_role_has_permission(self):
        role = Role(
            "test",
            permissions={
                Permission("resource_a", PermissionAction.READ),
                Permission("resource_b", PermissionAction.CREATE),
            },
        )
        assert role.has_permission("resource_a", PermissionAction.READ)
        assert role.has_permission("resource_b", PermissionAction.CREATE)
        assert not role.has_permission("resource_a", PermissionAction.CREATE)
        assert not role.has_permission("resource_c", PermissionAction.READ)

    def test_role_no_permissions(self):
        role = Role("empty")
        assert not role.has_permission("anything", PermissionAction.READ)
