"""STORY-11-01 — Versioned ICPProfile + deterministic scoring."""

from __future__ import annotations

import pytest

from app.modules.gtm.icp import ICPError, normalize_criteria
from app.modules.gtm.icp_engine import score_company_against_profile
from app.modules.gtm.icp_store import MemICPStore


def test_create_list_get_reusable_across_sessions() -> None:
    store = MemICPStore()
    created = store.create(
        tenant_id="pilot-1",
        name="Tech Riyadh mid-market",
        industries=["technology"],
        cities=["riyadh"],
        employees_min=20,
        employees_max=200,
    )
    assert created.schema_version == 1
    assert store.get(created.id, tenant_id="pilot-1") is not None
    assert store.get(created.id, tenant_id="other") is None
    listed = store.list_for_tenant(tenant_id="pilot-1")
    assert len(listed) == 1
    assert listed[0].id == created.id


def test_update_bumps_schema_version() -> None:
    store = MemICPStore()
    row = store.create(tenant_id="t1", name="A", industries=["technology"])
    updated = store.update(row.id, tenant_id="t1", cities=["riyadh"])
    assert updated.schema_version == 2
    assert updated.criteria.cities == ["riyadh"]
    assert updated.criteria.industries == ["technology"]


def test_score_prefers_matching_bands() -> None:
    store = MemICPStore()
    row = store.create(
        tenant_id="t1",
        name="Fit",
        industries=["technology"],
        cities=["riyadh"],
        employees_min=40,
        employees_max=100,
    )
    hit = store.score(
        row.id,
        tenant_id="t1",
        company={"industry": "technology", "city": "riyadh", "employees_count": 50},
    )
    miss = store.score(
        row.id,
        tenant_id="t1",
        company={"industry": "retail", "city": "jeddah", "employees_count": 10},
    )
    assert hit.fit_ratio > miss.fit_ratio
    assert hit.matched["industry"] is True
    assert miss.matched["industry"] is False


def test_score_uses_profile_schema_version() -> None:
    store = MemICPStore()
    row = store.create(tenant_id="t1", name="V", industries=["technology"])
    store.update(row.id, tenant_id="t1", cities=["riyadh"])
    result = score_company_against_profile(
        store.get(row.id, tenant_id="t1"),  # type: ignore[arg-type]
        {"industry": "technology", "city": "riyadh"},
    )
    assert result.schema_version == 2


def test_reject_bad_employee_range() -> None:
    with pytest.raises(ICPError, match="employees_min"):
        normalize_criteria(employees_min=100, employees_max=10)


def test_tenant_isolation() -> None:
    store = MemICPStore()
    a = store.create(tenant_id="t1", name="A")
    assert store.list_for_tenant(tenant_id="t2") == []
    with pytest.raises(KeyError):
        store.update(a.id, tenant_id="t2", name="hack")
