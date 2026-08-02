"""STORY-11-02 — TAM/SAM/SOM market sizing against company universe."""

from __future__ import annotations

import pytest

from app.modules.gtm.market_sizing import (
    GOVERNMENT_DATASET_SCALE_HINT,
    CompanyRecord,
    MarketSizingError,
    normalize_criteria,
)
from app.modules.gtm.market_sizing_engine import (
    MemCompanyUniverse,
    compute_tam_sam_som,
)
from app.modules.gtm.market_sizing_store import (
    MemMarketSizingStore,
    build_demo_government_universe,
)


def _universe() -> MemCompanyUniverse:
    return MemCompanyUniverse(
        records=[
            CompanyRecord("1", "technology", "riyadh", 50),
            CompanyRecord("2", "technology", "riyadh", 200),
            CompanyRecord("3", "technology", "jeddah", 80),
            CompanyRecord("4", "construction", "riyadh", 40),
            CompanyRecord("5", "healthcare", "dammam", 120),
            CompanyRecord("6", "technology", "riyadh", 10),
        ]
    )


def test_tam_sam_som_invariant_and_nesting() -> None:
    result = compute_tam_sam_som(
        normalize_criteria(
            industries=["technology"],
            cities=["riyadh"],
            employees_min=40,
            employees_max=100,
        ),
        _universe(),
    )
    assert result.tam == 4
    assert result.sam == 3
    assert result.som == 1
    assert result.invariant_ok
    assert result.som <= result.sam <= result.tam <= result.universe_size


def test_empty_filters_equals_universe() -> None:
    uni = _universe()
    result = compute_tam_sam_som(normalize_criteria(), uni)
    assert result.tam == result.sam == result.som == result.universe_size == 6


def test_dataset_scale_hint_constant() -> None:
    assert GOVERNMENT_DATASET_SCALE_HINT == 141_221


def test_store_compute_against_demo_gov_universe() -> None:
    store = MemMarketSizingStore()
    store.bind_universe(build_demo_government_universe())
    snap = store.compute(
        tenant_id="pilot-1",
        name="Tech Riyadh mid",
        industries=["technology"],
        cities=["riyadh"],
        employees_min=20,
        employees_max=200,
    )
    assert snap.dataset_scale_hint == 141_221
    assert snap.universe_size == 250
    assert snap.invariant_ok
    assert snap.som <= snap.sam <= snap.tam
    assert store.get(snap.id, tenant_id="pilot-1") is not None
    assert store.get(snap.id, tenant_id="other") is None


def test_reject_bad_employee_range() -> None:
    with pytest.raises(MarketSizingError, match="employees_min"):
        normalize_criteria(employees_min=100, employees_max=10)


def test_tenant_isolation_of_snapshots() -> None:
    store = MemMarketSizingStore()
    store.bind_universe(_universe())
    a = store.compute(tenant_id="t1", name="A", industries=["technology"])
    assert store.list_for_tenant(tenant_id="t2") == []
    assert store.get(a.id, tenant_id="t2") is None
