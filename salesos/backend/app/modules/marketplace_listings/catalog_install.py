"""STORY-13-04 — Tenant catalog install for published MarketplaceListing.

In-memory install receipt only — proves installable pack mechanism.
Does not claim live HubSpot/Odoo/REST sync GO. Not domains/marketplace plugin install.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.modules.marketplace_listings.models import (
    MarketplaceListing,
    MarketplaceListingError,
)

_INSTALLABLE_STATUSES = frozenset({"published", "certified"})


@dataclass
class CatalogInstallRecord:
    id: str
    tenant_id: str
    listing_id: str
    listing_slug: str
    listing_type: str
    connector_key: str = ""
    installed_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "listing_id": self.listing_id,
            "listing_slug": self.listing_slug,
            "listing_type": self.listing_type,
            "connector_key": self.connector_key,
            "installed_at": self.installed_at,
            "honesty": (
                "Catalog install receipt only; live ERP/CRM sync not claimed. " "Not Production GO."
            ),
        }


@dataclass
class MemCatalogInstallStore:
    """Tenant-scoped installs — isolated by tenant_id (DEC-085 catalog scope)."""

    _by_tenant: dict[str, dict[str, CatalogInstallRecord]] = field(default_factory=dict)

    def install(
        self,
        listing: MarketplaceListing,
        *,
        tenant_id: str,
    ) -> CatalogInstallRecord:
        tid = (tenant_id or "").strip()
        if not tid:
            raise MarketplaceListingError("tenant_id required")
        if listing.status not in _INSTALLABLE_STATUSES:
            raise MarketplaceListingError(
                f"listing not installable from status={listing.status}; "
                f"expected one of {sorted(_INSTALLABLE_STATUSES)}"
            )
        if not listing.manifest.get("installable", listing.status in _INSTALLABLE_STATUSES):
            raise MarketplaceListingError("listing marked not installable")

        bucket = self._by_tenant.setdefault(tid, {})
        existing = bucket.get(listing.id)
        if existing:
            return existing

        rec = CatalogInstallRecord(
            id=uuid.uuid4().hex[:12],
            tenant_id=tid,
            listing_id=listing.id,
            listing_slug=listing.slug,
            listing_type=listing.listing_type,
            connector_key=listing.connector_key,
            installed_at=datetime.now(UTC).isoformat(),
        )
        bucket[listing.id] = rec
        return rec

    def list_for_tenant(self, *, tenant_id: str) -> list[CatalogInstallRecord]:
        tid = (tenant_id or "").strip()
        return sorted(
            self._by_tenant.get(tid, {}).values(),
            key=lambda r: (r.listing_type, r.listing_slug),
        )

    def is_installed(self, *, tenant_id: str, listing_id: str) -> bool:
        return listing_id in self._by_tenant.get((tenant_id or "").strip(), {})


DEFAULT_CATALOG_INSTALL_STORE = MemCatalogInstallStore()


def listing_is_installable(listing: MarketplaceListing) -> bool:
    if listing.status not in _INSTALLABLE_STATUSES:
        return False
    flag = listing.manifest.get("installable")
    if flag is None:
        return True
    return bool(flag)
