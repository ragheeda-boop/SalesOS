from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("JWT_SECRET_KEY", "test")

from app.dependencies import get_current_user_role, get_current_user_id, verify_token
from app.main import app
import app.modules.admin.router as admin_router
from app.modules.admin.repositories import (
    InMemoryAICostRepository,
    InMemoryFeatureFlagRepository,
    InMemoryHealthRepository,
    InMemoryInvoiceRepository,
    InMemoryJobRepository,
    InMemoryLicenseRepository,
    InMemoryPlanRepository,
)


class InMemoryAdminRepositories:
    def __init__(self):
        self.plans = InMemoryPlanRepository()
        self.licenses = InMemoryLicenseRepository()
        self.invoices = InMemoryInvoiceRepository()
        self.flags = InMemoryFeatureFlagRepository()
        self.jobs = InMemoryJobRepository()
        self.ai = InMemoryAICostRepository()
        self.health = InMemoryHealthRepository()


_test_repos = InMemoryAdminRepositories()


async def _override_get_admin_repos():
    return _test_repos


@pytest.fixture(autouse=True)
def _reset_state():
    global _test_repos
    admin_router._tenants_store.clear()
    admin_router._users_store.clear()
    admin_router._seed_done = False
    admin_router._users_seeded = False
    admin_router._TENANT_UUIDS.clear()
    _test_repos = InMemoryAdminRepositories()
    admin_router._seed_state()


@pytest.fixture(scope="module", autouse=True)
def _override_deps():
    async def override_verify_token():
        return {"sub": "admin-user", "tenant_id": "system", "role": "admin"}

    async def override_get_current_user_role():
        return "admin"

    async def override_get_current_user_id():
        return "admin-user"

    app.dependency_overrides[verify_token] = override_verify_token
    app.dependency_overrides[get_current_user_role] = override_get_current_user_role
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    app.dependency_overrides[admin_router.get_admin_repos] = _override_get_admin_repos
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def admin_headers():
    return {"Authorization": "Bearer test-token", "X-Tenant-Id": admin_router._TENANT_UUIDS["techpro"], "X-API-Key": "test"}


@pytest.mark.asyncio
async def test_list_tenants(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 4
    names = [t["name"] for t in data]
    assert "شركة التقنية المتطورة" in names


@pytest.mark.asyncio
async def test_create_tenant(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/admin/tenants", json={
            "name": "New Tenant",
            "slug": "new-tenant",
        }, headers=admin_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "New Tenant"
    assert data["slug"] == "new-tenant"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_tenant(admin_headers):
    tid = admin_router._TENANT_UUIDS["techpro"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tid}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "شركة التقنية المتطورة"


@pytest.mark.asyncio
async def test_get_tenant_not_found(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants/nonexistent", headers=admin_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_tenant_suspend(admin_headers):
    tid = admin_router._TENANT_UUIDS["techpro"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(f"/api/v1/admin/tenants/{tid}", json={
            "is_active": False,
        }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_delete_tenant_soft(admin_headers):
    tid = admin_router._TENANT_UUIDS["techpro"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.delete(f"/api/v1/admin/tenants/{tid}", headers=admin_headers)
    assert resp.status_code == 200
    assert admin_router._tenants_store[tid]["is_active"] is False


@pytest.mark.asyncio
async def test_tenant_usage(admin_headers):
    tid = admin_router._TENANT_UUIDS["techpro"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tid}/usage", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["tenant_name"] == "شركة التقنية المتطورة"
    assert data["active_users"] >= 0


@pytest.mark.asyncio
async def test_list_plans(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/plans", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 4
    tiers = [p["tier"] for p in data]
    assert "free" in tiers
    assert "enterprise" in tiers


@pytest.mark.asyncio
async def test_create_plan(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/admin/plans", json={
            "name": "Custom Plan",
            "tier": "growth",
            "price_monthly": 599,
            "max_users": 10,
            "max_storage_mb": 5000,
            "max_api_calls": 50000,
            "features": ["basic_search", "reports"],
        }, headers=admin_headers)
    assert resp.status_code == 201
    assert resp.json()["name"] == "Custom Plan"


@pytest.mark.asyncio
async def test_update_plan(admin_headers):
    plans = await _test_repos.plans.list()
    plan_id = str(plans[0].id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(f"/api/v1/admin/plans/{plan_id}", json={
            "price_monthly": 199,
            "name": "Updated Plan",
        }, headers=admin_headers)
    assert resp.status_code == 200, f"Expected 200 got {resp.status_code}: {resp.text}"
    assert resp.json()["price_monthly"] == 199


@pytest.mark.asyncio
async def test_list_licenses(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/licenses", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_license(admin_headers):
    plans = await _test_repos.plans.list()
    plan_id = plans[1].id
    tid = admin_router._TENANT_UUIDS["techpro"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/admin/licenses", json={
            "tenant_id": tid,
            "plan_id": str(plan_id),
        }, headers=admin_headers)
    assert resp.status_code == 201, f"Expected 201 got {resp.status_code}: {resp.text}"
    assert resp.json()["plan_name"] == plans[1].name


@pytest.mark.asyncio
async def test_list_users(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/users", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 5
    emails = [u["email"] for u in data]
    assert "admin@techpro.sa" in emails


@pytest.mark.asyncio
async def test_get_user_detail(admin_headers):
    user_id = admin_router._users_store[0]["id"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/users/{user_id}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "admin@techpro.sa"
    assert "permissions" in resp.json()


@pytest.mark.asyncio
async def test_update_user_role(admin_headers):
    user_id = admin_router._users_store[0]["id"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(f"/api/v1/admin/users/{user_id}", json={
            "role": "manager",
        }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "manager"


@pytest.mark.asyncio
async def test_deactivate_user(admin_headers):
    user_id = admin_router._users_store[0]["id"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.delete(f"/api/v1/admin/users/{user_id}", headers=admin_headers)
    assert resp.status_code == 200
    assert admin_router._users_store[0]["is_active"] is False


@pytest.mark.asyncio
async def test_list_invoices(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/billing/invoices", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 3


@pytest.mark.asyncio
async def test_list_transactions(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/billing/transactions", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_list_feature_flags(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/feature-flags", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 5
    keys = [f["key"] for f in data]
    assert "ai_copilot" in keys


@pytest.mark.asyncio
async def test_create_feature_flag(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/admin/feature-flags", json={
            "key": "new_feature_x",
            "name": "New Feature X",
            "description": "Testing feature",
            "enabled": False,
        }, headers=admin_headers)
    assert resp.status_code == 201
    assert resp.json()["key"] == "new_feature_x"


@pytest.mark.asyncio
async def test_toggle_feature_flag(admin_headers):
    flags = await _test_repos.flags.list()
    flag_id = str(flags[0].id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(f"/api/v1/admin/feature-flags/{flag_id}", json={
            "enabled": False,
        }, headers=admin_headers)
    assert resp.status_code == 200, f"Expected 200 got {resp.status_code}: {resp.text}"
    assert resp.json()["enabled"] is False


@pytest.mark.asyncio
async def test_feature_flag_tenants(admin_headers):
    flags = await _test_repos.flags.list()
    flag_id = str(flags[0].id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/feature-flags/{flag_id}/tenants", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_list_jobs(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/jobs", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 4


@pytest.mark.asyncio
async def test_get_job_detail(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/jobs/job-001", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["type"] == "data_ingestion"
    assert "logs" in resp.json()


@pytest.mark.asyncio
async def test_retry_failed_job(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/admin/jobs/job-003/retry", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Job queued for retry"


@pytest.mark.asyncio
async def test_list_ai_costs(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/ai/costs", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 4


@pytest.mark.asyncio
async def test_ai_cost_summary(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/ai/summary", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_cost"] > 0
    assert len(data["by_model"]) >= 2


@pytest.mark.asyncio
async def test_ai_usage(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/ai/usage", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tokens"] > 0


@pytest.mark.asyncio
async def test_detailed_health(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/health/detailed", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_status"] == "healthy"
    assert len(data["components"]) >= 5


@pytest.mark.asyncio
async def test_health_history(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/health/history", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 5


@pytest.mark.asyncio
async def test_list_tenants_filter_by_plan(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?plan=enterprise", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert all(t["plan"] == "enterprise" for t in data)
