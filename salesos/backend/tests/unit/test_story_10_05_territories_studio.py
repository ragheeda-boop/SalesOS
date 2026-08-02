"""STORY-10-05 — Territory Rules Studio: geography/industry/size + assign."""

from __future__ import annotations

import pytest

from app.modules.tenant_studio.territories import (
    TerritoryRuleError,
    build_territory_rule,
)
from app.modules.tenant_studio.territories_engine import assign_territory
from app.modules.tenant_studio.territories_store import MemTerritoriesStore


def test_geography_rule_matches_region() -> None:
    store = MemTerritoriesStore()
    rule = store.upsert(
        tenant_id="t1",
        name="Riyadh North",
        territory_key="riyadh-north",
        region="Riyadh",
        rep_id="rep-1",
        priority=10,
        match_conditions=[{"field": "region", "op": "eq", "value": "Riyadh"}],
    )
    hit = store.assign(tenant_id="t1", attributes={"region": "Riyadh", "industry": "gov"})
    miss = store.assign(tenant_id="t1", attributes={"region": "Jeddah"})
    assert hit.matched is True
    assert hit.territory_key == "riyadh-north"
    assert hit.rule_id == rule.id
    assert hit.rep_id == "rep-1"
    assert hit.source == "tenant_rule"
    assert miss.matched is False
    assert miss.source == "unmatched"
    assert miss.territory_key is None


def test_industry_and_size_conditions() -> None:
    store = MemTerritoriesStore()
    store.upsert(
        tenant_id="t1",
        name="Enterprise Gov",
        territory_key="ent-gov",
        priority=5,
        match_conditions=[
            {"field": "industry", "op": "eq", "value": "government"},
            {"field": "employee_count", "op": "gte", "value": 500},
        ],
    )
    hit = store.assign(
        tenant_id="t1",
        attributes={"industry": "government", "employee_count": 800},
    )
    small = store.assign(
        tenant_id="t1",
        attributes={"industry": "government", "employee_count": 50},
    )
    assert hit.matched is True
    assert hit.territory_key == "ent-gov"
    assert small.matched is False


def test_priority_selects_lower_number() -> None:
    store = MemTerritoriesStore()
    store.upsert(
        tenant_id="t1",
        name="Broad",
        territory_key="broad",
        priority=50,
        match_conditions=[{"field": "country", "op": "eq", "value": "SA"}],
    )
    store.upsert(
        tenant_id="t1",
        name="Specific",
        territory_key="specific",
        priority=1,
        match_conditions=[
            {"field": "country", "op": "eq", "value": "SA"},
            {"field": "city", "op": "eq", "value": "Dammam"},
        ],
    )
    result = store.assign(
        tenant_id="t1",
        attributes={"country": "SA", "city": "Dammam"},
    )
    assert result.territory_key == "specific"


def test_tenant_isolation() -> None:
    store = MemTerritoriesStore()
    store.upsert(
        tenant_id="t1",
        name="T1",
        territory_key="t1-key",
        match_conditions=[{"field": "region", "op": "eq", "value": "X"}],
    )
    assert store.list_for_tenant(tenant_id="t2") == []
    assert store.get(store.list_for_tenant(tenant_id="t1")[0].id, tenant_id="t2") is None
    with pytest.raises(PermissionError):
        rid = store.list_for_tenant(tenant_id="t1")[0].id
        store.upsert(
            tenant_id="t2",
            name="Hijack",
            territory_key="x",
            match_conditions=[{"field": "region", "op": "eq", "value": "X"}],
            rule_id=rid,
        )


def test_empty_match_conditions_rejected() -> None:
    with pytest.raises(TerritoryRuleError, match="match_conditions"):
        build_territory_rule(
            tenant_id="t1",
            name="Bad",
            territory_key="k",
            match_conditions=[],
        )


def test_unmatched_does_not_invent_territory() -> None:
    result = assign_territory(rules=[], attributes={"region": "Riyadh"})
    assert result.matched is False
    assert result.territory_key is None
    assert result.source == "unmatched"


def test_delete_and_inactive_skip() -> None:
    store = MemTerritoriesStore()
    rule = store.upsert(
        tenant_id="t1",
        name="Temp",
        territory_key="temp",
        match_conditions=[{"field": "sector", "op": "eq", "value": "oil"}],
    )
    store.upsert(
        tenant_id="t1",
        name="Temp off",
        territory_key="temp",
        match_conditions=[{"field": "sector", "op": "eq", "value": "oil"}],
        active=False,
        rule_id=rule.id,
    )
    assert store.assign(tenant_id="t1", attributes={"sector": "oil"}).matched is False
    assert store.delete(rule.id, tenant_id="t1") is True
    assert store.get(rule.id, tenant_id="t1") is None
