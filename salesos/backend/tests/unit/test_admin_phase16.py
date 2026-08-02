"""Phase 16 Admin Backend — Feature Flags, Roles, Config, Audit CSV, Tenant lifecycle."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.db_models import (
    FeatureFlagModel,
    PermissionModel,
    RoleModel,
    TenantConfigModel,
)
from app.modules.admin.pg_repositories import (
    PostgresFeatureFlagRepository,
    PostgresPermissionRepository,
    PostgresRoleRepository,
    PostgresTenantConfigRepository,
)
from app.modules.admin.routers.tenants import apply_tenant_list_filters
from app.modules.admin.schemas import TenantActivateRequest
from app.modules.admin.services import (
    AuditCSVExportService,
    ConfigEditorService,
    FeatureFlagService,
    TenantProvisioningService,
)
from app.modules.identity.models import Tenant

# ── Fake SQLAlchemy helpers ──────────────────────────────────────────────────


class FakeScalars:
    def __init__(self, items=None):
        self._items = items or []

    def all(self):
        return self._items

    def first(self):
        return self._items[0] if self._items else None


class FakeResult:
    def __init__(self, scalars=None, scalar_val=None, mapping_rows=None, iter_rows=None):
        self._scalars = FakeScalars(scalars) if scalars is not None else None
        self._scalar_val = scalar_val
        self._mapping_rows = mapping_rows or []
        self._iter_rows = iter_rows or self._mapping_rows

    def scalars(self):
        return self._scalars

    def scalar_one_or_none(self):
        return self._scalar_val

    def scalar(self):
        return self._scalar_val

    def one(self):
        if self._mapping_rows:
            return self._mapping_rows[0]
        return None

    def all(self):
        return self._mapping_rows

    def __iter__(self):
        return iter(self._iter_rows)


def _make_flag(key="test_flag", enabled=True, is_ci_test=False, rollout_pct=100, overrides=None):
    now = datetime.now(UTC)
    return FeatureFlagModel(
        id=uuid.uuid4(),
        key=key,
        name=f"Flag {key}",
        description=f"Test flag {key}",
        enabled=enabled,
        is_global=True,
        tenant_overrides=overrides or {},
        rollout_percentage=rollout_pct,
        is_ci_test=is_ci_test,
        created_at=now,
        updated_at=now,
    )


def _make_role(role_id="role_test", name="Test Role", is_system=False):
    now = datetime.now(UTC)
    return RoleModel(
        id=role_id,
        name=name,
        description=f"Role {name}",
        is_system=is_system,
        created_at=now,
        updated_at=now,
    )


def _make_permission(perm_id="perm_test", key="test_perm", name="Test Perm", group="test"):
    now = datetime.now(UTC)
    return PermissionModel(
        id=perm_id,
        key=key,
        name=name,
        description=f"Permission {name}",
        group=group,
        created_at=now,
    )


def _make_config(tenant_id="t-1", key="settings", yaml_content="key: value", version=1):
    now = datetime.now(UTC)
    return TenantConfigModel(
        id=version,
        tenant_id=tenant_id,
        key=key,
        yaml_content=yaml_content,
        version=version,
        created_by="admin",
        created_at=now,
    )


# ── Feature Flag Evaluation ─────────────────────────────────────────────────


class TestFeatureFlagEvaluation:
    @pytest.mark.asyncio
    async def test_ci_test_flag_always_enabled(self):
        flag = _make_flag(is_ci_test=True, enabled=False)
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            s = str(stmt)
            if "admin_feature_flags" in s and "key" in s:
                return FakeResult(scalar_val=flag)
            if "SELECT" in s and "tenants" in s:
                return FakeResult(scalar_val=None)
            return FakeResult()

        session.execute = execute
        repo = PostgresFeatureFlagRepository(session)
        result = await repo.evaluate("test_flag", "t-1", ["t-1"])
        assert result["enabled"] is True
        assert result["reason"] == "ci_test_always_on"

    @pytest.mark.asyncio
    async def test_tenant_override_takes_precedence(self):
        flag = _make_flag(enabled=True, overrides={"t-99": False})
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            s = str(stmt)
            if "admin_feature_flags" in s and "key" in s:
                return FakeResult(scalar_val=flag)
            return FakeResult()

        session.execute = execute
        repo = PostgresFeatureFlagRepository(session)
        result = await repo.evaluate("test_flag", "t-99")
        assert result["enabled"] is False
        assert result["reason"] == "tenant_override"

    @pytest.mark.asyncio
    async def test_globally_disabled_flag(self):
        flag = _make_flag(enabled=False)
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            s = str(stmt)
            if "admin_feature_flags" in s and "key" in s:
                return FakeResult(scalar_val=flag)
            return FakeResult()

        session.execute = execute
        repo = PostgresFeatureFlagRepository(session)
        result = await repo.evaluate("test_flag", "t-1")
        assert result["enabled"] is False
        assert result["reason"] == "globally_disabled"

    @pytest.mark.asyncio
    async def test_full_rollout_enabled(self):
        flag = _make_flag(enabled=True, rollout_pct=100)
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            s = str(stmt)
            if "admin_feature_flags" in s and "key" in s:
                return FakeResult(scalar_val=flag)
            return FakeResult()

        session.execute = execute
        repo = PostgresFeatureFlagRepository(session)
        result = await repo.evaluate("test_flag", "t-1")
        assert result["enabled"] is True
        assert result["reason"] == "fully_rollout"

    @pytest.mark.asyncio
    async def test_zero_rollout_disabled(self):
        flag = _make_flag(enabled=True, rollout_pct=0)
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            s = str(stmt)
            if "admin_feature_flags" in s and "key" in s:
                return FakeResult(scalar_val=flag)
            return FakeResult()

        session.execute = execute
        repo = PostgresFeatureFlagRepository(session)
        result = await repo.evaluate("test_flag", "t-1")
        assert result["enabled"] is False
        assert result["reason"] == "zero_rollout"

    @pytest.mark.asyncio
    async def test_gradual_rollout_first_included(self):
        flag = _make_flag(enabled=True, rollout_pct=50)
        tenant_ids = ["t-1", "t-2", "t-3", "t-4"]
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            s = str(stmt)
            if "admin_feature_flags" in s and "key" in s:
                return FakeResult(scalar_val=flag)
            return FakeResult()

        session.execute = execute
        repo = PostgresFeatureFlagRepository(session)
        result = await repo.evaluate("test_flag", "t-1", tenant_ids)
        assert result["reason"] == "gradual_rollout_50pct"
        sorted_ids = sorted(tenant_ids)
        idx = sorted_ids.index("t-1")
        ratio = idx / len(sorted_ids)
        expected = ratio < 0.5
        assert result["enabled"] == expected

    @pytest.mark.asyncio
    async def test_flag_not_found(self):
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            s = str(stmt)
            if "admin_feature_flags" in s:
                return FakeResult(scalar_val=None)
            return FakeResult()

        session.execute = execute
        repo = PostgresFeatureFlagRepository(session)
        result = await repo.evaluate("nonexistent", "t-1")
        assert result["enabled"] is False
        assert result["reason"] == "flag_not_found"

    @pytest.mark.asyncio
    async def test_tenant_not_in_rollout_set(self):
        flag = _make_flag(enabled=True, rollout_pct=50)
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            s = str(stmt)
            if "admin_feature_flags" in s and "key" in s:
                return FakeResult(scalar_val=flag)
            return FakeResult()

        session.execute = execute
        repo = PostgresFeatureFlagRepository(session)
        result = await repo.evaluate("test_flag", "t-unknown", ["t-1", "t-2"])
        assert result["enabled"] is False
        assert result["reason"] == "tenant_not_in_rollout_set"


# ── Feature Flag Service ────────────────────────────────────────────────────


class TestFeatureFlagService:
    @pytest.mark.asyncio
    async def test_create_ci_test_flag(self):
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()

        svc = FeatureFlagService(session)
        result = await svc.create_ci_test_flag("ci_flag", "CI Flag", "for testing")
        assert result["key"] == "ci_flag"
        assert result["enabled"] is True
        assert result["is_ci_test"] is True
        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_enabled_calls_evaluate(self):
        flag = _make_flag(enabled=True, rollout_pct=100)
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            s = str(stmt)
            if "admin_feature_flags" in s:
                return FakeResult(scalar_val=flag)
            return FakeResult(scalar_val=None)

        session.execute = execute
        svc = FeatureFlagService(session)
        result = await svc.is_enabled("test_flag", "t-1")
        assert result["enabled"] is True


# ── Roles & Permissions ─────────────────────────────────────────────────────


class TestRolesAndPermissions:
    @pytest.mark.asyncio
    async def test_list_roles(self):
        roles = [_make_role("role_a", "Role A"), _make_role("role_b", "Role B")]
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            s = str(stmt)
            if "admin_roles" in s and "admin_role_permissions" not in s:
                return FakeResult(scalars=roles)
            if "admin_role_permissions" in s and "permission_id" in s:
                return FakeResult(scalar_val=None)
            return FakeResult()

        session.execute = execute
        repo = PostgresRoleRepository(session)
        result = await repo.list()
        assert len(result) == 2
        assert result[0].name == "Role A"

    @pytest.mark.asyncio
    async def test_create_role(self):
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()

        repo = PostgresRoleRepository(session)
        role = _make_role("role_new", "New Role")
        created = await repo.create(role)
        assert created.id == "role_new"
        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_role(self):
        role = _make_role("role_upd", "Old Name")
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            s = str(stmt)
            if "admin_roles" in s and "WHERE" in s:
                return FakeResult(scalar_val=role)
            return FakeResult()

        session.execute = execute
        repo = PostgresRoleRepository(session)
        updated = await repo.update("role_upd", {"name": "New Name"})
        assert updated.name == "New Name"

    @pytest.mark.asyncio
    async def test_delete_non_system_role(self):
        role = _make_role("role_del", "Delete Me", is_system=False)
        session = AsyncMock(spec=AsyncSession)
        session.delete = AsyncMock()
        session.flush = AsyncMock()

        async def execute(stmt, *args, **kwargs):
            return FakeResult(scalar_val=role)

        session.execute = execute
        repo = PostgresRoleRepository(session)
        result = await repo.delete("role_del")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_system_role_blocked(self):
        role = _make_role("role_admin", "Admin", is_system=True)
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            return FakeResult(scalar_val=role)

        session.execute = execute
        repo = PostgresRoleRepository(session)
        result = await repo.delete("role_admin")
        assert result is False

    @pytest.mark.asyncio
    async def test_set_permissions(self):
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.execute = AsyncMock()

        repo = PostgresRoleRepository(session)
        await repo.set_permissions("role_a", ["perm_1", "perm_2"])
        assert session.add.call_count == 2

    @pytest.mark.asyncio
    async def test_get_permissions(self):
        rows = [("perm_1",), ("perm_2",)]
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            return FakeResult(mapping_rows=rows)

        session.execute = execute
        repo = PostgresRoleRepository(session)
        perms = await repo.get_permissions("role_a")
        assert perms == ["perm_1", "perm_2"]

    @pytest.mark.asyncio
    async def test_list_permissions(self):
        perms = [
            _make_permission("p1", "read", "Read", "crm"),
            _make_permission("p2", "write", "Write", "crm"),
        ]
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            return FakeResult(scalars=perms)

        session.execute = execute
        repo = PostgresPermissionRepository(session)
        result = await repo.list()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_roles_with_permissions(self):
        role = _make_role("role_x", "Role X")
        session = AsyncMock(spec=AsyncSession)
        call_count = 0

        async def execute(stmt, *args, **kwargs):
            nonlocal call_count
            s = str(stmt)
            if "admin_roles" in s and "admin_role_permissions" not in s and "WHERE" not in s:
                return FakeResult(scalars=[role])
            if "admin_role_permissions" in s and "permission_id" in s:
                call_count += 1
                if call_count == 1:
                    return FakeResult(mapping_rows=[("perm_a",), ("perm_b",)])
                return FakeResult(mapping_rows=[])
            return FakeResult()

        session.execute = execute
        repo = PostgresRoleRepository(session)
        result = await repo.get_roles_with_permissions()
        assert len(result) == 1
        assert result[0]["permissions"] == ["perm_a", "perm_b"]


# ── Config Editor ────────────────────────────────────────────────────────────


class TestConfigEditor:
    def test_validate_valid_yaml(self):
        result = ConfigEditorService.validate_yaml("key: value\nlist:\n  - item1\n")
        assert result["valid"] is True
        assert result["errors"] == []

    def test_validate_invalid_yaml(self):
        result = ConfigEditorService.validate_yaml("{{invalid yaml}}")
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_empty_yaml(self):
        result = ConfigEditorService.validate_yaml("")
        assert result["valid"] is False

    def test_validate_non_dict_yaml(self):
        result = ConfigEditorService.validate_yaml("- item1\n- item2\n")
        assert result["valid"] is False
        assert "Root must be a mapping" in result["errors"][0]["message"]

    @pytest.mark.asyncio
    async def test_save_config_creates_versioned_entry(self):
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.execute = AsyncMock(return_value=FakeResult(scalar_val=0))

        svc = ConfigEditorService(session)
        result = await svc.save("t-1", "settings", "key: value\n")
        assert result["saved"] is True
        assert result["version"] == 1

    @pytest.mark.asyncio
    async def test_save_config_rejects_invalid_yaml(self):
        session = AsyncMock(spec=AsyncSession)
        svc = ConfigEditorService(session)
        result = await svc.save("t-1", "settings", "{{bad}}")
        assert result["saved"] is False

    @pytest.mark.asyncio
    async def test_list_keys(self):
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock(
            return_value=FakeResult(mapping_rows=[("settings",), ("rules",)])
        )

        svc = ConfigEditorService(session)
        keys = await svc.list_keys("t-1")
        assert keys == ["settings", "rules"]

    @pytest.mark.asyncio
    async def test_list_versions(self):
        configs = [_make_config(version=3), _make_config(version=2), _make_config(version=1)]
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock(return_value=FakeResult(scalars=configs))

        svc = ConfigEditorService(session)
        versions = await svc.list_versions("t-1", "settings")
        assert len(versions) == 3
        assert versions[0]["version"] == 3


# ── Audit CSV Export ────────────────────────────────────────────────────────


class TestAuditCSVExport:
    def test_empty_entries_returns_empty_string(self):
        result = AuditCSVExportService.to_csv([])
        assert result == ""

    def test_single_entry_csv(self):
        now = datetime.now(UTC)
        entries = [
            {
                "id": "log-1",
                "tenant_id": "t-1",
                "user_id": "u-1",
                "action": "created",
                "resource_type": "company",
                "resource_id": "c-1",
                "outcome": "success",
                "ip_address": "127.0.0.1",
                "user_agent": "test",
                "created_at": now,
            }
        ]
        result = AuditCSVExportService.to_csv(entries)
        lines = result.strip().split("\n")
        assert len(lines) == 2
        header = lines[0]
        assert "id" in header
        assert "outcome" in header
        assert "log-1" in lines[1]

    def test_multiple_entries_csv(self):
        now = datetime.now(UTC)
        entries = [
            {
                "id": f"log-{i}",
                "tenant_id": "t-1",
                "action": f"action_{i}",
                "resource_type": "company",
                "created_at": now,
            }
            for i in range(5)
        ]
        result = AuditCSVExportService.to_csv(entries)
        lines = result.strip().split("\n")
        assert len(lines) == 6

    def test_csv_datetime_serialization(self):
        now = datetime.now(UTC)
        entries = [{"id": "log-dt", "created_at": now}]
        result = AuditCSVExportService.to_csv(entries)
        assert now.isoformat() in result

    def test_csv_extras_ignored(self):
        entries = [{"id": "log-extra", "unknown_field": "ignored", "action": "test"}]
        result = AuditCSVExportService.to_csv(entries)
        assert "unknown_field" not in result.split("\n")[0]
        assert "action" in result.split("\n")[0]


# ── Tenant Provisioning ─────────────────────────────────────────────────────


class TestTenantProvisioning:
    @pytest.mark.asyncio
    async def test_seed_defaults_creates_permissions_and_roles(self):
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()

        perm_repo = AsyncMock()
        perm_repo.list = AsyncMock(return_value=[])
        role_repo = AsyncMock()
        role_repo.list = AsyncMock(return_value=[])
        role_repo.get_permissions = AsyncMock(return_value=[])
        role_repo.set_permissions = AsyncMock()

        with (
            patch(
                "app.modules.admin.services.PostgresPermissionRepository", return_value=perm_repo
            ),
            patch("app.modules.admin.services.PostgresRoleRepository", return_value=role_repo),
        ):
            svc = TenantProvisioningService(session)
            await svc.seed_defaults()

        assert session.add.call_count > 0

    @pytest.mark.asyncio
    async def test_provision_tenant_calls_seed(self):
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()

        perm_repo = AsyncMock()
        perm_repo.list = AsyncMock(return_value=[])
        role_repo = AsyncMock()
        role_repo.list = AsyncMock(return_value=[])
        role_repo.get_permissions = AsyncMock(return_value=[])
        role_repo.set_permissions = AsyncMock()

        with (
            patch(
                "app.modules.admin.services.PostgresPermissionRepository", return_value=perm_repo
            ),
            patch("app.modules.admin.services.PostgresRoleRepository", return_value=role_repo),
        ):
            svc = TenantProvisioningService(session)
            result = await svc.provision_tenant("t-new")
        assert result["tenant_id"] == "t-new"
        assert result["roles_provisioned"] > 0
        assert result["permissions_provisioned"] > 0

    @pytest.mark.asyncio
    async def test_seed_studio_config_idempotent(self):
        session = AsyncMock(spec=AsyncSession)
        config_repo = AsyncMock()
        existing = MagicMock()
        existing.version = 1
        config_repo.get_latest = AsyncMock(return_value=existing)

        with patch(
            "app.modules.admin.services.PostgresTenantConfigRepository", return_value=config_repo
        ):
            svc = TenantProvisioningService(session)
            result = await svc.seed_studio_config("t-1", plan="free")
        assert result["seeded"] is False
        assert result["idempotent"] is True
        config_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_provision_workflow_creates_tenant(self):
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()

        empty = MagicMock()
        empty.scalar_one_or_none = MagicMock(return_value=None)
        session.execute = AsyncMock(return_value=empty)

        perm_repo = AsyncMock()
        perm_repo.list = AsyncMock(return_value=[])
        role_repo = AsyncMock()
        role_repo.list = AsyncMock(return_value=[])
        role_repo.get_permissions = AsyncMock(return_value=[])
        role_repo.set_permissions = AsyncMock()
        config_repo = AsyncMock()
        config_repo.get_latest = AsyncMock(return_value=None)
        created_cfg = MagicMock()
        created_cfg.version = 1
        config_repo.create = AsyncMock(return_value=created_cfg)

        with (
            patch(
                "app.modules.admin.services.PostgresPermissionRepository", return_value=perm_repo
            ),
            patch("app.modules.admin.services.PostgresRoleRepository", return_value=role_repo),
            patch(
                "app.modules.admin.services.PostgresTenantConfigRepository",
                return_value=config_repo,
            ),
        ):
            svc = TenantProvisioningService(session)
            result = await svc.provision_workflow(
                name="Acme",
                slug="acme-test",
                plan="starter",
                plan_id="plan_starter_v1",
                region="me-central-1",
            )

        assert result["created"] is True
        assert result["idempotent"] is False
        assert result["provisioning_status"] == "active"
        assert result["studio_config"]["seeded"] is True
        assert session.add.call_count >= 1
        tenant_arg = session.add.call_args_list[0].args[0]
        assert getattr(tenant_arg, "plan_id", None) == "plan_starter_v1"
        assert getattr(tenant_arg, "region", None) == "me-central-1"

    def test_normalize_slug_rejects_invalid(self):
        with pytest.raises(ValueError):
            TenantProvisioningService._normalize_slug("Bad Slug")
        with pytest.raises(ValueError):
            TenantProvisioningService._normalize_slug("a")
        assert TenantProvisioningService._normalize_slug("  Acme-1  ") == "acme-1"

    def test_admin_triplet_partial_rejected(self):
        with pytest.raises(ValueError, match="together"):
            TenantProvisioningService._validate_admin_triplet("a@b.c", "pw", None)
        assert TenantProvisioningService._validate_admin_triplet("a@b.c", "pw", "Admin") is True

    @pytest.mark.asyncio
    async def test_provision_workflow_rejects_empty_name_and_long_plan_id(self):
        session = AsyncMock(spec=AsyncSession)
        svc = TenantProvisioningService(session)
        with pytest.raises(ValueError, match="name must"):
            await svc.provision_workflow(name="  ", slug="ok-slug")
        with pytest.raises(ValueError, match="plan_id"):
            await svc.provision_workflow(name="Acme", slug="ok-slug", plan_id="x" * 65)

    @pytest.mark.asyncio
    async def test_provision_workflow_keeps_suspended_on_idempotent_rerun(self):
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()

        existing_tenant = MagicMock()
        existing_tenant.id = "t-susp"
        existing_tenant.slug = "acme-susp"
        existing_tenant.plan = "free"
        existing_tenant.provisioning_status = "suspended"
        existing_tenant.is_active = False
        existing_tenant.name = "Acme"

        found = MagicMock()
        found.scalar_one_or_none = MagicMock(return_value=existing_tenant)
        session.execute = AsyncMock(return_value=found)

        perm_repo = AsyncMock()
        perm_repo.list = AsyncMock(return_value=[])
        role_repo = AsyncMock()
        role_repo.list = AsyncMock(return_value=[])
        role_repo.get_permissions = AsyncMock(return_value=[])
        role_repo.set_permissions = AsyncMock()
        config_repo = AsyncMock()
        existing_cfg = MagicMock()
        existing_cfg.version = 1
        config_repo.get_latest = AsyncMock(return_value=existing_cfg)

        with (
            patch(
                "app.modules.admin.services.PostgresPermissionRepository", return_value=perm_repo
            ),
            patch("app.modules.admin.services.PostgresRoleRepository", return_value=role_repo),
            patch(
                "app.modules.admin.services.PostgresTenantConfigRepository",
                return_value=config_repo,
            ),
        ):
            svc = TenantProvisioningService(session)
            result = await svc.provision_workflow(name="Acme", slug="acme-susp")

        assert result["idempotent"] is True
        assert result["provisioning_status"] == "suspended"
        assert existing_tenant.provisioning_status == "suspended"


class TestTenantListFilters:
    """GET /admin/tenants Owner Platform query params (FE-S04-10/12/15/16)."""

    def test_owner_platform_filters_compile(self):
        now = datetime(2026, 8, 2, tzinfo=UTC)
        stmt = apply_tenant_list_filters(
            select(Tenant),
            plan_id="plan_starter_v1",
            region="me-central-1",
            data_residency="ae",
            provisioning_status="active",
            trial="has_trial",
            search="acme",
            now=now,
        )
        sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "plan_id" in sql
        assert "me-central-1" in sql
        assert "data_residency" in sql
        assert "provisioning_status" in sql
        assert "trial_ends_at" in sql

    def test_trial_none_and_expired(self):
        now = datetime(2026, 8, 2, tzinfo=UTC)
        none_sql = str(
            apply_tenant_list_filters(select(Tenant), trial="none", now=now).compile(
                compile_kwargs={"literal_binds": True}
            )
        )
        assert "IS NULL" in none_sql.upper() or "is null" in none_sql.lower()
        expired_sql = str(
            apply_tenant_list_filters(select(Tenant), trial="expired", now=now).compile(
                compile_kwargs={"literal_binds": True}
            )
        )
        assert "trial_ends_at" in expired_sql

    def test_invalid_filter_values_raise(self):
        with pytest.raises(ValueError, match="provisioning_status"):
            apply_tenant_list_filters(select(Tenant), provisioning_status="bogus")
        with pytest.raises(ValueError, match="trial"):
            apply_tenant_list_filters(select(Tenant), trial="soon")

    def test_activate_request_defaults(self):
        assert TenantActivateRequest().reason == ""
        assert TenantActivateRequest(reason="restore").reason == "restore"


# ── Repository Unit Tests ───────────────────────────────────────────────────


class TestFeatureFlagRepository:
    @pytest.mark.asyncio
    async def test_list(self):
        flags = [_make_flag("f1"), _make_flag("f2")]
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            return FakeResult(scalars=flags)

        session.execute = execute
        repo = PostgresFeatureFlagRepository(session)
        result = await repo.list()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_by_key(self):
        flag = _make_flag("my_flag")
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            return FakeResult(scalar_val=flag)

        session.execute = execute
        repo = PostgresFeatureFlagRepository(session)
        result = await repo.get_by_key("my_flag")
        assert result.key == "my_flag"

    @pytest.mark.asyncio
    async def test_create_flag(self):
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()

        repo = PostgresFeatureFlagRepository(session)
        flag = _make_flag("new_flag")
        created = await repo.create(flag)
        assert created.key == "new_flag"
        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_tenant_override(self):
        flag = _make_flag("ov_flag", overrides={})
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            return FakeResult(scalar_val=flag)

        session.execute = execute
        session.flush = AsyncMock()

        repo = PostgresFeatureFlagRepository(session)
        result = await repo.set_tenant_override(flag.id, "t-99", True)
        assert result.tenant_overrides["t-99"] is True

    @pytest.mark.asyncio
    async def test_get_tenants_for_flag(self):
        flag = _make_flag("tf_flag", overrides={"t-1": True, "t-2": False})
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            return FakeResult(scalar_val=flag)

        session.execute = execute

        repo = PostgresFeatureFlagRepository(session)
        result = await repo.get_tenants_for_flag(flag.id)
        assert len(result) == 2
        tenant_ids = {t["tenant_id"] for t in result}
        assert "t-1" in tenant_ids
        assert "t-2" in tenant_ids


# ── Tenant Config Repository ────────────────────────────────────────────────


class TestTenantConfigRepository:
    @pytest.mark.asyncio
    async def test_get_latest(self):
        config = _make_config(version=3)
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            return FakeResult(scalar_val=config)

        session.execute = execute
        repo = PostgresTenantConfigRepository(session)
        result = await repo.get_latest("t-1", "settings")
        assert result.version == 3

    @pytest.mark.asyncio
    async def test_list_keys(self):
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock(return_value=FakeResult(mapping_rows=[("a",), ("b",)]))

        repo = PostgresTenantConfigRepository(session)
        keys = await repo.list_keys("t-1")
        assert keys == ["a", "b"]

    @pytest.mark.asyncio
    async def test_get_version_count(self):
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock(return_value=FakeResult(scalar_val=5))

        repo = PostgresTenantConfigRepository(session)
        count = await repo.get_version_count("t-1", "settings")
        assert count == 5

    @pytest.mark.asyncio
    async def test_create_config(self):
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()

        repo = PostgresTenantConfigRepository(session)
        config = _make_config()
        created = await repo.create(config)
        assert created.tenant_id == "t-1"
        session.add.assert_called_once()


# ── Role Repository ─────────────────────────────────────────────────────────


class TestRoleRepository:
    @pytest.mark.asyncio
    async def test_get_role(self):
        role = _make_role("r1", "Role One")
        session = AsyncMock(spec=AsyncSession)

        async def execute(stmt, *args, **kwargs):
            return FakeResult(scalar_val=role)

        session.execute = execute
        repo = PostgresRoleRepository(session)
        result = await repo.get("r1")
        assert result.name == "Role One"

    @pytest.mark.asyncio
    async def test_get_role_not_found(self):
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock(return_value=FakeResult(scalar_val=None))

        repo = PostgresRoleRepository(session)
        result = await repo.get("nonexistent")
        assert result is None
