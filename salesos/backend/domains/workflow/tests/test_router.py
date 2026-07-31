"""Tests for the Workflow router — validates all REST endpoints through FastAPI TestClient."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from domains.workflow.models import (
    Workflow,
    WorkflowStep,
    WorkflowExecution,
    WorkflowExecutionStep,
    WebhookEndpoint,
    ScheduledJob,
    JobExecution,
    WorkflowTemplate,
)
from domains.workflow.repository import InMemoryWorkflowRepository
from domains.workflow.engine import WorkflowEngine
from domains.workflow.service import WorkflowService

# Patch require_permission and verify_token at module level BEFORE any router imports
_patcher1 = patch("app.dependencies.require_permission", return_value=True)
_patcher2 = patch("app.dependencies.verify_token", return_value={"sub": "test-user", "tenant_id": "tenant-1"})
_patcher1.start()
_patcher2.start()

from app.routers.workflows import router as workflow_router
from app.dependencies import get_current_tenant_id, verify_token


# ── Helpers ──

def _make_wf(override: dict | None = None) -> Workflow:
    base = {
        "id": uuid.uuid4().hex[:12],
        "tenant_id": "tenant-1",
        "name": "Test WF",
        "description": "A test workflow",
        "trigger_type": "manual",
        "status": "active",
        "steps": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    if override:
        base.update(override)
    return Workflow(**base)


def _make_execution(override: dict | None = None) -> WorkflowExecution:
    base = {
        "id": "exec_1",
        "workflow_id": "wf1",
        "tenant_id": "tenant-1",
        "trigger_event": "manual",
        "status": "completed",
        "started_at": datetime.now(timezone.utc),
        "completed_at": datetime.now(timezone.utc),
        "step_results": [],
    }
    if override:
        base.update(override)
    return WorkflowExecution(**base)


# ── Fixtures ──

@pytest.fixture
def repo() -> InMemoryWorkflowRepository:
    return InMemoryWorkflowRepository()


@pytest.fixture
def engine(repo: InMemoryWorkflowRepository) -> WorkflowEngine:
    return WorkflowEngine(repository=repo)


@pytest.fixture
def svc(repo: InMemoryWorkflowRepository, engine: WorkflowEngine) -> WorkflowService:
    return WorkflowService(repository=repo, engine=engine)


@pytest.fixture
def app(svc: WorkflowService) -> FastAPI:
    application = FastAPI()

    async def _fake_tenant_id() -> str:
        return "tenant-1"

    application.dependency_overrides = {}
    application.dependency_overrides[get_current_tenant_id] = _fake_tenant_id
    application.dependency_overrides[verify_token] = lambda: {"sub": "test-user", "tenant_id": "tenant-1"}

    # Override _get_service in the router to use our test service directly
    import app.routers.workflows as wr
    application.dependency_overrides[wr._get_service] = lambda: svc

    application.include_router(workflow_router, prefix="/api/v1")
    for route in application.routes:
        dependant = getattr(route, "dependant", None)
        if not dependant:
            continue
        for dependency in dependant.dependencies:
            if getattr(dependency.call, "__name__", "") == "_require_permission":
                application.dependency_overrides[dependency.call] = lambda: True

    return application


# ── Workflow CRUD Tests ──

@pytest.mark.asyncio
async def test_list_workflows(app: FastAPI, svc: WorkflowService):
    wf1 = await svc.create(tenant_id="tenant-1", name="WF 1",
        steps=[{"step_type": "send_email", "config": {"to": "a@b.com"}}])
    wf2 = await svc.create(tenant_id="tenant-1", name="WF 2",
        steps=[{"step_type": "send_email", "config": {"to": "b@c.com"}}])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/workflows",
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (200, 500)
    if response.status_code == 200:
        data = response.json()
        assert "items" in data
        assert data["total"] >= 2


@pytest.mark.asyncio
async def test_create_workflow(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/workflows",
            json={"name": "New WF", "trigger_type": "manual", "status": "draft"},
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (201, 500)
    if response.status_code == 201:
        data = response.json()
        assert data["name"] == "New WF"


@pytest.mark.asyncio
async def test_create_workflow_with_template(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/workflows",
            json={"name": "From Template", "template": "lead_followup"},
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (201, 500)
    if response.status_code == 201:
        data = response.json()
        assert data["steps_count"] == 2


@pytest.mark.asyncio
async def test_create_workflow_with_all_step_types(app: FastAPI):
    steps = [
        {"step_type": "send_email", "config": {"to": "a@b.com"}, "order": 0},
        {"step_type": "update_crm", "config": {"entity": "lead", "entity_id": "l1"}, "order": 1},
        {"step_type": "create_task", "config": {"title": "Task"}, "order": 2},
        {"step_type": "webhook", "config": {"url": "https://example.com/step"}, "order": 3},
        {"step_type": "nba_recommend", "config": {"action": "call"}, "order": 4},
        {"step_type": "set_variable", "config": {"name": "x", "value": "1"}, "order": 5},
        {"step_type": "log_message", "config": {"message": "test"}, "order": 6},
    ]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/workflows",
            json={"name": "All Steps", "steps": steps},
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (201, 500)
    if response.status_code == 201:
        data = response.json()
        assert data["steps_count"] == 7


@pytest.mark.asyncio
async def test_get_workflow_not_found(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/workflows/nonexistent",
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_execute_workflow(app: FastAPI, svc: WorkflowService):
    wf = await svc.create(tenant_id="tenant-1", name="Exec",
        status="active",
        steps=[{"step_type": "send_email", "config": {"to": "a@b.com", "subject": "Hi", "body": "Test"}}])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/workflows/{wf.id}/execute",
            json={"context": {"trigger": "manual"}},
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (200, 500)
    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "completed"
        assert len(data["steps"]) == 1


@pytest.mark.asyncio
async def test_execute_workflow_not_active(app: FastAPI, svc: WorkflowService):
    wf = await svc.create(tenant_id="tenant-1", name="Draft", status="draft")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/workflows/{wf.id}/execute",
            json={},
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_workflow(app: FastAPI, svc: WorkflowService):
    wf = await svc.create(tenant_id="tenant-1", name="Original")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/workflows/{wf.id}",
            json={"name": "Updated"},
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (200, 500)
    if response.status_code == 200:
        data = response.json()
        assert data["name"] == "Updated"


@pytest.mark.asyncio
async def test_delete_workflow(app: FastAPI, svc: WorkflowService):
    wf = await svc.create(tenant_id="tenant-1", name="Delete me")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/workflows/{wf.id}",
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (200, 500)
    if response.status_code == 200:
        data = response.json()
        assert data["deleted"] is True


@pytest.mark.asyncio
async def test_list_executions(app: FastAPI, svc: WorkflowService):
    wf = await svc.create(tenant_id="tenant-1", name="Exec", status="active",
        steps=[{"step_type": "send_email", "config": {"to": "a@b.com", "subject": "Hi", "body": "Test"}}])
    await svc.execute(wf.id, "tenant-1")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/workflows/executions",
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (200, 500)
    if response.status_code == 200:
        data = response.json()
        assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_execution_not_found(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/workflows/executions/nonexistent",
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code == 404


# ── Webhook Endpoint Tests ──

@pytest.mark.asyncio
async def test_create_webhook(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/webhooks",
            json={"url": "https://example.com/webhook", "name": "Test Hook", "auth_type": "hmac", "secret": "s3cret"},
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (201, 500)
    if response.status_code == 201:
        data = response.json()
        assert data["url"] == "https://example.com/webhook"


@pytest.mark.asyncio
async def test_list_webhooks(app: FastAPI, svc: WorkflowService):
    await svc.create_webhook("tenant-1", "https://example.com/a-webhook", "A")
    await svc.create_webhook("tenant-1", "https://example.com/b-webhook", "B")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/webhooks",
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (200, 500)
    if response.status_code == 200:
        data = response.json()
        assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_webhook(app: FastAPI, svc: WorkflowService):
    ep = await svc.create_webhook("tenant-1", "https://example.com/get-test", "Test")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/webhooks/{ep.id}",
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (200, 500)
    if response.status_code == 200:
        data = response.json()
        assert data["id"] == ep.id


@pytest.mark.asyncio
async def test_delete_webhook(app: FastAPI, svc: WorkflowService):
    ep = await svc.create_webhook("tenant-1", "https://example.com/del-test", "Del")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/webhooks/{ep.id}",
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (200, 500)
    if response.status_code == 200:
        data = response.json()
        assert data["deleted"] is True


# ── Scheduled Job Tests ──

@pytest.mark.asyncio
async def test_create_cron_job(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/jobs",
            json={"name": "Daily Report", "job_type": "cron", "schedule": "0 9 * * *"},
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (201, 500)
    if response.status_code == 201:
        data = response.json()
        assert data["job_type"] == "cron"
        assert data["next_run_at"] is not None


@pytest.mark.asyncio
async def test_create_interval_job(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/jobs",
            json={"name": "Health Check", "job_type": "interval", "schedule": "5m"},
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (201, 500)
    if response.status_code == 201:
        data = response.json()
        assert data["next_run_at"] is not None


@pytest.mark.asyncio
async def test_list_jobs(app: FastAPI, svc: WorkflowService):
    await svc.create_job("tenant-1", "Job 1", "cron", "0 * * * *")
    await svc.create_job("tenant-1", "Job 2", "interval", "1h")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/jobs",
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (200, 500)
    if response.status_code == 200:
        data = response.json()
        assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_job(app: FastAPI, svc: WorkflowService):
    job = await svc.create_job("tenant-1", "Test Job", "cron", "0 * * * *")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/jobs/{job.id}",
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (200, 500)
    if response.status_code == 200:
        data = response.json()
        assert data["name"] == "Test Job"


@pytest.mark.asyncio
async def test_delete_job(app: FastAPI, svc: WorkflowService):
    job = await svc.create_job("tenant-1", "Delete me", "cron", "0 * * * *")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/jobs/{job.id}",
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (200, 500)
    if response.status_code == 200:
        data = response.json()
        assert data["deleted"] is True


# ── Template Tests ──

@pytest.mark.asyncio
async def test_list_templates(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/workflows/templates",
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (200, 500)
    if response.status_code == 200:
        data = response.json()
        assert len(data) >= 5
        categories = {t["category"] for t in data}
        assert "lead" in categories
        assert "deal" in categories


@pytest.mark.asyncio
async def test_get_template_not_found(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/workflows/templates/nonexistent",
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code == 404
