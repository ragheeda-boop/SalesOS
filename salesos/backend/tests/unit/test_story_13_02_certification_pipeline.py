"""STORY-13-02 — CAP-094 certification pipeline."""

from __future__ import annotations

import pytest

from app.modules.marketplace_listings.models import MarketplaceListingError
from app.modules.marketplace_listings.pipeline import (
    run_certification_pipeline,
    submit_for_certification,
)
from app.modules.marketplace_listings.security_checklist import run_security_checklist
from app.modules.marketplace_listings.store import MemMarketplaceListingStore
from app.modules.marketplace_listings.trial_sandbox import CertificationTrialSandbox


@pytest.mark.asyncio
async def test_hubspot_listing_certifies() -> None:
    store = MemMarketplaceListingStore()
    row = store.upsert(
        slug="connector-hubspot-trial",
        name="HubSpot",
        listing_type="connector",
        version="1.0.0",
        connector_key="hubspot",
        status="draft",
        first_party=True,
    )
    report = await run_certification_pipeline(
        store,
        row.id,
        real_tenant_ids=["tenant-real-a", "tenant-real-b"],
    )
    assert report.ok is True
    assert report.status_after == "certified"
    stages = {s.stage: s.ok for s in report.stages}
    assert stages == {
        "conformance": True,
        "security_checklist": True,
        "sandboxed_trial": True,
    }
    assert store.get(row.id).status == "certified"


@pytest.mark.asyncio
async def test_negative_broken_connector_rejected() -> None:
    store = MemMarketplaceListingStore()
    row = store.upsert(
        slug="connector-broken",
        name="Broken",
        listing_type="connector",
        version="1.0.0",
        connector_key="broken",
        status="draft",
    )
    report = await run_certification_pipeline(store, row.id)
    assert report.ok is False
    assert report.status_after == "rejected"
    conf = next(s for s in report.stages if s.stage == "conformance")
    assert conf.ok is False


@pytest.mark.asyncio
async def test_unknown_connector_rejected() -> None:
    store = MemMarketplaceListingStore()
    row = store.upsert(
        slug="connector-unknown",
        name="Unknown",
        listing_type="connector",
        version="1.0.0",
        connector_key="sap-not-wired",
        status="draft",
    )
    report = await run_certification_pipeline(store, row.id)
    assert report.ok is False
    assert report.status_after == "rejected"


def test_security_checklist_rejects_secret_manifest() -> None:
    store = MemMarketplaceListingStore()
    row = store.upsert(
        slug="app-leaky",
        name="Leaky",
        listing_type="app",
        version="1.0.0",
        manifest={"api_key": "sk-live-should-fail"},
    )
    result = run_security_checklist(row)
    assert result.ok is False
    assert result.as_dict()["first_party_exception"] is False
    assert any(i.id == "no_secrets_in_manifest" and not i.ok for i in result.items)


def test_security_checklist_applies_to_first_party() -> None:
    store = MemMarketplaceListingStore()
    row = store.upsert(
        slug="connector-odoo-fp",
        name="Odoo",
        listing_type="connector",
        version="1.0.0",
        connector_key="odoo",
        first_party=True,
    )
    result = run_security_checklist(row)
    assert result.ok is True
    assert any(i.id == "no_first_party_bypass" and i.ok for i in result.items)


def test_trial_sandbox_no_leak_to_real_tenants() -> None:
    store = MemMarketplaceListingStore()
    row = store.upsert(
        slug="playbook-trial",
        name="Playbook",
        listing_type="playbook",
        version="1.0.0",
    )
    box = CertificationTrialSandbox()
    # Pre-seed empty real tenant bucket
    box._installs["tenant-real"] = []
    detail = box.run_trial(row, real_tenant_ids=["tenant-real"])
    assert detail["ok"] is True
    assert detail["not_domains_marketplace_sandbox"] is True
    assert box.installs_for("tenant-real") == []
    assert box.installs_for(detail["trial_tenant_id"])


def test_submit_status_machine() -> None:
    store = MemMarketplaceListingStore()
    row = store.upsert(
        slug="app-submit",
        name="App",
        listing_type="app",
        version="1.0.0",
        status="draft",
    )
    pending = submit_for_certification(store, row.id)
    assert pending.status == "pending_certification"
    with pytest.raises(MarketplaceListingError, match="cannot submit"):
        submit_for_certification(store, pending.id)


@pytest.mark.asyncio
async def test_secret_manifest_fails_pipeline_even_if_conformance_skips() -> None:
    store = MemMarketplaceListingStore()
    row = store.upsert(
        slug="prompt-bad",
        name="Bad prompts",
        listing_type="prompt_pack",
        version="1.0.0",
        manifest={"client_secret": "x"},
    )
    report = await run_certification_pipeline(store, row.id)
    assert report.ok is False
    assert report.status_after == "rejected"
    sec = next(s for s in report.stages if s.stage == "security_checklist")
    assert sec.ok is False
