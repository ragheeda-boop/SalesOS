"""STORY-04-03 / STORY-04-04 unit tests — suspension + retention helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.modules.identity.tenant_lifecycle_guard import (
    clear_deletion_requested,
    get_deletion_requested_at,
    is_tenant_suspended,
    path_skips_suspension_guard,
    retention_elapsed,
    stamp_deletion_requested,
)


def test_path_skips_admin_and_auth():
    assert path_skips_suspension_guard("/api/v1/admin/tenants") is True
    assert path_skips_suspension_guard("/api/v1/auth/login") is True
    assert path_skips_suspension_guard("/health") is True
    assert path_skips_suspension_guard("/api/v1/companies") is False


def test_is_tenant_suspended():
    assert is_tenant_suspended(None) is False
    assert is_tenant_suspended(SimpleNamespace(provisioning_status="active")) is False
    assert is_tenant_suspended(SimpleNamespace(provisioning_status="suspended")) is True


def test_retention_window():
    tenant = SimpleNamespace(settings={})
    stamp_deletion_requested(tenant, now=datetime(2026, 7, 1, tzinfo=UTC))
    assert get_deletion_requested_at(tenant) is not None
    assert (
        retention_elapsed(
            tenant,
            now=datetime(2026, 7, 10, tzinfo=UTC),
            retention_days=30,
        )
        is False
    )
    assert (
        retention_elapsed(
            tenant,
            now=datetime(2026, 8, 5, tzinfo=UTC),
            retention_days=30,
        )
        is True
    )
    clear_deletion_requested(tenant)
    assert get_deletion_requested_at(tenant) is None
    assert retention_elapsed(tenant, now=datetime.now(UTC), retention_days=30) is True


def test_stamp_idempotent_overwrite():
    tenant = SimpleNamespace(settings={"other": 1})
    t0 = datetime(2026, 6, 1, tzinfo=UTC)
    stamp_deletion_requested(tenant, now=t0)
    stamp_deletion_requested(tenant, now=t0 + timedelta(days=1))
    assert get_deletion_requested_at(tenant) == t0 + timedelta(days=1)
    assert tenant.settings["other"] == 1
