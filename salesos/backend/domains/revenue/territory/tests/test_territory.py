"""Tests for Revenue Territory Planning Domain."""

from datetime import datetime, timezone

import pytest

from domains.revenue.territory.models import (
    CoverageAnalysis, CoverageGap, LoadBalanceRecommendation,
    Territory, TerritorySummary,
)
from domains.revenue.territory.in_memory_repo import InMemoryTerritoryRepository
from domains.revenue.territory.service import TerritoryService


# ── Model Tests ──

def test_territory_account_count():
    t = Territory(id="t1", tenant_id="ten1", name="Riyadh North", account_ids=["a1", "a2", "a3"])
    assert t.account_count == 3


def test_territory_empty_accounts():
    t = Territory(id="t1", tenant_id="ten1", name="Empty")
    assert t.account_count == 0


# ── Service Tests ──

@pytest.mark.asyncio
async def test_create_territory():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    t = await svc.create_territory("ten1", "Riyadh North", region="Riyadh", rep_id="r1", rep_name="Ahmed")
    assert t.tenant_id == "ten1"
    assert t.name == "Riyadh North"
    assert t.region == "Riyadh"


@pytest.mark.asyncio
async def test_list_territories():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    await svc.create_territory("ten1", "Riyadh North", rep_id="r1")
    await svc.create_territory("ten1", "Riyadh South", rep_id="r2")
    items = await svc.list_territories("ten1")
    assert len(items) == 2


@pytest.mark.asyncio
async def test_list_territories_by_rep():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    await svc.create_territory("ten1", "Riyadh", rep_id="r1")
    await svc.create_territory("ten1", "Jeddah", rep_id="r2")
    items = await svc.list_territories("ten1", rep_id="r1")
    assert len(items) == 1
    assert items[0].rep_id == "r1"


@pytest.mark.asyncio
async def test_list_territories_by_region():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    await svc.create_territory("ten1", "North", region="Riyadh")
    await svc.create_territory("ten1", "South", region="Riyadh")
    await svc.create_territory("ten1", "East", region="Jeddah")
    items = await svc.list_territories("ten1", region="Riyadh")
    assert len(items) == 2


@pytest.mark.asyncio
async def test_update_territory():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    t = await svc.create_territory("ten1", "Old Name", rep_id="r1")
    updated = await svc.update_territory(t.id, name="New Name", rep_id="r2")
    assert updated.name == "New Name"
    assert updated.rep_id == "r2"


@pytest.mark.asyncio
async def test_update_territory_not_found():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    with pytest.raises(ValueError, match="not found"):
        await svc.update_territory("nonexistent", name="X")


@pytest.mark.asyncio
async def test_delete_territory():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    t = await svc.create_territory("ten1", "Delete Me")
    result = await svc.delete_territory(t.id)
    assert result is True
    assert await svc.get_territory(t.id) is None


@pytest.mark.asyncio
async def test_delete_territory_not_found():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    result = await svc.delete_territory("nonexistent")
    assert result is False


@pytest.mark.asyncio
async def test_assign_accounts():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    t = await svc.create_territory("ten1", "Riyadh")
    updated = await svc.assign_accounts(t.id, ["a1", "a2", "a3"])
    assert updated.account_count == 3


@pytest.mark.asyncio
async def test_assign_accounts_deduplicates():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    t = await svc.create_territory("ten1", "Riyadh", account_ids=["a1"])
    updated = await svc.assign_accounts(t.id, ["a1", "a2"])
    assert updated.account_count == 2
    assert "a1" in updated.account_ids
    assert "a2" in updated.account_ids


@pytest.mark.asyncio
async def test_unassign_accounts():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    t = await svc.create_territory("ten1", "Riyadh", account_ids=["a1", "a2", "a3"])
    updated = await svc.unassign_accounts(t.id, ["a2"])
    assert updated.account_count == 2
    assert "a2" not in updated.account_ids


@pytest.mark.asyncio
async def test_move_account():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    t1 = await svc.create_territory("ten1", "North", account_ids=["a1", "a2"])
    t2 = await svc.create_territory("ten1", "South", account_ids=["a3"])
    from_t, to_t = await svc.move_account(t1.id, t2.id, "a1")
    assert "a1" not in from_t.account_ids
    assert "a1" in to_t.account_ids


@pytest.mark.asyncio
async def test_coverage_analysis():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    await svc.create_territory("ten1", "North", rep_id="r1", rep_name="Ahmed", account_ids=["a1", "a2"])
    await svc.create_territory("ten1", "South", rep_id="r2", rep_name="Sara", account_ids=["a3"])
    summary = await svc.coverage_analysis("ten1")
    assert summary.total_territories == 2
    assert summary.total_accounts == 3
    assert summary.total_reps == 2
    assert summary.avg_accounts_per_rep == 1.5


@pytest.mark.asyncio
async def test_coverage_analysis_with_values():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    await svc.create_territory("ten1", "North", rep_id="r1", account_ids=["a1", "a2"])
    await svc.create_territory("ten1", "South", rep_id="r2", account_ids=["a3"])
    values = {"a1": 100000, "a2": 50000, "a3": 200000}
    summary = await svc.coverage_analysis("ten1", account_values=values)
    assert len(summary.per_rep) == 2
    r1 = next(p for p in summary.per_rep if p.rep_id == "r1")
    assert r1.total_pipeline_value == 150000


@pytest.mark.asyncio
async def test_find_gaps():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    await svc.create_territory("ten1", "North", account_ids=["a1", "a2"])
    known = ["a1", "a2", "a3", "a4"]
    gaps = await svc.find_gaps("ten1", known)
    assert len(gaps) == 2
    gap_ids = {g.account_id for g in gaps}
    assert "a3" in gap_ids
    assert "a4" in gap_ids


@pytest.mark.asyncio
async def test_find_gaps_with_names():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    await svc.create_territory("ten1", "North", account_ids=["a1"])
    gaps = await svc.find_gaps("ten1", ["a1", "a2"], account_names={"a2": "Acme Corp"})
    assert len(gaps) == 1
    assert gaps[0].account_name == "Acme Corp"


@pytest.mark.asyncio
async def test_find_gaps_sorted_by_value():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    gaps = await svc.find_gaps("ten1", ["a1", "a2", "a3"], account_values={"a1": 100, "a2": 300, "a3": 200})
    assert gaps[0].account_id == "a2"
    assert gaps[1].account_id == "a3"
    assert gaps[2].account_id == "a1"


@pytest.mark.asyncio
async def test_load_balance():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    await svc.create_territory("ten1", "North", rep_id="r1", account_ids=["a1", "a2", "a3", "a4", "a5"])
    await svc.create_territory("ten1", "South", rep_id="r2", account_ids=["a6"])
    recs = await svc.load_balance("ten1", max_accounts_per_rep=3)
    assert len(recs) > 0
    assert recs[0].from_rep_id == "r1"
    assert recs[0].to_rep_id == "r2"


@pytest.mark.asyncio
async def test_load_balance_balanced():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    await svc.create_territory("ten1", "North", rep_id="r1", account_ids=["a1", "a2"])
    await svc.create_territory("ten1", "South", rep_id="r2", account_ids=["a3", "a4"])
    recs = await svc.load_balance("ten1", max_accounts_per_rep=5)
    assert len(recs) == 0


@pytest.mark.asyncio
async def test_load_balance_auto_threshold():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    await svc.create_territory("ten1", "North", rep_id="r1",
                                account_ids=["a1", "a2", "a3", "a4", "a5", "a6", "a7"])
    await svc.create_territory("ten1", "South", rep_id="r2", account_ids=["a8"])
    recs = await svc.load_balance("ten1")
    assert len(recs) > 0


@pytest.mark.asyncio
async def test_find_territory_for_account():
    repo = InMemoryTerritoryRepository()
    svc = TerritoryService(repo)
    await svc.create_territory("ten1", "North", account_ids=["a1", "a2"])
    t = await svc._repository.find_territory_for_account("ten1", "a2")
    assert t is not None
    assert t.name == "North"
