"""Admin domain services: feature flag evaluation, tenant provisioning, config validation, audit CSV export."""  # noqa: E501

from __future__ import annotations

import csv
import io
from typing import Any, cast

import yaml  # type: ignore[import-untyped]
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import Tenant, User

from .db_models import (
    PermissionModel,
    RoleModel,
    TenantConfigModel,
)
from .pg_repositories import (
    PostgresFeatureFlagRepository,
    PostgresPermissionRepository,
    PostgresRoleRepository,
    PostgresTenantConfigRepository,
)


class FeatureFlagService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PostgresFeatureFlagRepository(session)

    async def is_enabled(self, flag_key: str, tenant_id: str) -> dict[str, Any]:
        from sqlalchemy import select as sa_select

        result = await self.session.execute(sa_select(Tenant.id))
        all_tenant_ids = [str(row[0]) for row in result]
        return await self.repo.evaluate(flag_key, tenant_id, all_tenant_ids)

    async def create_ci_test_flag(self, key: str, name: str, description: str = "") -> dict:
        from .db_models import FeatureFlagModel

        flag = FeatureFlagModel(
            key=key,
            name=name,
            description=description,
            enabled=True,
            is_ci_test=True,
            rollout_percentage=100,
        )
        self.session.add(flag)
        await self.session.flush()
        return {
            "id": str(flag.id),
            "key": flag.key,
            "name": flag.name,
            "enabled": True,
            "is_ci_test": True,
        }


class TenantProvisioningService:
    """Handles tenant creation with default roles, permissions, and admin user."""

    DEFAULT_ROLES = [
        {
            "id": "role_admin",
            "name": "Admin",
            "description": "Full system access",
            "permissions": [
                "admin",
                "manage_users",
                "manage_billing",
                "manage_plans",
                "manage_roles",
            ],
            "is_system": True,
        },
        {
            "id": "role_manager",
            "name": "Sales Manager",
            "description": "Manage sales team and pipeline",
            "permissions": [
                "read_companies",
                "read_contacts",
                "manage_opportunities",
                "manage_tasks",
                "reports",
            ],
            "is_system": False,
        },
        {
            "id": "role_rep",
            "name": "Sales Representative",
            "description": "Basic sales access",
            "permissions": ["read_companies", "read_contacts", "manage_opportunities"],
            "is_system": False,
        },
        {
            "id": "role_viewer",
            "name": "Viewer",
            "description": "Read-only access",
            "permissions": ["read_companies", "read_contacts"],
            "is_system": False,
        },
    ]

    DEFAULT_PERMISSIONS = [
        {
            "id": "perm_admin",
            "key": "admin",
            "name": "Administrator",
            "description": "Full admin access",
            "group": "system",
        },
        {
            "id": "perm_manage_users",
            "key": "manage_users",
            "name": "Manage Users",
            "description": "Create, edit, deactivate users",
            "group": "users",
        },
        {
            "id": "perm_manage_billing",
            "key": "manage_billing",
            "name": "Manage Billing",
            "description": "Manage invoices and payments",
            "group": "billing",
        },
        {
            "id": "perm_manage_plans",
            "key": "manage_plans",
            "name": "Manage Plans",
            "description": "Create and edit subscription plans",
            "group": "billing",
        },
        {
            "id": "perm_manage_roles",
            "key": "manage_roles",
            "name": "Manage Roles",
            "description": "Create and edit RBAC roles",
            "group": "users",
        },
        {
            "id": "perm_read_companies",
            "key": "read_companies",
            "name": "Read Companies",
            "description": "View company data",
            "group": "crm",
        },
        {
            "id": "perm_read_contacts",
            "key": "read_contacts",
            "name": "Read Contacts",
            "description": "View contact data",
            "group": "crm",
        },
        {
            "id": "perm_manage_opportunities",
            "key": "manage_opportunities",
            "name": "Manage Opportunities",
            "description": "Create and manage sales opportunities",
            "group": "sales",
        },
        {
            "id": "perm_manage_tasks",
            "key": "manage_tasks",
            "name": "Manage Tasks",
            "description": "Create and manage tasks",
            "group": "sales",
        },
        {
            "id": "perm_reports",
            "key": "reports",
            "name": "Reports",
            "description": "View and generate reports",
            "group": "analytics",
        },
    ]

    def __init__(self, session: AsyncSession):
        self.session = session
        self.role_repo = PostgresRoleRepository(session)
        self.perm_repo = PostgresPermissionRepository(session)

    async def seed_defaults(self) -> None:
        """Seed default permissions and roles if not present."""
        existing_perms = await self.perm_repo.list()
        existing_keys = {p.key for p in existing_perms}

        for pd in self.DEFAULT_PERMISSIONS:
            if pd["key"] not in existing_keys:
                self.session.add(
                    PermissionModel(
                        id=pd["id"],
                        key=pd["key"],
                        name=pd["name"],
                        description=pd["description"],
                        group=pd["group"],
                    )
                )
        await self.session.flush()

        existing_roles = await self.role_repo.list()
        existing_role_ids = {r.id for r in existing_roles}

        for rd in self.DEFAULT_ROLES:
            if rd["id"] not in existing_role_ids:
                self.session.add(
                    RoleModel(
                        id=rd["id"],
                        name=rd["name"],
                        description=rd["description"],
                        is_system=rd["is_system"],
                    )
                )
        await self.session.flush()

        for rd in self.DEFAULT_ROLES:
            role_id = str(rd["id"])
            existing_perms_for_role = await self.role_repo.get_permissions(role_id)
            if not existing_perms_for_role:
                await self.role_repo.set_permissions(
                    role_id, cast(list[str], rd["permissions"])
                )

    async def provision_tenant(self, tenant_id: str, admin_user_id: str | None = None) -> dict:
        """Provision a new tenant with default roles, permissions, and optionally an admin user."""
        await self.seed_defaults()

        if admin_user_id:
            admin_user = await self.session.get(User, admin_user_id)
            if admin_user and admin_user.role != "admin":
                admin_user.role = "admin"
                await self.session.flush()

        return {
            "tenant_id": tenant_id,
            "roles_provisioned": len(self.DEFAULT_ROLES),
            "permissions_provisioned": len(self.DEFAULT_PERMISSIONS),
            "admin_user_id": admin_user_id,
        }


class ConfigEditorService:
    """YAML config storage with validation and versioning."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PostgresTenantConfigRepository(session)

    @staticmethod
    def validate_yaml(content: str) -> dict[str, Any]:
        """Validate YAML content. Returns {'valid': bool, 'errors': list}."""
        errors = []
        try:
            parsed = yaml.safe_load(content)
            if parsed is None:
                errors.append({"line": 1, "message": "Empty YAML content"})
            elif not isinstance(parsed, dict):
                errors.append(
                    {"line": 1, "message": f"Root must be a mapping, got {type(parsed).__name__}"}
                )
        except yaml.YAMLError as e:
            line = getattr(e, "problem_mark", None)
            if line is not None:
                errors.append({"line": line.line + 1, "column": line.column + 1, "message": str(e)})
            else:
                errors.append({"line": 0, "message": str(e)})

        return {"valid": len(errors) == 0, "errors": errors}

    async def save(
        self, tenant_id: str, key: str, yaml_content: str, created_by: str | None = None
    ) -> dict:
        """Save a YAML config with versioning."""
        validation = self.validate_yaml(yaml_content)
        if not validation["valid"]:
            return {"saved": False, "validation": validation}

        version_count = await self.repo.get_version_count(tenant_id, key)
        config = TenantConfigModel(
            tenant_id=tenant_id,
            key=key,
            yaml_content=yaml_content,
            version=version_count + 1,
            created_by=created_by,
        )
        saved = await self.repo.create(config)
        return {
            "saved": True,
            "id": saved.id,
            "version": saved.version,
            "validation": validation,
        }

    async def get_latest(self, tenant_id: str, key: str) -> TenantConfigModel | None:
        return await self.repo.get_latest(tenant_id, key)

    async def list_keys(self, tenant_id: str) -> list[str]:
        return await self.repo.list_keys(tenant_id)

    async def list_versions(self, tenant_id: str, key: str) -> list[dict]:
        versions = await self.repo.list_versions(tenant_id, key)
        return [
            {
                "id": v.id,
                "version": v.version,
                "created_by": v.created_by,
                "created_at": v.created_at,
            }
            for v in versions
        ]


class AuditCSVExportService:
    """Export audit logs to CSV."""

    @staticmethod
    def to_csv(entries: list[dict]) -> str:
        if not entries:
            return ""

        output = io.StringIO()
        fieldnames = [
            "id",
            "tenant_id",
            "user_id",
            "action",
            "resource_type",
            "resource_id",
            "outcome",
            "ip_address",
            "user_agent",
            "created_at",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for entry in entries:
            row = {k: entry.get(k, "") for k in fieldnames}
            if row.get("created_at"):
                row["created_at"] = (
                    row["created_at"].isoformat()
                    if hasattr(row["created_at"], "isoformat")
                    else str(row["created_at"])
                )
            writer.writerow(row)

        return output.getvalue()
