from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.modules.audit.models import AuditLog
from app.modules.audit.service import AuditService, InMemoryAuditRepository, PostgresAuditRepository


@pytest.fixture
def inmem_repo():
    return InMemoryAuditRepository()


@pytest.fixture
def audit_service(inmem_repo):
    return AuditService(repository=inmem_repo)


class TestAuditLogging:
    @pytest.mark.asyncio
    async def test_log_basic_entry(self, audit_service):
        entry = await audit_service.log(
            tenant_id="tenant-1",
            user_id="user-1",
            action="created",
            resource_type="company",
            resource_id="comp-1",
            details={"name": "ACME"},
            ip_address="192.168.1.1",
            user_agent="test-client",
        )
        assert entry.tenant_id == "tenant-1"
        assert entry.user_id == "user-1"
        assert entry.action == "created"
        assert entry.resource_type == "company"
        assert entry.resource_id == "comp-1"
        assert entry.details == {"name": "ACME"}
        assert entry.ip_address == "192.168.1.1"

    @pytest.mark.asyncio
    async def test_log_without_optional_fields(self, audit_service):
        entry = await audit_service.log(
            tenant_id="tenant-1",
            user_id=None,
            action="read",
            resource_type="report",
        )
        assert entry.tenant_id == "tenant-1"
        assert entry.user_id is None
        assert entry.action == "read"
        assert entry.resource_type == "report"

    @pytest.mark.asyncio
    async def test_log_multiple_entries(self, audit_service):
        for i in range(5):
            await audit_service.log(
                tenant_id="tenant-1",
                user_id=f"user-{i}",
                action="created",
                resource_type="item",
                resource_id=f"item-{i}",
            )
        entries, total = await audit_service.query("tenant-1")
        assert total == 5
        assert len(entries) == 5

    @pytest.mark.asyncio
    async def test_log_includes_timestamp(self, audit_service):
        before = datetime.now(timezone.utc)
        entry = await audit_service.log("t1", "u1", "login", "session")
        after = datetime.now(timezone.utc)
        assert entry.created_at is not None
        assert before <= entry.created_at.replace(tzinfo=timezone.utc) <= after


class TestAuditQuery:
    @pytest.mark.asyncio
    async def test_query_by_tenant(self, audit_service):
        await audit_service.log("tenant-a", "u1", "create", "company")
        await audit_service.log("tenant-b", "u2", "create", "company")
        entries_a, total_a = await audit_service.query("tenant-a")
        assert total_a == 1
        entries_b, total_b = await audit_service.query("tenant-b")
        assert total_b == 1

    @pytest.mark.asyncio
    async def test_query_by_action(self, audit_service):
        await audit_service.log("t1", "u1", "create", "company")
        await audit_service.log("t1", "u1", "update", "company")
        await audit_service.log("t1", "u1", "delete", "company")
        entries, total = await audit_service.query("t1", {"action": "update"})
        assert total == 1
        assert entries[0].action == "update"

    @pytest.mark.asyncio
    async def test_query_by_resource_type(self, audit_service):
        await audit_service.log("t1", "u1", "create", "company")
        await audit_service.log("t1", "u1", "create", "contact")
        entries, total = await audit_service.query("t1", {"resource_type": "company"})
        assert total == 1

    @pytest.mark.asyncio
    async def test_query_by_user_id(self, audit_service):
        await audit_service.log("t1", "user-a", "create", "company")
        await audit_service.log("t1", "user-b", "create", "company")
        entries, total = await audit_service.query("t1", {"user_id": "user-a"})
        assert total == 1

    @pytest.mark.asyncio
    async def test_query_with_pagination(self, audit_service):
        for i in range(10):
            await audit_service.log("t1", "u1", "create", "item", resource_id=f"item-{i}")
        page1, total = await audit_service.query("t1", page=1, size=3)
        assert total == 10
        assert len(page1) == 3
        page2, _ = await audit_service.query("t1", page=2, size=3)
        assert len(page2) == 3
        assert page1[0].resource_id != page2[0].resource_id

    @pytest.mark.asyncio
    async def test_query_empty_result(self, audit_service):
        entries, total = await audit_service.query("nonexistent")
        assert total == 0
        assert entries == []


class TestAuditStats:
    @pytest.mark.asyncio
    async def test_stats_total_events(self, audit_service):
        for i in range(7):
            await audit_service.log("t1", f"user-{i % 3}", "create", "company")
        stats = await audit_service.stats("t1", days=30)
        assert stats["total_events"] == 7

    @pytest.mark.asyncio
    async def test_stats_top_users(self, audit_service):
        for i in range(10):
            await audit_service.log("t1", "frequent-user", "create", "company")
        await audit_service.log("t1", "rare-user", "create", "company")
        stats = await audit_service.stats("t1", days=30)
        top = stats["top_users"]
        assert len(top) >= 1
        assert top[0]["user_id"] == "frequent-user"

    @pytest.mark.asyncio
    async def test_stats_top_actions(self, audit_service):
        await audit_service.log("t1", "u1", "create", "company")
        await audit_service.log("t1", "u1", "create", "company")
        await audit_service.log("t1", "u1", "delete", "company")
        stats = await audit_service.stats("t1", days=30)
        actions = {a["action"]: a["count"] for a in stats["top_actions"]}
        assert actions["create"] == 2

    @pytest.mark.asyncio
    async def test_stats_resource_breakdown(self, audit_service):
        await audit_service.log("t1", "u1", "create", "company")
        await audit_service.log("t1", "u1", "create", "contact")
        await audit_service.log("t1", "u1", "create", "contact")
        stats = await audit_service.stats("t1", days=30)
        breakdown = {r["resource_type"]: r["count"] for r in stats["resource_breakdown"]}
        assert breakdown["contact"] == 2
        assert breakdown["company"] == 1

    @pytest.mark.asyncio
    async def test_stats_respects_days(self, audit_service):
        old_entry = AuditLog(
            tenant_id="t1", user_id="u1", action="old", resource_type="x",
            created_at=datetime.now(timezone.utc) - timedelta(days=400),
        )
        audit_service.repository._entries.append(old_entry)
        await audit_service.log("t1", "u1", "new", "x")
        stats = await audit_service.stats("t1", days=30)
        assert stats["total_events"] == 1
