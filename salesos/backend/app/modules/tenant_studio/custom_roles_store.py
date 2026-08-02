"""STORY-10-06 — In-memory custom roles store (no Alembic / FORCE RLS).

Ceiling from Plan.entitlements (injected per tenant or plan_tier default).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.modules.admin.entitlements import (
    PlanEntitlements,
    default_entitlements_for_tier,
    parse_entitlements,
)
from app.modules.tenant_studio.custom_roles import (
    CustomRole,
    CustomRoleError,
    build_custom_role,
)
from app.modules.tenant_studio.permission_ceiling import (
    PermissionCeilingError,
    assert_within_ceiling,
    catalog_with_ceiling,
    check_permissions_against_ceiling,
    summarize_ceiling,
)


@dataclass
class MemCustomRolesStore:
    """Tenant-scoped custom roles for CAP-003 Studio."""

    _by_id: dict[str, CustomRole] = field(default_factory=dict)
    _ceilings: dict[str, PlanEntitlements] = field(default_factory=dict)

    def set_ceiling(
        self,
        tenant_id: str,
        entitlements: PlanEntitlements | dict[str, Any] | None = None,
        *,
        plan_tier: str | None = None,
    ) -> PlanEntitlements:
        tid = str(tenant_id).strip()
        if not tid:
            raise CustomRoleError("tenant_id required")
        if entitlements is not None:
            doc = parse_entitlements(entitlements)
        else:
            doc = default_entitlements_for_tier(plan_tier or "starter")
        self._ceilings[tid] = doc
        return doc

    def get_ceiling(self, tenant_id: str, *, plan_tier: str | None = None) -> PlanEntitlements:
        tid = str(tenant_id).strip()
        if tid in self._ceilings:
            return self._ceilings[tid]
        return default_entitlements_for_tier(plan_tier or "starter")

    def upsert(
        self,
        *,
        tenant_id: str,
        name: str,
        permissions: list[str],
        description: str = "",
        role_id: str | None = None,
        entitlements: PlanEntitlements | dict[str, Any] | None = None,
        plan_tier: str | None = None,
    ) -> CustomRole:
        tid = str(tenant_id)
        if entitlements is not None:
            ceiling = self.set_ceiling(tid, entitlements)
        elif plan_tier is not None:
            ceiling = self.set_ceiling(tid, plan_tier=plan_tier)
        else:
            ceiling = self.get_ceiling(tid)

        capped = assert_within_ceiling(list(permissions), ceiling)

        now = datetime.now(UTC).isoformat()
        rid = (role_id or "").strip()
        existing = self._by_id.get(rid) if rid else None
        if existing and existing.tenant_id != tid:
            raise PermissionError("cross-tenant custom role write blocked")
        schema_version = 1
        created_at = now
        if existing:
            schema_version = max(existing.schema_version + 1, 1)
            created_at = existing.created_at or now
        else:
            rid = rid or uuid.uuid4().hex[:12]

        role = build_custom_role(
            tenant_id=tid,
            name=name,
            permissions=capped,
            description=description,
            role_id=rid,
            schema_version=schema_version,
        )
        role.created_at = created_at
        role.updated_at = now
        self._by_id[role.id] = role
        return role

    def get(self, role_id: str, *, tenant_id: str) -> CustomRole | None:
        row = self._by_id.get(str(role_id))
        if row is None or row.tenant_id != str(tenant_id):
            return None
        return row

    def list_for_tenant(self, *, tenant_id: str) -> list[CustomRole]:
        tid = str(tenant_id)
        return sorted(
            [r for r in self._by_id.values() if r.tenant_id == tid],
            key=lambda r: r.updated_at or "",
            reverse=True,
        )

    def check(
        self,
        *,
        tenant_id: str,
        permissions: list[str],
        entitlements: PlanEntitlements | dict[str, Any] | None = None,
        plan_tier: str | None = None,
    ):
        if entitlements is not None:
            ceiling = parse_entitlements(entitlements)
        elif plan_tier is not None:
            ceiling = default_entitlements_for_tier(plan_tier)
        else:
            ceiling = self.get_ceiling(tenant_id)
        return check_permissions_against_ceiling(list(permissions), ceiling)

    def catalog(
        self,
        *,
        tenant_id: str,
        plan_tier: str | None = None,
    ) -> list[dict[str, Any]]:
        return catalog_with_ceiling(self.get_ceiling(tenant_id, plan_tier=plan_tier))

    def ceiling_summary(self, *, tenant_id: str, plan_tier: str | None = None) -> dict[str, Any]:
        return summarize_ceiling(self.get_ceiling(tenant_id, plan_tier=plan_tier))


DEFAULT_CUSTOM_ROLES_STORE = MemCustomRolesStore()

__all__ = [
    "DEFAULT_CUSTOM_ROLES_STORE",
    "MemCustomRolesStore",
    "PermissionCeilingError",
    "CustomRoleError",
]
