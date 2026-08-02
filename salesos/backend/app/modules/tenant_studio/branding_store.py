"""STORY-10-07 — In-memory Branding store (no Alembic / FORCE RLS)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.modules.tenant_studio.branding import (
    BrandingConfig,
    BrandingError,
    build_branding_config,
)


@dataclass
class MemBrandingStore:
    """Tenant-scoped branding configs for CAP-092 Studio."""

    _by_tenant: dict[str, BrandingConfig] = field(default_factory=dict)

    def get(self, *, tenant_id: str) -> BrandingConfig:
        tid = str(tenant_id).strip()
        if not tid:
            raise BrandingError("tenant_id required")
        existing = self._by_tenant.get(tid)
        if existing:
            return existing
        # Default empty branding — FE can render platform defaults.
        return build_branding_config(tenant_id=tid, display_name="")

    def upsert(
        self,
        *,
        tenant_id: str,
        display_name: str = "",
        logo_url: str = "",
        primary_color: str = "#0F172A",
        secondary_color: str = "#334155",
        default_locale: str = "ar",
        supported_locales: list[str] | None = None,
    ) -> BrandingConfig:
        tid = str(tenant_id).strip()
        if not tid:
            raise BrandingError("tenant_id required")
        now = datetime.now(UTC).isoformat()
        existing = self._by_tenant.get(tid)
        schema_version = 1
        created_at = now
        if existing:
            schema_version = max(existing.schema_version + 1, 1)
            created_at = existing.created_at or now

        row = build_branding_config(
            tenant_id=tid,
            display_name=display_name,
            logo_url=logo_url,
            primary_color=primary_color,
            secondary_color=secondary_color,
            default_locale=default_locale,
            supported_locales=supported_locales,
            schema_version=schema_version,
        )
        row.created_at = created_at
        row.updated_at = now
        self._by_tenant[tid] = row
        return row


DEFAULT_BRANDING_STORE = MemBrandingStore()
