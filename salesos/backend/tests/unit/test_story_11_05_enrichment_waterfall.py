"""STORY-11-05 — Enrichment Waterfall (≥2 swappable providers)."""

from __future__ import annotations

import pytest

from app.modules.gtm.enrichment import EnrichmentError, normalize_request
from app.modules.gtm.enrichment_engine import (
    MemEnrichmentProvider,
    build_default_providers,
    run_waterfall,
)
from app.modules.gtm.enrichment_store import MemEnrichmentStore


@pytest.mark.asyncio
async def test_waterfall_uses_two_providers_first_wins() -> None:
    providers = build_default_providers()
    assert len(providers) >= 2
    req = normalize_request(company_name="Acme", domain="acme.sa")
    filled, hits, attempted, configured = await run_waterfall(req, providers)
    assert set(configured) >= {"fake_a", "fake_b"}
    assert "fake_a" in attempted and "fake_b" in attempted
    assert filled["industry"] == "technology"
    assert filled["city"] == "riyadh"  # A wins over B's jeddah
    assert filled["email"] == "hello@acme.sa"
    assert filled["phone"] == "+966500000001"
    by_field = {h.field: h.provider_key for h in hits}
    assert by_field["industry"] == "fake_a"
    assert by_field["email"] == "fake_b"
    assert by_field["city"] == "fake_a"


@pytest.mark.asyncio
async def test_provider_order_override() -> None:
    providers = build_default_providers()
    req = normalize_request(
        company_name="Acme",
        domain="acme.sa",
        provider_order=["fake_b", "fake_a"],
    )
    filled, hits, attempted, _ = await run_waterfall(req, providers)
    assert attempted[0] == "fake_b"
    by_field = {h.field: h.provider_key for h in hits}
    assert by_field["city"] == "fake_b"  # B first → jeddah sticks
    assert filled["city"] == "jeddah"


@pytest.mark.asyncio
async def test_known_values_not_overwritten() -> None:
    providers = build_default_providers()
    req = normalize_request(
        company_name="Acme",
        domain="acme.sa",
        known={"city": "dammam"},
    )
    filled, hits, _, _ = await run_waterfall(req, providers)
    assert filled["city"] == "dammam"
    assert all(h.field != "city" for h in hits)


@pytest.mark.asyncio
async def test_store_tenant_isolation_and_meta_providers() -> None:
    store = MemEnrichmentStore()
    assert len(store.provider_keys()) >= 2
    row = await store.enrich(
        tenant_id="pilot-1",
        company_name="Acme",
        domain="acme.sa",
    )
    assert store.get(row.id, tenant_id="pilot-1") is not None
    assert store.get(row.id, tenant_id="other") is None
    assert store.list_for_tenant(tenant_id="other") == []


def test_requires_company_name() -> None:
    with pytest.raises(EnrichmentError, match="company_name"):
        normalize_request(company_name="  ")


@pytest.mark.asyncio
async def test_requires_two_providers() -> None:
    solo = [
        MemEnrichmentProvider(key="only", catalog={}, supported_fields=("city",)),
    ]
    with pytest.raises(EnrichmentError, match="at least 2"):
        await run_waterfall(normalize_request(company_name="X"), solo)
