"""STORY-13-01 — In-memory MarketplaceListing store (no Alembic / FORCE RLS).

Owner-platform catalog scope (not tenant RLS tables).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.modules.marketplace_listings.models import (
    MarketplaceListing,
    MarketplaceListingError,
    build_marketplace_listing,
)


@dataclass
class MemMarketplaceListingStore:
    """Process-local MarketplaceListing catalog."""

    _by_id: dict[str, MarketplaceListing] = field(default_factory=dict)
    _slug_index: dict[str, str] = field(default_factory=dict)

    def upsert(
        self,
        *,
        slug: str,
        name: str,
        listing_type: str,
        version: str,
        status: str = "draft",
        description: str = "",
        publisher: str = "SalesOS",
        first_party: bool = True,
        connector_key: str = "",
        tags: list[str] | None = None,
        manifest: dict[str, Any] | None = None,
        listing_id: str | None = None,
    ) -> MarketplaceListing:
        now = datetime.now(UTC).isoformat()
        rid = (listing_id or "").strip()
        existing = self._by_id.get(rid) if rid else None
        slug_key = (slug or "").strip().lower()
        other_id = self._slug_index.get(slug_key)
        if other_id and (not existing or other_id != existing.id):
            raise MarketplaceListingError(f"slug already in use: {slug_key}")

        schema_version = 1
        created_at = now
        if existing:
            schema_version = max(existing.schema_version + 1, 1)
            created_at = existing.created_at or now
            if existing.slug != slug_key:
                self._slug_index.pop(existing.slug, None)
        else:
            rid = rid or uuid.uuid4().hex[:12]

        row = build_marketplace_listing(
            slug=slug_key,
            name=name,
            listing_type=listing_type,
            version=version,
            status=status,
            description=description,
            publisher=publisher,
            first_party=first_party,
            connector_key=connector_key,
            tags=tags,
            manifest=manifest,
            listing_id=rid,
            schema_version=schema_version,
        )
        row.created_at = created_at
        row.updated_at = now
        self._by_id[row.id] = row
        self._slug_index[row.slug] = row.id
        return row

    def get(self, listing_id: str) -> MarketplaceListing | None:
        return self._by_id.get(str(listing_id))

    def get_by_slug(self, slug: str) -> MarketplaceListing | None:
        rid = self._slug_index.get((slug or "").strip().lower())
        return self._by_id.get(rid) if rid else None

    def list(
        self,
        *,
        listing_type: str | None = None,
        status: str | None = None,
    ) -> list[MarketplaceListing]:
        rows = list(self._by_id.values())
        if listing_type:
            lt = listing_type.strip().lower()
            rows = [r for r in rows if r.listing_type == lt]
        if status:
            st = status.strip().lower()
            rows = [r for r in rows if r.status == st]
        return sorted(rows, key=lambda r: (r.listing_type, r.slug, r.version))

    def delete(self, listing_id: str) -> bool:
        row = self.get(listing_id)
        if row is None:
            return False
        del self._by_id[row.id]
        self._slug_index.pop(row.slug, None)
        return True

    def seed_first_party_connectors(self) -> list[MarketplaceListing]:
        """Seed Odoo + HubSpot listings (EPIC-08/11 certify paths)."""
        seeds = [
            {
                "slug": "connector-odoo",
                "name": "Odoo ERP Connector",
                "listing_type": "connector",
                "version": "1.0.0",
                "status": "certified",
                "description": "First-party Odoo SourceConnector (CI certified).",
                "connector_key": "odoo",
                "tags": ["erp", "odoo", "first-party"],
                "manifest": {"certify_key": "odoo", "pipeline": "STORY-13-02-deferred"},
            },
            {
                "slug": "connector-hubspot",
                "name": "HubSpot CRM Connector",
                "listing_type": "connector",
                "version": "1.0.0",
                "status": "certified",
                "description": "First-party HubSpot SourceConnector (CI certified).",
                "connector_key": "hubspot",
                "tags": ["crm", "hubspot", "first-party"],
                "manifest": {
                    "certify_key": "hubspot",
                    "pipeline": "STORY-13-02-deferred",
                    "honesty": "CI certification only; production pilot sync OPEN",
                },
            },
        ]
        out: list[MarketplaceListing] = []
        for spec in seeds:
            existing = self.get_by_slug(str(spec["slug"]))
            out.append(
                self.upsert(
                    listing_id=existing.id if existing else None,
                    **spec,  # type: ignore[arg-type]
                )
            )
        return out


DEFAULT_MARKETPLACE_LISTING_STORE = MemMarketplaceListingStore()
