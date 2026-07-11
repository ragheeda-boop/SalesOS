from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.modules.telemetry.models import TelemetryEvent
from app.modules.telemetry.service import (
    EVENT_TYPES,
    InMemoryTelemetryRepository,
    TelemetryService,
)
from app.domains.customer_success.health import compute_health_score, compute_tenant_health


@pytest.fixture
def inmem_repo():
    return InMemoryTelemetryRepository()


@pytest.fixture
def telemetry_service(inmem_repo):
    return TelemetryService(repository=inmem_repo)


# ─── Event Tracking ─────────────────────────────────────────────

class TestEventTracking:
    @pytest.mark.asyncio
    async def test_track_basic_event(self, telemetry_service):
        event = await telemetry_service.track(
            event_type="page_view",
            tenant_id="tenant-1",
            user_id="user-1",
            properties={"page": "/dashboard"},
        )
        assert event.event_type == "page_view"
        assert event.tenant_id == "tenant-1"
        assert event.user_id == "user-1"
        assert event.properties == {"page": "/dashboard"}
        assert event.id is not None

    @pytest.mark.asyncio
    async def test_track_all_event_types(self, telemetry_service):
        for etype in sorted(EVENT_TYPES):
            event = await telemetry_service.track(etype, "t1", "u1")
            assert event.event_type == etype

    @pytest.mark.asyncio
    async def test_track_without_properties(self, telemetry_service):
        event = await telemetry_service.track("login", "t1", "u1")
        assert event.properties == {}

    @pytest.mark.asyncio
    async def test_track_with_custom_timestamp(self, telemetry_service):
        ts = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        event = await telemetry_service.track("login", "t1", "u1", timestamp=ts)
        assert event.timestamp == ts

    @pytest.mark.asyncio
    async def test_track_multiple_events(self, telemetry_service):
        for i in range(10):
            await telemetry_service.track("page_view", "t1", f"user-{i}")
        events = telemetry_service.repository._events
        assert len(events) == 10

    @pytest.mark.asyncio
    async def test_track_auto_timestamp(self, telemetry_service):
        before = datetime.now(timezone.utc)
        event = await telemetry_service.track("login", "t1", "u1")
        after = datetime.now(timezone.utc)
        assert before <= event.timestamp.replace(tzinfo=timezone.utc) <= after


# ─── Event Querying ─────────────────────────────────────────────

class TestEventQuerying:
    @pytest.mark.asyncio
    async def test_query_by_event_type(self, telemetry_service):
        await telemetry_service.track("page_view", "t1", "u1")
        await telemetry_service.track("search_query", "t1", "u1")
        await telemetry_service.track("page_view", "t1", "u2")
        results, total = await telemetry_service.repository.query("t1", event_type="page_view")
        assert total == 2
        assert all(e.event_type == "page_view" for e in results)

    @pytest.mark.asyncio
    async def test_query_by_date_range(self, telemetry_service):
        old_ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
        new_ts = datetime(2026, 6, 15, tzinfo=timezone.utc)
        await telemetry_service.track("login", "t1", "u1", timestamp=old_ts)
        await telemetry_service.track("login", "t1", "u1", timestamp=new_ts)
        frm = datetime(2026, 1, 1, tzinfo=timezone.utc)
        to = datetime(2026, 12, 31, tzinfo=timezone.utc)
        results, total = await telemetry_service.repository.query("t1", from_date=frm, to_date=to)
        assert total == 1
        assert results[0].timestamp == new_ts

    @pytest.mark.asyncio
    async def test_query_tenant_isolation(self, telemetry_service):
        await telemetry_service.track("login", "tenant-a", "u1")
        await telemetry_service.track("login", "tenant-b", "u1")
        results_a, total_a = await telemetry_service.repository.query("tenant-a")
        assert total_a == 1
        results_b, total_b = await telemetry_service.repository.query("tenant-b")
        assert total_b == 1

    @pytest.mark.asyncio
    async def test_query_pagination(self, telemetry_service):
        for i in range(10):
            await telemetry_service.track("page_view", "t1", f"u{i}")
        page1, total = await telemetry_service.repository.query("t1", limit=3, offset=0)
        assert total == 10
        assert len(page1) == 3
        page2, _ = await telemetry_service.repository.query("t1", limit=3, offset=3)
        assert len(page2) == 3
        assert page1[0].id != page2[0].id

    @pytest.mark.asyncio
    async def test_query_empty(self, telemetry_service):
        results, total = await telemetry_service.repository.query("nonexistent")
        assert total == 0
        assert results == []


# ─── Aggregation ────────────────────────────────────────────────

class TestAggregation:
    @pytest.mark.asyncio
    async def test_aggregate_daily(self, telemetry_service):
        day1 = datetime(2026, 7, 1, tzinfo=timezone.utc)
        day2 = datetime(2026, 7, 2, tzinfo=timezone.utc)
        await telemetry_service.track("login", "t1", "u1", timestamp=day1)
        await telemetry_service.track("login", "t1", "u1", timestamp=day1)
        await telemetry_service.track("login", "t1", "u1", timestamp=day2)
        result = await telemetry_service.query("t1", granularity="day")
        buckets = {r["period"]: r["count"] for r in result}
        assert buckets["2026-07-01"] == 2
        assert buckets["2026-07-02"] == 1

    @pytest.mark.asyncio
    async def test_aggregate_monthly(self, telemetry_service):
        jan = datetime(2026, 1, 15, tzinfo=timezone.utc)
        feb = datetime(2026, 2, 10, tzinfo=timezone.utc)
        await telemetry_service.track("login", "t1", "u1", timestamp=jan)
        await telemetry_service.track("login", "t1", "u1", timestamp=feb)
        await telemetry_service.track("login", "t1", "u1", timestamp=feb)
        result = await telemetry_service.query("t1", granularity="month")
        buckets = {r["period"]: r["count"] for r in result}
        assert buckets["2026-01"] == 1
        assert buckets["2026-02"] == 2

    @pytest.mark.asyncio
    async def test_aggregate_filtered_by_type(self, telemetry_service):
        ts = datetime(2026, 7, 1, tzinfo=timezone.utc)
        await telemetry_service.track("login", "t1", "u1", timestamp=ts)
        await telemetry_service.track("search_query", "t1", "u1", timestamp=ts)
        result = await telemetry_service.query("t1", event_type="login", granularity="day")
        buckets = {r["period"]: r["count"] for r in result}
        assert buckets["2026-07-01"] == 1

    @pytest.mark.asyncio
    async def test_aggregate_empty(self, telemetry_service):
        result = await telemetry_service.query("nonexistent")
        assert result == []


# ─── Feature Adoption ───────────────────────────────────────────

class TestFeatureAdoption:
    @pytest.mark.asyncio
    async def test_feature_adoption_basic(self, telemetry_service):
        await telemetry_service.track("search_query", "t1", "user-a")
        await telemetry_service.track("search_query", "t1", "user-b")
        await telemetry_service.track("nba_view", "t1", "user-a")
        result = await telemetry_service.feature_adoption("t1")
        features = {r["feature"]: r for r in result}
        assert features["search_query"]["user_count"] == 2
        assert features["nba_view"]["user_count"] == 1
        assert features["search_query"]["adoption_pct"] >= features["nba_view"]["adoption_pct"]

    @pytest.mark.asyncio
    async def test_feature_adoption_empty(self, telemetry_service):
        result = await telemetry_service.feature_adoption("nonexistent")
        assert all(r["adoption_pct"] == 0.0 for r in result)

    @pytest.mark.asyncio
    async def test_feature_adoption_label(self, telemetry_service):
        await telemetry_service.track("search_query", "t1", "u1")
        result = await telemetry_service.feature_adoption("t1")
        entry = next(r for r in result if r["feature"] == "search_query")
        assert entry["label"] == "البحث"


# ─── Search Success Rate ────────────────────────────────────────

class TestSearchSuccess:
    @pytest.mark.asyncio
    async def test_search_success_rate(self, telemetry_service):
        await telemetry_service.track("search_query", "t1", "u1", properties={"clicked": True})
        await telemetry_service.track("search_query", "t1", "u1", properties={"clicked": False})
        result = await telemetry_service.search_success_rate("t1")
        assert result["total_searches"] == 2
        assert result["success_rate"] == 50.0

    @pytest.mark.asyncio
    async def test_search_success_no_searches(self, telemetry_service):
        result = await telemetry_service.search_success_rate("t1")
        assert result["total_searches"] == 0
        assert result["success_rate"] == 0.0


# ─── NBA Acceptance Rate ────────────────────────────────────────

class TestNBAAcceptance:
    @pytest.mark.asyncio
    async def test_nba_acceptance_rate(self, telemetry_service):
        await telemetry_service.track("nba_view", "t1", "u1")
        await telemetry_service.track("nba_accept", "t1", "u1")
        await telemetry_service.track("nba_reject", "t1", "u1")
        result = await telemetry_service.nba_acceptance_rate("t1")
        assert result["nba_views"] == 1
        assert result["nba_accepts"] == 1
        assert result["nba_rejects"] == 1
        assert result["acceptance_rate"] == 50.0

    @pytest.mark.asyncio
    async def test_nba_acceptance_no_decisions(self, telemetry_service):
        result = await telemetry_service.nba_acceptance_rate("t1")
        assert result["acceptance_rate"] == 0.0


# ─── Time Metrics ───────────────────────────────────────────────

class TestTimeMetrics:
    @pytest.mark.asyncio
    async def test_time_to_insight(self, telemetry_service):
        base = datetime(2026, 7, 1, 8, 0, 0, tzinfo=timezone.utc)
        await telemetry_service.track("login", "t1", "user-a", timestamp=base)
        await telemetry_service.track("search_query", "t1", "user-a", timestamp=base + timedelta(minutes=5))
        result = await telemetry_service.time_to_insight("t1")
        assert result["users_with_insight"] == 1
        assert result["avg_time_to_insight_seconds"] == 300.0

    @pytest.mark.asyncio
    async def test_time_to_insight_no_logins(self, telemetry_service):
        result = await telemetry_service.time_to_insight("t1")
        assert result["avg_time_to_insight_seconds"] == 0.0

    @pytest.mark.asyncio
    async def test_time_to_action(self, telemetry_service):
        base = datetime(2026, 7, 1, 8, 0, 0, tzinfo=timezone.utc)
        await telemetry_service.track("nba_view", "t1", "user-a", timestamp=base)
        await telemetry_service.track("nba_accept", "t1", "user-a", timestamp=base + timedelta(minutes=10))
        result = await telemetry_service.time_to_action("t1")
        assert result["users_with_action"] == 1
        assert result["avg_time_to_action_seconds"] == 600.0


# ─── Active Users ───────────────────────────────────────────────

class TestActiveUsers:
    @pytest.mark.asyncio
    async def test_active_users(self, telemetry_service):
        now = datetime.now(timezone.utc)
        await telemetry_service.track("login", "t1", "user-a", timestamp=now)
        await telemetry_service.track("login", "t1", "user-b", timestamp=now - timedelta(days=3))
        await telemetry_service.track("login", "t1", "user-c", timestamp=now - timedelta(days=20))
        result = await telemetry_service.active_users(days=30)
        assert result["dau"] == 1
        assert result["wau"] == 2
        assert result["mau"] == 3


# ─── Health Score Algorithm ─────────────────────────────────────

class TestHealthScore:
    def test_health_score_green(self):
        result = compute_health_score(90.0, 85.0, 80.0)
        assert result["status"] == "healthy"
        assert result["color"] == "green"
        assert result["score"] > 80

    def test_health_score_yellow(self):
        result = compute_health_score(60.0, 50.0, 55.0)
        assert result["status"] == "warning"
        assert result["color"] == "yellow"
        assert 50 < result["score"] <= 80

    def test_health_score_red(self):
        result = compute_health_score(30.0, 40.0, 35.0)
        assert result["status"] == "critical"
        assert result["color"] == "red"
        assert result["score"] < 50

    def test_health_score_formula(self):
        result = compute_health_score(100.0, 100.0, 100.0)
        assert result["score"] == 100.0
        assert result["components"]["feature_adoption"]["contribution"] == 40.0
        assert result["components"]["search_success"]["contribution"] == 30.0
        assert result["components"]["nba_acceptance"]["contribution"] == 30.0

    def test_health_score_renewal_risk(self):
        low_since = datetime.now(timezone.utc) - timedelta(days=35)
        result = compute_health_score(30.0, 40.0, 35.0, low_health_since=low_since)
        assert result["renewal_risk"] is True
        assert result["days_in_low_health"] >= 30

    def test_health_score_no_renewal_risk_recent(self):
        low_since = datetime.now(timezone.utc) - timedelta(days=10)
        result = compute_health_score(30.0, 40.0, 35.0, low_health_since=low_since)
        assert result["renewal_risk"] is False
        assert result["days_in_low_health"] < 30

    def test_health_score_no_low_health_since(self):
        result = compute_health_score(90.0, 85.0, 80.0)
        assert result["renewal_risk"] is False
        assert result["days_in_low_health"] == 0

    def test_tenant_health_returns_tenant_info(self):
        result = compute_tenant_health(
            "tenant-1", "شركة التقنية",
            80.0, 75.0, 70.0,
            user_count=25, last_active="2026-07-10",
        )
        assert result["tenant_id"] == "tenant-1"
        assert result["tenant_name"] == "شركة التقنية"
        assert result["user_count"] == 25
        assert result["last_active"] == "2026-07-10"
