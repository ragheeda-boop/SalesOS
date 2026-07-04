"""Tests for Revenue Analytics Domain — Measurement Layer."""

from datetime import datetime, timedelta, timezone

import pytest

from domains.revenue.analytics.models import AnalyticsSnapshot, KPI, KPIValue, MetricCategory
from domains.revenue.analytics.registry import KPIRegistry
from domains.revenue.analytics.service import AnalyticsInput, AnalyticsService
from domains.revenue.analytics.in_memory_repo import InMemoryAnalyticsRepository


# ── KPI Registry ──

def test_kpi_registry_loaded():
    KPIRegistry.load_defaults()
    assert len(KPIRegistry.all()) >= 18  # at least 19 KPIs
    assert KPIRegistry.get("booked_revenue") is not None
    assert KPIRegistry.get("nonexistent") is None


def test_kpi_by_category():
    KPIRegistry.load_defaults()
    revenue_kpis = KPIRegistry.by_category(MetricCategory.REVENUE)
    assert len(revenue_kpis) >= 4


def test_kpi_formula():
    KPIRegistry.load_defaults()
    kpi = KPIRegistry.get("forecast_accuracy")
    assert kpi is not None
    assert kpi.formula == "1 - ABS(forecast - actual) / forecast"


def test_kpi_registry_explainable():
    KPIRegistry.load_defaults()
    explained = AnalyticsService.explain("booked_revenue")
    assert explained["formula"] == "SUM(quote.grand_total WHERE quote.accepted)"
    assert explained["unit"] == "currency"


# ── Models ──

def test_analytics_snapshot_values():
    snap = AnalyticsSnapshot(id="s1", tenant_id="t1",
                             period_start=datetime(2026, 1, 1), period_end=datetime(2026, 3, 31),
                             values=[KPIValue(kpi_id="booked_revenue", value=100000)])
    assert snap.total_kpis == 1
    assert snap.get_value("booked_revenue") is not None
    assert snap.get_value("nonexistent") is None


def test_snapshot_does_not_store_facts():
    snap = AnalyticsSnapshot(id="s1", tenant_id="t1",
                             period_start=datetime(2026, 1, 1), period_end=datetime(2026, 3, 31))
    assert not hasattr(snap, "opportunities")
    assert not hasattr(snap, "quotes")


# ── Service ──

@pytest.mark.asyncio
async def test_generate_snapshot():
    repo = InMemoryAnalyticsRepository()
    svc = AnalyticsService(repo)
    KPIRegistry.load_defaults()

    now = datetime.now(timezone.utc)
    inputs = AnalyticsInput(
        total_booked_revenue=500000,
        total_expected_revenue=650000,
        previous_booked_revenue=400000,
        pipeline_coverage_ratio=3.5,
        avg_stage_velocity_days=21.5,
        stage_conversion_rate=0.45,
        quote_acceptance_rate=0.6,
        avg_discount_percent=12.5,
        forecast_accuracy=0.82,
    )

    snap = await svc.generate_snapshot("t1", inputs, now - timedelta(days=30), now)
    assert snap.tenant_id == "t1"
    assert snap.total_kpis >= 18

    # Check specific KPI
    revenue_variance = snap.get_value("revenue_variance")
    assert revenue_variance is not None
    assert revenue_variance.value > 0


@pytest.mark.asyncio
async def test_revenue_growth():
    repo = InMemoryAnalyticsRepository()
    svc = AnalyticsService(repo)
    KPIRegistry.load_defaults()

    now = datetime.now(timezone.utc)
    inputs = AnalyticsInput(total_booked_revenue=600000, previous_booked_revenue=400000)
    snap = await svc.generate_snapshot("t1", inputs, now - timedelta(days=30), now)

    growth = snap.get_value("revenue_growth")
    assert growth is not None
    assert growth.value == 50.0  # (600K - 400K) / 400K * 100


@pytest.mark.asyncio
async def test_forecast_accuracy():
    repo = InMemoryAnalyticsRepository()
    svc = AnalyticsService(repo)
    KPIRegistry.load_defaults()

    now = datetime.now(timezone.utc)
    inputs = AnalyticsInput(forecast_accuracy=0.85)
    snap = await svc.generate_snapshot("t1", inputs, now - timedelta(days=30), now)

    acc = snap.get_value("forecast_accuracy")
    assert acc is not None
    assert acc.value == 85.0


@pytest.mark.asyncio
async def test_kpi_trend():
    repo = InMemoryAnalyticsRepository()
    svc = AnalyticsService(repo)
    KPIRegistry.load_defaults()

    now = datetime.now(timezone.utc)
    inputs = AnalyticsInput(total_booked_revenue=500000, previous_booked_revenue=400000)
    snap = await svc.generate_snapshot("t1", inputs, now - timedelta(days=30), now)

    revenue = snap.get_value("booked_revenue")
    assert revenue is not None
    assert revenue.value == 500000
    assert revenue.previous_value == 400000
    assert revenue.change == 100000


@pytest.mark.asyncio
async def test_snapshot_immutability():
    repo = InMemoryAnalyticsRepository()
    svc = AnalyticsService(repo)
    KPIRegistry.load_defaults()

    now = datetime.now(timezone.utc)
    inputs = AnalyticsInput(total_booked_revenue=500000)
    snap = await svc.generate_snapshot("t1", inputs, now - timedelta(days=30), now)
    original_value = snap.get_value("booked_revenue").value

    # Retrieve again and verify unchanged
    retrieved = await svc.get(snap.id)
    assert retrieved.get_value("booked_revenue").value == original_value


@pytest.mark.asyncio
async def test_list_snapshots():
    repo = InMemoryAnalyticsRepository()
    svc = AnalyticsService(repo)
    KPIRegistry.load_defaults()

    now = datetime.now(timezone.utc)
    for i in range(3):
        inputs = AnalyticsInput(total_booked_revenue=100000 * (i + 1))
        await svc.generate_snapshot("t1", inputs, now - timedelta(days=30 * (i + 1)), now - timedelta(days=30 * i))

    snapshots = await svc.list_snapshots("t1")
    assert len(snapshots) == 3


@pytest.mark.asyncio
async def test_no_decisions():
    """Analytics must not make decisions — only measurements."""
    repo = InMemoryAnalyticsRepository()
    svc = AnalyticsService(repo)
    KPIRegistry.load_defaults()

    now = datetime.now(timezone.utc)
    inputs = AnalyticsInput(total_booked_revenue=500000)
    snap = await svc.generate_snapshot("t1", inputs, now - timedelta(days=30), now)

    # Verify no decision fields
    assert not hasattr(snap, "recommendations")
    assert not hasattr(snap, "actions")
