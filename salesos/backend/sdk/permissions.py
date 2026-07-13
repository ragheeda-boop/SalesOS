"""Permission registry and RBAC enforcer."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


class PermissionAction(Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    IMPORT = "import"
    ADMIN = "admin"


@dataclass(frozen=True)
class Permission:
    """A granular permission for a specific resource and action."""

    resource: str
    action: PermissionAction
    scope: str = "*"  # all, own, tenant

    @property
    def key(self) -> str:
        return f"{self.resource}.{self.action.value}"


@dataclass
class Role:
    """A named collection of permissions."""

    name: str
    permissions: set[Permission] = field(default_factory=set)

    def has_permission(self, resource: str, action: PermissionAction) -> bool:
        return any(
            p.resource == resource and p.action == action for p in self.permissions
        )


class PermissionRegistry:
    """Central registry for all permissions in the system.

    Each module registers its permissions on startup.
    """

    _permissions: dict[str, Permission] = {}
    _roles: dict[str, Role] = {}

    @classmethod
    def register(cls, permission: Permission) -> None:
        cls._permissions[permission.key] = permission

    @classmethod
    def register_role(cls, role: Role) -> None:
        cls._roles[role.name] = role

    @classmethod
    def get_role(cls, name: str) -> Role | None:
        return cls._roles.get(name)

    @classmethod
    def register_module_permissions(cls, module: str, actions: list[PermissionAction]) -> None:
        for action in actions:
            perm = Permission(resource=module, action=action)
            cls.register(perm)

    @classmethod
    def has_permission(cls, role_name: str, resource: str, action: PermissionAction) -> bool:
        role = cls._roles.get(role_name)
        if not role:
            return False
        return role.has_permission(resource, action)

    @classmethod
    def default_roles(cls) -> dict[str, list[Permission]]:
        return {
            "admin": [
                Permission(r, a)
                for r in ["company", "contact", "license", "opportunity", "pipeline", "user", "tenant", "settings", "billing", "audit", "api", "executive", "workflow", "employee", "entity-resolution", "search", "feature-store", "data-fabric", "knowledge-graph", "decision", "timeline", "monitoring", "customer-success", "work-intelligence", "employee-360"]
                for a in PermissionAction
            ],
            "manager": [
                Permission("company", PermissionAction.CREATE),
                Permission("company", PermissionAction.READ),
                Permission("company", PermissionAction.UPDATE),
                Permission("contact", PermissionAction.CREATE),
                Permission("contact", PermissionAction.READ),
                Permission("contact", PermissionAction.UPDATE),
                Permission("opportunity", PermissionAction.CREATE),
                Permission("opportunity", PermissionAction.READ),
                Permission("opportunity", PermissionAction.UPDATE),
                Permission("pipeline", PermissionAction.READ),
                Permission("pipeline", PermissionAction.UPDATE),
            ],
            "user": [
                Permission("company", PermissionAction.READ),
                Permission("contact", PermissionAction.READ),
                Permission("contact", PermissionAction.CREATE),
                Permission("opportunity", PermissionAction.CREATE),
                Permission("opportunity", PermissionAction.READ),
                Permission("opportunity", PermissionAction.UPDATE),
            ],
            "api": [
                Permission("company", PermissionAction.READ),
                Permission("company", PermissionAction.CREATE),
                Permission("contact", PermissionAction.READ),
            ],
            "auditor": [
                Permission("company", PermissionAction.READ),
                Permission("audit", PermissionAction.READ),
            ],
        }


class PermissionEnforcer:
    """Middleware-friendly permission enforcer."""

    @staticmethod
    def check(user_role: str, resource: str, action: PermissionAction) -> None:
        if not PermissionRegistry.has_permission(user_role, resource, action):
            from sdk.exceptions import PermissionDeniedError

            raise PermissionDeniedError(user_role, f"{resource}.{action.value}")
