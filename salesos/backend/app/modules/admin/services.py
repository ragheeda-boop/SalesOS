"""Admin domain services: feature flag evaluation, tenant provisioning, config validation, audit CSV export."""  # noqa: E501

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime
from typing import Any, cast

import yaml  # type: ignore[import-untyped]
from sqlalchemy import select
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
    """Handles tenant creation with default roles, permissions, and admin user.

    STORY-04-02: idempotent ``provision_workflow`` creates tenant + Studio config
    seed + first admin assignment. Hardcoded Studio templates per plan tier are
    accepted debt until Tenant Studio (Phase 3).
    """

    STUDIO_CONFIG_KEY = "studio.defaults"

    # Hardcoded per plan tier (Sprint-04 technical debt — not Studio-editable yet).
    STUDIO_TEMPLATES: dict[str, str] = {
        "free": (
            "version: 1\n"
            "tier: free\n"
            "modules:\n"
            "  - crm_basic\n"
            "limits:\n"
            "  max_users: 3\n"
        ),
        "starter": (
            "version: 1\n"
            "tier: starter\n"
            "modules:\n"
            "  - crm_basic\n"
            "  - pipeline\n"
            "limits:\n"
            "  max_users: 10\n"
        ),
        "growth": (
            "version: 1\n"
            "tier: growth\n"
            "modules:\n"
            "  - crm_basic\n"
            "  - pipeline\n"
            "  - reports\n"
            "limits:\n"
            "  max_users: 50\n"
        ),
        "enterprise": (
            "version: 1\n"
            "tier: enterprise\n"
            "modules:\n"
            "  - crm_basic\n"
            "  - pipeline\n"
            "  - reports\n"
            "  - integrations\n"
            "limits:\n"
            "  max_users: -1\n"
        ),
    }

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
                await self.role_repo.set_permissions(role_id, cast(list[str], rd["permissions"]))

    async def provision_tenant(self, tenant_id: str, admin_user_id: str | None = None) -> dict:
        """Provision a new tenant with default roles, permissions, and optionally an admin user."""
        await self.seed_defaults()

        if admin_user_id:
            await self._assign_admin(admin_user_id)

        return {
            "tenant_id": tenant_id,
            "roles_provisioned": len(self.DEFAULT_ROLES),
            "permissions_provisioned": len(self.DEFAULT_PERMISSIONS),
            "admin_user_id": admin_user_id,
        }

    async def _assign_admin(self, admin_user_id: str) -> User | None:
        try:
            uid: uuid.UUID | str = uuid.UUID(admin_user_id)
        except (ValueError, TypeError):
            uid = admin_user_id
        admin_user = await self.session.get(User, uid)
        if admin_user and admin_user.role != "admin":
            admin_user.role = "admin"
            await self.session.flush()
        return admin_user

    def _studio_yaml_for_plan(self, plan: str) -> str:
        return self.STUDIO_TEMPLATES.get(plan, self.STUDIO_TEMPLATES["free"])

    async def seed_studio_config(self, tenant_id: str, plan: str = "free") -> dict[str, Any]:
        """Seed default Studio YAML if missing (idempotent)."""
        config_repo = PostgresTenantConfigRepository(self.session)
        existing = await config_repo.get_latest(tenant_id, self.STUDIO_CONFIG_KEY)
        if existing is not None:
            return {
                "seeded": False,
                "idempotent": True,
                "key": self.STUDIO_CONFIG_KEY,
                "version": existing.version,
            }

        yaml_content = self._studio_yaml_for_plan(plan)
        config = TenantConfigModel(
            tenant_id=tenant_id,
            key=self.STUDIO_CONFIG_KEY,
            yaml_content=yaml_content,
            version=1,
            created_by="system:provisioning",
        )
        saved = await config_repo.create(config)
        return {
            "seeded": True,
            "idempotent": False,
            "key": self.STUDIO_CONFIG_KEY,
            "version": saved.version,
        }

    @staticmethod
    def _normalize_slug(slug: str) -> str:
        normalized = (slug or "").strip().lower()
        if not normalized or len(normalized) < 2 or len(normalized) > 100:
            raise ValueError("slug must be 2–100 chars")
        if any(ch for ch in normalized if not (ch.isalnum() or ch == "-")):
            raise ValueError("slug must match ^[a-z0-9-]+$")
        return normalized

    @staticmethod
    def _validate_admin_triplet(
        admin_email: str | None,
        admin_password: str | None,
        admin_full_name: str | None,
    ) -> bool:
        """Return True if all three present; raise if partially provided."""
        present = [bool(admin_email), bool(admin_password), bool(admin_full_name)]
        if any(present) and not all(present):
            raise ValueError(
                "admin_email, admin_password, and admin_full_name must be provided together"
            )
        return all(present)

    async def provision_workflow(
        self,
        *,
        name: str,
        slug: str,
        domain: str | None = None,
        plan: str = "free",
        plan_id: str | None = None,
        region: str | None = None,
        data_residency: str | None = None,
        trial_ends_at: datetime | None = None,
        admin_user_id: str | None = None,
        admin_email: str | None = None,
        admin_password: str | None = None,
        admin_full_name: str | None = None,
        force_active: bool = False,
    ) -> dict[str, Any]:
        """Idempotent STORY-04-02 workflow: tenant + roles + Studio seed + first admin.

        Re-invoking with the same slug returns the existing tenant without
        duplicating Studio config or roles. Suspended tenants stay suspended
        on idempotent re-run unless ``force_active=True``.
        """
        slug = self._normalize_slug(slug)
        if plan_id is not None and len(plan_id) > 64:
            raise ValueError("plan_id must be <= 64 chars")
        if region is not None and len(region) > 32:
            raise ValueError("region must be <= 32 chars")
        if data_residency is not None and len(data_residency) > 32:
            raise ValueError("data_residency must be <= 32 chars")
        create_admin = self._validate_admin_triplet(admin_email, admin_password, admin_full_name)

        existing = await self.session.execute(select(Tenant).where(Tenant.slug == slug))
        tenant = existing.scalar_one_or_none()
        created = False
        prior_status = None

        if tenant is None:
            tenant = Tenant(
                name=name.strip() if name else name,
                slug=slug,
                domain=domain,
                plan=plan or "free",
                plan_id=plan_id,
                region=region,
                data_residency=data_residency,
                provisioning_status="pending",
                trial_ends_at=trial_ends_at,
                is_active=True,
                settings={},
                features={},
            )
            self.session.add(tenant)
            await self.session.flush()
            created = True
        else:
            prior_status = tenant.provisioning_status
            if plan_id is not None:
                tenant.plan_id = plan_id
            if region is not None:
                tenant.region = region
            if data_residency is not None:
                tenant.data_residency = data_residency
            if trial_ends_at is not None:
                tenant.trial_ends_at = trial_ends_at
            if name and name.strip() and name.strip() != tenant.name:
                tenant.name = name.strip()

        try:
            seed_result = await self.provision_tenant(str(tenant.id), admin_user_id=admin_user_id)
            studio_result = await self.seed_studio_config(str(tenant.id), plan=tenant.plan)

            resolved_admin_id = admin_user_id
            if create_admin and not admin_user_id:
                resolved_admin_id = await self._ensure_first_admin(
                    tenant_id=tenant.id,
                    email=str(admin_email),
                    password=str(admin_password),
                    full_name=str(admin_full_name),
                )

            # Do not silently reactivate a suspended tenant on idempotent re-run.
            if prior_status == "suspended" and not force_active:
                tenant.provisioning_status = "suspended"
            else:
                tenant.provisioning_status = "active"
                if not tenant.is_active and force_active:
                    tenant.is_active = True
            await self.session.flush()

            return {
                "tenant_id": str(tenant.id),
                "slug": tenant.slug,
                "created": created,
                "idempotent": not created,
                "provisioning_status": tenant.provisioning_status,
                "roles_provisioned": seed_result["roles_provisioned"],
                "permissions_provisioned": seed_result["permissions_provisioned"],
                "studio_config": studio_result,
                "admin_user_id": resolved_admin_id,
            }
        except Exception:
            tenant.provisioning_status = "failed"
            await self.session.flush()
            raise

    async def _ensure_first_admin(
        self,
        *,
        tenant_id: uuid.UUID,
        email: str,
        password: str,
        full_name: str,
    ) -> str:
        """Create or promote first admin for the tenant (idempotent by email)."""
        from app.modules.identity.service import IdentityService

        result = await self.session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is not None:
            user.tenant_id = tenant_id
            user.role = "admin"
            user.is_active = True
            await self.session.flush()
            return str(user.id)

        identity = IdentityService(db=self.session)
        created_user = await identity.create_user(
            email=email,
            password=password,
            full_name=full_name,
            tenant_id=str(tenant_id),
        )
        created_user.role = "admin"
        await self.session.flush()
        return str(created_user.id)


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
