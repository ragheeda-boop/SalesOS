"""STORY-04-03 / STORY-04-04 — suspended write guard + soft-delete retention helpers.

DEC-085 untouched. No Production GO.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.identity.models import Tenant

WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Owner Platform + auth + health — must remain reachable when a tenant is suspended.
# Public identity auth must skip: X-Tenant-Id on register previously triggered an
# unbounded fetch_tenant_by_id BEFORE the route handler (no register_* logs).
SKIP_PATH_PREFIXES = (
    "/health",
    "/ready",
    "/live",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/admin",
    "/api/v1/auth",
    "/api/v1/owner",
    "/api/v1/identity/register",
    "/api/v1/identity/login",
    "/api/v1/identity/refresh",
    "/api/v1/identity/forgot-password",
    "/api/v1/identity/reset-password",
    "/api/v1/billing/stripe/webhook",
    "/api/health",
)

DELETION_REQUESTED_AT_KEY = "deletion_requested_at"


def path_skips_suspension_guard(path: str) -> bool:
    path = path.split("?", 1)[0]
    return any(path == p or path.startswith(p + "/") for p in SKIP_PATH_PREFIXES)


def is_tenant_suspended(tenant: Tenant | None) -> bool:
    if tenant is None:
        return False
    return (tenant.provisioning_status or "") == "suspended"


def suspension_write_blocked_detail() -> str:
    return (
        "Tenant is suspended (read-only). "
        "Owner Platform must activate before writes are allowed."
    )


def get_deletion_requested_at(tenant: Tenant) -> datetime | None:
    """Prefer ``tenants.deleted_at``; fall back to settings stamp (pre-column rows)."""
    col = getattr(tenant, "deleted_at", None)
    if isinstance(col, datetime):
        dt = col
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    raw = (tenant.settings or {}).get(DELETION_REQUESTED_AT_KEY)
    if not raw or not isinstance(raw, str):
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def stamp_deletion_requested(tenant: Tenant, *, now: datetime | None = None) -> None:
    """Dual-write column + settings during STORY-04-04 column cutover."""
    clock = now or datetime.now(UTC)
    tenant.deleted_at = clock
    data = dict(tenant.settings or {})
    data[DELETION_REQUESTED_AT_KEY] = clock.isoformat()
    tenant.settings = data


def clear_deletion_requested(tenant: Tenant) -> None:
    tenant.deleted_at = None
    data = dict(tenant.settings or {})
    data.pop(DELETION_REQUESTED_AT_KEY, None)
    tenant.settings = data


def retention_elapsed(
    tenant: Tenant,
    *,
    now: datetime | None = None,
    retention_days: int | None = None,
) -> bool:
    """True when soft-delete retention window has passed (or no stamp → allow)."""
    requested = get_deletion_requested_at(tenant)
    if requested is None:
        return True
    days = (
        retention_days
        if retention_days is not None
        else int(getattr(settings, "tenant_deletion_retention_days", 30))
    )
    clock = now or datetime.now(UTC)
    return clock >= requested + timedelta(days=days)


async def load_tenant(db: AsyncSession, tenant_id: str) -> Tenant | None:
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        return None
    return await db.get(Tenant, tid)


async def fetch_tenant_by_id(db: AsyncSession, tenant_id: str) -> Tenant | None:
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        return None
    result = await db.execute(select(Tenant).where(Tenant.id == tid))
    return result.scalar_one_or_none()


def lifecycle_settings_snapshot(tenant: Tenant) -> dict[str, Any]:
    requested = get_deletion_requested_at(tenant)
    return {
        "provisioning_status": tenant.provisioning_status,
        "is_active": tenant.is_active,
        "deleted_at": requested.isoformat() if requested else None,
        "deletion_requested_at": (tenant.settings or {}).get(DELETION_REQUESTED_AT_KEY),
    }
