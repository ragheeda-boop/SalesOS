"""STORY-10-06 — Permissions Studio: entitlement ceiling + privilege escalation."""

from __future__ import annotations

import pytest

from app.modules.admin.entitlements import default_entitlements_for_tier
from app.modules.tenant_studio.custom_roles_store import MemCustomRolesStore
from app.modules.tenant_studio.permission_ceiling import (
    PermissionCeilingError,
    assert_within_ceiling,
    check_permissions_against_ceiling,
)


def test_starter_cannot_grant_ai_rag_privilege_escalation() -> None:
    starter = default_entitlements_for_tier("starter")
    result = check_permissions_against_ceiling(["crm.companies.read", "ai.rag.use"], starter)
    assert result.allowed is False
    assert "ai.rag.use" in result.rejected
    assert "DOM-011" in result.reasons["ai.rag.use"]


def test_growth_can_grant_ai_rag() -> None:
    growth = default_entitlements_for_tier("growth")
    capped = assert_within_ceiling(["crm.companies.read", "ai.rag.use", "ai.copilot.use"], growth)
    assert capped == ["crm.companies.read", "ai.rag.use", "ai.copilot.use"]


def test_marketplace_publish_requires_publish_flag() -> None:
    growth = default_entitlements_for_tier("growth")
    result = check_permissions_against_ceiling(["marketplace.publish"], growth)
    assert result.allowed is False
    assert "publish" in result.reasons["marketplace.publish"]

    enterprise = default_entitlements_for_tier("enterprise")
    capped = assert_within_ceiling(["marketplace.publish"], enterprise)
    assert capped == ["marketplace.publish"]


def test_owner_plane_keys_blocked() -> None:
    ents = default_entitlements_for_tier("enterprise")
    for key in ("admin", "manage_plans", "owner.admin", "*"):
        with pytest.raises(PermissionCeilingError, match="not grantable|unknown"):
            assert_within_ceiling([key], ents)


def test_unknown_permission_fail_closed() -> None:
    with pytest.raises(PermissionCeilingError, match="unknown"):
        assert_within_ceiling(
            ["not.a.real.permission"], default_entitlements_for_tier("enterprise")
        )


def test_store_upsert_rejects_escalation() -> None:
    store = MemCustomRolesStore()
    store.set_ceiling("t1", plan_tier="starter")
    with pytest.raises(PermissionCeilingError, match="ceiling"):
        store.upsert(
            tenant_id="t1",
            name="Hacker",
            permissions=["ai.rag.use"],
        )


def test_store_upsert_within_ceiling() -> None:
    store = MemCustomRolesStore()
    store.set_ceiling("t1", plan_tier="starter")
    role = store.upsert(
        tenant_id="t1",
        name="Seller",
        permissions=["crm.companies.read", "crm.contacts.read", "studio.configure"],
    )
    assert role.permissions == [
        "crm.companies.read",
        "crm.contacts.read",
        "studio.configure",
    ]
    assert store.get(role.id, tenant_id="t1") is not None
    assert store.get(role.id, tenant_id="t2") is None


def test_plan_downgrade_blocks_existing_grant_on_update() -> None:
    """Privilege-escalation: after downgrade, re-upsert with AI perms fails."""
    store = MemCustomRolesStore()
    store.set_ceiling("t1", plan_tier="growth")
    role = store.upsert(
        tenant_id="t1",
        name="Analyst",
        permissions=["ai.rag.use"],
    )
    store.set_ceiling("t1", plan_tier="starter")
    with pytest.raises(PermissionCeilingError):
        store.upsert(
            tenant_id="t1",
            name="Analyst",
            permissions=["ai.rag.use"],
            role_id=role.id,
        )


def test_tenant_isolation() -> None:
    store = MemCustomRolesStore()
    a = store.upsert(
        tenant_id="tenant-a",
        name="A",
        permissions=["crm.companies.read"],
        plan_tier="starter",
    )
    assert store.list_for_tenant(tenant_id="tenant-b") == []
    assert store.get(a.id, tenant_id="tenant-b") is None
