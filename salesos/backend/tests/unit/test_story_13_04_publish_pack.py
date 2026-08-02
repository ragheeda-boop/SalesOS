"""STORY-13-04 — Publish pack (≥3 connectors + ≥1 playbook)."""

from __future__ import annotations

import pytest

from app.modules.integration_hub.second_connector import (
    build_certifiable_adapter,
    certify_named_connector,
)
from app.modules.marketplace_listings.catalog_install import MemCatalogInstallStore
from app.modules.marketplace_listings.models import MarketplaceListingError
from app.modules.marketplace_listings.pipeline import run_certification_pipeline
from app.modules.marketplace_listings.publish import publish_listing
from app.modules.marketplace_listings.store import MemMarketplaceListingStore


def test_seed_publish_pack_shape() -> None:
    store = MemMarketplaceListingStore()
    rows = store.seed_publish_pack()
    assert len(rows) == 4
    connectors = [r for r in rows if r.listing_type == "connector"]
    playbooks = [r for r in rows if r.listing_type == "playbook"]
    assert len(connectors) == 3
    assert len(playbooks) == 1
    assert {c.connector_key for c in connectors} == {"odoo", "hubspot", "rest_csv"}
    assert all(r.status == "published" for r in rows)
    assert all(r.manifest.get("installable") is True for r in rows)
    assert all(r.manifest.get("certified") is True for r in rows)
    assert all(r.first_party for r in rows)
    # idempotent
    again = store.seed_publish_pack()
    assert len(store.list_listings()) == 4
    assert {r.slug for r in again} == {
        "connector-odoo",
        "connector-hubspot",
        "connector-rest-csv",
        "playbook-gcc-outbound",
    }


def test_seed_first_party_alias() -> None:
    store = MemMarketplaceListingStore()
    assert len(store.seed_first_party_connectors()) == 4


@pytest.mark.asyncio
async def test_rest_csv_certifies() -> None:
    adapter = build_certifiable_adapter("rest_csv")
    assert adapter.connector_key == "rest_csv"
    result = await certify_named_connector("rest_csv")
    assert result.get("ok") is True


@pytest.mark.asyncio
async def test_rest_csv_listing_pipeline() -> None:
    store = MemMarketplaceListingStore()
    row = store.upsert(
        slug="connector-rest-csv-draft",
        name="REST/CSV",
        listing_type="connector",
        version="1.0.0",
        connector_key="rest_csv",
        status="draft",
    )
    report = await run_certification_pipeline(store, row.id)
    assert report.ok is True
    assert report.status_after == "certified"
    published = publish_listing(store, row.id)
    assert published.status == "published"
    assert published.manifest.get("installable") is True


def test_catalog_install_tenant_scoped() -> None:
    store = MemMarketplaceListingStore()
    pack = store.seed_publish_pack()
    listing = next(r for r in pack if r.slug == "playbook-gcc-outbound")
    installs = MemCatalogInstallStore()
    a = installs.install(listing, tenant_id="tenant-a")
    b = installs.install(listing, tenant_id="tenant-b")
    assert a.tenant_id == "tenant-a"
    assert b.tenant_id == "tenant-b"
    assert len(installs.list_for_tenant(tenant_id="tenant-a")) == 1
    assert len(installs.list_for_tenant(tenant_id="tenant-b")) == 1
    # idempotent per tenant
    again = installs.install(listing, tenant_id="tenant-a")
    assert again.id == a.id


def test_draft_not_installable() -> None:
    store = MemMarketplaceListingStore()
    row = store.upsert(
        slug="playbook-draft",
        name="Draft",
        listing_type="playbook",
        version="1.0.0",
        status="draft",
    )
    installs = MemCatalogInstallStore()
    with pytest.raises(MarketplaceListingError, match="installable"):
        installs.install(row, tenant_id="tenant-a")


def test_publish_requires_certified() -> None:
    store = MemMarketplaceListingStore()
    row = store.upsert(
        slug="app-draft",
        name="App",
        listing_type="app",
        version="1.0.0",
        status="draft",
    )
    with pytest.raises(MarketplaceListingError, match="certified"):
        publish_listing(store, row.id)
