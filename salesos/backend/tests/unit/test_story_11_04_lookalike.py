"""STORY-11-04 — Lookalike Accounts (won/lost Opportunity-shaped history)."""

from __future__ import annotations

import pytest

from app.modules.gtm.lookalike import LookalikeError, OpportunityRecord, normalize_seed
from app.modules.gtm.lookalike_engine import (
    MemOpportunityHistory,
    build_demo_opportunity_history,
    rank_lookalikes,
)
from app.modules.gtm.lookalike_store import MemLookalikeStore


def test_rank_prefers_matching_won_accounts() -> None:
    hist = build_demo_opportunity_history(tenant_id="t1")
    seed = normalize_seed(
        company_name="Seed Tech",
        industry="technology",
        city="riyadh",
        employees_count=70,
    )
    hits, won_n, lost_n = rank_lookalikes(seed, hist, tenant_id="t1", limit=5)
    assert won_n >= 1 and lost_n >= 1
    assert len(hits) >= 1
    assert hits[0].similarity >= hits[-1].similarity
    assert "industry" in hits[0].matched_features or hits[0].industry == "technology"


def test_empty_history_rejected() -> None:
    hist = MemOpportunityHistory(records=[])
    seed = normalize_seed(company_name="X", industry="technology")
    with pytest.raises(LookalikeError, match="empty"):
        rank_lookalikes(seed, hist, tenant_id="t1")


def test_store_reusable_and_tenant_isolated() -> None:
    store = MemLookalikeStore()
    store.bind_history(build_demo_opportunity_history(tenant_id=""))
    row = store.run(
        tenant_id="pilot-1",
        name="Tech lookalikes",
        company_name="Seed",
        industry="technology",
        city="riyadh",
        employees_count=80,
        limit=5,
    )
    assert row.trained_on_won >= 1
    assert row.schema_version == 1
    assert store.get(row.id, tenant_id="pilot-1") is not None
    assert store.get(row.id, tenant_id="other") is None
    assert store.list_for_tenant(tenant_id="other") == []


def test_update_bumps_schema_version() -> None:
    store = MemLookalikeStore()
    a = store.run(
        tenant_id="t1",
        name="A",
        company_name="Seed",
        industry="technology",
        model_id="fixed-id",
    )
    b = store.run(
        tenant_id="t1",
        name="A2",
        company_name="Seed",
        industry="healthcare",
        model_id="fixed-id",
    )
    assert a.id == b.id
    assert b.schema_version == 2


def test_reject_blank_seed_name() -> None:
    with pytest.raises(LookalikeError, match="company_name"):
        normalize_seed(company_name="  ")


def test_tenant_scoped_history() -> None:
    hist = MemOpportunityHistory(
        records=[
            OpportunityRecord("1", "Only T1", "technology", "riyadh", 50, "won", "t1"),
        ]
    )
    seed = normalize_seed(company_name="Seed", industry="technology", city="riyadh")
    with pytest.raises(LookalikeError, match="empty"):
        rank_lookalikes(seed, hist, tenant_id="t2")
