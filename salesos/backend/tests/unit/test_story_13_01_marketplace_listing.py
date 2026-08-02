"""STORY-13-01 — MarketplaceListing single object across types."""

from __future__ import annotations

import pytest

from app.modules.marketplace_listings.models import (
    MarketplaceListingError,
    build_marketplace_listing,
)
from app.modules.marketplace_listings.store import MemMarketplaceListingStore


def test_connector_requires_key() -> None:
    with pytest.raises(MarketplaceListingError, match="connector_key"):
        build_marketplace_listing(
            slug="x",
            name="X",
            listing_type="connector",
            version="1.0.0",
        )


def test_playbook_rejects_connector_key() -> None:
    with pytest.raises(MarketplaceListingError, match="connector_key only"):
        build_marketplace_listing(
            slug="pb",
            name="Playbook",
            listing_type="playbook",
            version="1.0.0",
            connector_key="odoo",
        )


def test_single_object_across_types() -> None:
    store = MemMarketplaceListingStore()
    c = store.upsert(
        slug="connector-odoo",
        name="Odoo",
        listing_type="connector",
        version="1.0.0",
        connector_key="odoo",
        status="certified",
    )
    p = store.upsert(
        slug="playbook-meddic",
        name="MEDDIC",
        listing_type="playbook",
        version="1.0.0",
        status="draft",
    )
    a = store.upsert(
        slug="app-prompts-gcc",
        name="GCC Prompts",
        listing_type="prompt_pack",
        version="0.1.0",
    )
    assert {c.listing_type, p.listing_type, a.listing_type} == {
        "connector",
        "playbook",
        "prompt_pack",
    }
    assert len(store.list_listings()) == 3
    assert len(store.list_listings(listing_type="connector")) == 1


def test_slug_unique() -> None:
    store = MemMarketplaceListingStore()
    store.upsert(
        slug="dup",
        name="A",
        listing_type="app",
        version="1.0.0",
    )
    with pytest.raises(MarketplaceListingError, match="slug"):
        store.upsert(
            slug="dup",
            name="B",
            listing_type="app",
            version="1.0.1",
        )


def test_seed_first_party_odoo_hubspot() -> None:
    store = MemMarketplaceListingStore()
    rows = store.seed_first_party_connectors()
    assert len(rows) == 2
    keys = {r.connector_key for r in rows}
    assert keys == {"odoo", "hubspot"}
    assert all(r.listing_type == "connector" for r in rows)
    assert all(r.status == "certified" for r in rows)
    assert all(r.first_party for r in rows)
    # idempotent
    again = store.seed_first_party_connectors()
    assert len(store.list_listings()) == 2
    assert {r.slug for r in again} == {"connector-odoo", "connector-hubspot"}


def test_semver_required() -> None:
    with pytest.raises(MarketplaceListingError, match="semver"):
        build_marketplace_listing(
            slug="x",
            name="X",
            listing_type="app",
            version="1.0",
        )
