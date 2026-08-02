"""STORY-13-04 — Publish certified MarketplaceListing to live catalog."""

from __future__ import annotations

from datetime import UTC, datetime

from app.modules.marketplace_listings.models import (
    MarketplaceListing,
    MarketplaceListingError,
)
from app.modules.marketplace_listings.store import MemMarketplaceListingStore

_PUBLISH_FROM = frozenset({"certified"})


def publish_listing(
    store: MemMarketplaceListingStore,
    listing_id: str,
) -> MarketplaceListing:
    row = store.get(listing_id) or store.get_by_slug(listing_id)
    if row is None:
        raise MarketplaceListingError("marketplace listing not found")
    if row.status not in _PUBLISH_FROM and row.status != "published":
        raise MarketplaceListingError(
            f"cannot publish from status={row.status}; expected certified"
        )
    if row.status == "published":
        return row
    return store.upsert(
        listing_id=row.id,
        slug=row.slug,
        name=row.name,
        listing_type=row.listing_type,
        version=row.version,
        status="published",
        description=row.description,
        publisher=row.publisher,
        first_party=row.first_party,
        connector_key=row.connector_key,
        tags=list(row.tags),
        manifest={
            **row.manifest,
            "installable": True,
            "certified": True,
            "published_at": datetime.now(UTC).isoformat(),
            "pipeline": row.manifest.get("pipeline") or "STORY-13-04",
        },
    )
