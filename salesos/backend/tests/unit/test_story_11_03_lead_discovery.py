"""STORY-11-03 — Lead Discovery (gov-first + Integration Hub fallback)."""

from __future__ import annotations

import pytest

from app.modules.gtm.lead_discovery import (
    SOURCE_GOVERNMENT,
    LeadDiscoveryError,
    normalize_query,
)
from app.modules.gtm.lead_discovery_engine import discover_leads, search_government
from app.modules.gtm.lead_discovery_store import (
    MemLeadDiscoveryStore,
    seed_fake_provider_companies,
)
from app.modules.gtm.market_sizing import GOVERNMENT_DATASET_SCALE_HINT, CompanyRecord
from app.modules.gtm.market_sizing_engine import MemCompanyUniverse
from app.modules.gtm.market_sizing_store import build_demo_government_universe
from app.modules.integration_hub.fake_adapter import FakeSourceConnector


def _tiny_universe() -> MemCompanyUniverse:
    return MemCompanyUniverse(
        records=[
            CompanyRecord("1", "technology", "riyadh", 50),
            CompanyRecord("2", "technology", "jeddah", 80),
            CompanyRecord("3", "construction", "riyadh", 40),
        ]
    )


@pytest.mark.asyncio
async def test_government_first_then_provider_fallback() -> None:
    """Gov hits precede provider; provider fills remaining limit."""
    uni = MemCompanyUniverse(records=[CompanyRecord("g1", "technology", "riyadh", 50)])
    fake = FakeSourceConnector()
    await seed_fake_provider_companies(fake)
    query = normalize_query(industries=["technology"], cities=["riyadh"], limit=5)
    leads, gov_n, prov_n, key = await discover_leads(
        query=query,
        universe=uni,
        provider=fake,
    )
    assert gov_n == 1
    assert prov_n >= 1
    assert key == "fake"
    assert leads[0].source == SOURCE_GOVERNMENT
    assert all(
        lead.source == SOURCE_GOVERNMENT or lead.source.startswith("provider:") for lead in leads
    )
    # first contiguous block is government
    first_provider_idx = next(
        (i for i, lead in enumerate(leads) if lead.source.startswith("provider:")),
        len(leads),
    )
    assert all(leads[i].source == SOURCE_GOVERNMENT for i in range(first_provider_idx))


@pytest.mark.asyncio
async def test_provider_only_when_government_empty() -> None:
    uni = MemCompanyUniverse(records=[])
    fake = FakeSourceConnector()
    await seed_fake_provider_companies(fake)
    query = normalize_query(industries=["technology"], limit=10)
    leads, gov_n, prov_n, _ = await discover_leads(
        query=query,
        universe=uni,
        provider=fake,
    )
    assert gov_n == 0
    assert prov_n >= 1
    assert all(lead.source.startswith("provider:") for lead in leads)


def test_government_search_filters() -> None:
    hits = search_government(
        _tiny_universe(),
        normalize_query(industries=["technology"], cities=["riyadh"], limit=10),
    )
    assert len(hits) == 1
    assert hits[0].external_id == "1"
    assert hits[0].source == SOURCE_GOVERNMENT


@pytest.mark.asyncio
async def test_store_discover_demo_universe_and_isolation() -> None:
    store = MemLeadDiscoveryStore()
    store.bind_universe(build_demo_government_universe())
    fake = FakeSourceConnector()
    await seed_fake_provider_companies(fake)
    store.bind_provider(fake)

    run = await store.discover(
        tenant_id="pilot-1",
        name="Tech Riyadh",
        industries=["technology"],
        cities=["riyadh"],
        limit=10,
    )
    assert run.dataset_scale_hint == GOVERNMENT_DATASET_SCALE_HINT
    assert run.government_hit_count >= 1
    assert run.government_first_ok
    assert store.get(run.id, tenant_id="pilot-1") is not None
    assert store.get(run.id, tenant_id="other") is None
    assert store.list_for_tenant(tenant_id="other") == []


def test_reject_bad_limit() -> None:
    with pytest.raises(LeadDiscoveryError, match="limit"):
        normalize_query(limit=0)
