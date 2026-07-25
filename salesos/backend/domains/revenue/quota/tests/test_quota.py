"""Tests for Revenue Quota Management Domain."""

from datetime import datetime, timedelta, timezone

import pytest

from domains.revenue.quota.models import (
    Quota, QuotaForecast, QuotaPeriod, QuotaSnapshot, QuotaStatus, TeamAggregate,
)
from domains.revenue.quota.in_memory_repo import InMemoryQuotaRepository
from domains.revenue.quota.service import QuotaService


# ── Model Tests ──

def test_quota_attainment_percent():
    q = Quota(id="q1", tenant_id="t1", rep_id="r1", target_amount=100000, attained_amount=75000)
    assert q.attainment_percent == 75.0


def test_quota_attainment_zero_target():
    q = Quota(id="q1", tenant_id="t1", rep_id="r1", target_amount=0, attained_amount=5000)
    assert q.attainment_percent == 0.0


def test_quota_remaining_amount():
    q = Quota(id="q1", tenant_id="t1", rep_id="r1", target_amount=100000, attained_amount=60000)
    assert q.remaining_amount == 40000.0


def test_quota_remaining_exceeded():
    q = Quota(id="q1", tenant_id="t1", rep_id="r1", target_amount=100000, attained_amount=120000)
    assert q.remaining_amount == 0.0


def test_quota_is_on_track():
    now = datetime.now(timezone.utc)
    q = Quota(
        id="q1", tenant_id="t1", rep_id="r1",
        target_amount=100000, attained_amount=80000,
        start_date=now - timedelta(days=60),
        end_date=now + timedelta(days=30),
    )
    assert q.is_on_track is True


def test_quota_is_not_on_track():
    now = datetime.now(timezone.utc)
    q = Quota(
        id="q1", tenant_id="t1", rep_id="r1",
        target_amount=100000, attained_amount=20000,
        start_date=now - timedelta(days=60),
        end_date=now + timedelta(days=30),
    )
    assert q.is_on_track is False


def test_quota_snapshot_totals():
    snap = QuotaSnapshot(id="s1", tenant_id="t1", quotas=[
        Quota(id="q1", tenant_id="t1", rep_id="r1", target_amount=100000, attained_amount=80000),
        Quota(id="q2", tenant_id="t1", rep_id="r2", target_amount=50000, attained_amount=50000),
    ])
    assert snap.total_target == 150000
    assert snap.total_attained == 130000
    assert round(snap.overall_attainment, 2) == 86.67


# ── Service Tests ──

@pytest.mark.asyncio
async def test_create_quota():
    repo = InMemoryQuotaRepository()
    svc = QuotaService(repo)
    q = await svc.create_quota("t1", "r1", 100000, rep_name="Ahmed")
    assert q.tenant_id == "t1"
    assert q.rep_id == "r1"
    assert q.target_amount == 100000
    assert q.status == QuotaStatus.ACTIVE


@pytest.mark.asyncio
async def test_list_quotas():
    repo = InMemoryQuotaRepository()
    svc = QuotaService(repo)
    await svc.create_quota("t1", "r1", 100000)
    await svc.create_quota("t1", "r2", 80000)
    quotas = await svc.list_quotas("t1")
    assert len(quotas) == 2


@pytest.mark.asyncio
async def test_list_quotas_by_rep():
    repo = InMemoryQuotaRepository()
    svc = QuotaService(repo)
    await svc.create_quota("t1", "r1", 100000)
    await svc.create_quota("t1", "r2", 80000)
    quotas = await svc.list_quotas("t1", rep_id="r1")
    assert len(quotas) == 1
    assert quotas[0].rep_id == "r1"


@pytest.mark.asyncio
async def test_update_attainment():
    repo = InMemoryQuotaRepository()
    svc = QuotaService(repo)
    q = await svc.create_quota("t1", "r1", 100000)
    updated = await svc.update_attainment(q.id, 75000)
    assert updated.attained_amount == 75000
    assert updated.attainment_percent == 75.0


@pytest.mark.asyncio
async def test_update_attainment_completes():
    repo = InMemoryQuotaRepository()
    svc = QuotaService(repo)
    q = await svc.create_quota("t1", "r1", 100000)
    updated = await svc.update_attainment(q.id, 100000)
    assert updated.status == QuotaStatus.COMPLETED


@pytest.mark.asyncio
async def test_increment_attainment():
    repo = InMemoryQuotaRepository()
    svc = QuotaService(repo)
    q = await svc.create_quota("t1", "r1", 100000)
    await svc.update_attainment(q.id, 50000)
    updated = await svc.increment_attainment(q.id, 25000)
    assert updated.attained_amount == 75000


@pytest.mark.asyncio
async def test_update_attainment_not_found():
    repo = InMemoryQuotaRepository()
    svc = QuotaService(repo)
    with pytest.raises(ValueError, match="not found"):
        await svc.update_attainment("nonexistent", 1000)


@pytest.mark.asyncio
async def test_forecast_attainment():
    repo = InMemoryQuotaRepository()
    svc = QuotaService(repo)
    q = await svc.create_quota("t1", "r1", 100000)
    forecast = await svc.forecast_attainment(
        "t1", "r1",
        closed_revenue=50000,
        period_days_elapsed=45,
        total_period_days=90,
    )
    assert forecast.quota_id == q.id
    assert forecast.current_velocity > 0
    assert forecast.projected_attainment > 50000
    assert forecast.days_remaining > 0


@pytest.mark.asyncio
async def test_forecast_attainment_will_hit():
    repo = InMemoryQuotaRepository()
    svc = QuotaService(repo)
    await svc.create_quota("t1", "r1", 100000)
    forecast = await svc.forecast_attainment(
        "t1", "r1",
        closed_revenue=75000,
        period_days_elapsed=45,
        total_period_days=90,
    )
    assert forecast.will_hit_target is True


@pytest.mark.asyncio
async def test_forecast_attainment_will_miss():
    repo = InMemoryQuotaRepository()
    svc = QuotaService(repo)
    await svc.create_quota("t1", "r1", 100000)
    forecast = await svc.forecast_attainment(
        "t1", "r1",
        closed_revenue=20000,
        period_days_elapsed=45,
        total_period_days=90,
    )
    assert forecast.will_hit_target is False


@pytest.mark.asyncio
async def test_get_per_rep_view():
    repo = InMemoryQuotaRepository()
    svc = QuotaService(repo)
    await svc.create_quota("t1", "r1", 100000, rep_name="Ahmed")
    await svc.create_quota("t1", "r1", 50000, rep_name="Ahmed")
    await svc.create_quota("t1", "r2", 80000, rep_name="Sara")
    view = await svc.get_per_rep_view("t1")
    assert len(view) == 2
    r1 = next(v for v in view if v["rep_id"] == "r1")
    assert r1["total_target"] == 150000


@pytest.mark.asyncio
async def test_get_team_aggregate():
    repo = InMemoryQuotaRepository()
    svc = QuotaService(repo)
    await svc.create_quota("t1", "r1", 100000)
    await svc.update_attainment((await svc.list_quotas("t1"))[0].id, 100000)
    await svc.create_quota("t1", "r2", 80000)
    team = await svc.get_team_aggregate("t1")
    assert team.total_targets == 180000
    assert team.total_attained == 100000
    assert team.rep_count == 2


@pytest.mark.asyncio
async def test_take_snapshot():
    repo = InMemoryQuotaRepository()
    svc = QuotaService(repo)
    await svc.create_quota("t1", "r1", 100000)
    await svc.create_quota("t1", "r2", 80000)
    snap = await svc.take_snapshot("t1", "2026-Q3")
    assert snap.tenant_id == "t1"
    assert len(snap.quotas) == 2
    assert snap.team is not None
    assert snap.team.rep_count == 2


@pytest.mark.asyncio
async def test_delete_quota():
    repo = InMemoryQuotaRepository()
    svc = QuotaService(repo)
    q = await svc.create_quota("t1", "r1", 100000)
    result = await svc.delete_quota(q.id)
    assert result is True
    assert await svc.get_quota(q.id) is None
