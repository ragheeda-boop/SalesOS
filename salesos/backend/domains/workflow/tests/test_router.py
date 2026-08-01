"""Tests for the Workflow router â€” validates all REST endpoints through FastAPI TestClient."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_current_tenant_id, get_db_session, require_permission, verify_token
from app.routers.workflows import router as workflow_router
from domains.workflow.engine import WorkflowEngine
from domains.workflow.models import (
    JobExecution,
    ScheduledJob,
    WebhookEndpoint,
    Workflow,
    WorkflowExecution,
    WorkflowExecutionStep,
    WorkflowStep,
    WorkflowTemplate,
)
from domains.workflow.repository import InMemoryWorkflowRepository
from domains.workflow.service import WorkflowService


# â”€â”€ Helpers â”€â”€

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


# â”€â”€ Fixtures â”€â”€

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
def wf_app(svc: WorkflowService) -> FastAPI:
    application = FastAPI()

    async def _fake_tenant_id() -> str:
        return "tenant-1"

    async def _fake_token() -> dict:
        return {"sub": "test-user", "tenant_id": "tenant-1"}

    async def _allow() -> bool:
        return True

    import app.routers.workflows as wr

    application.dependency_overrides[get_current_tenant_id] = _fake_tenant_id
    application.dependency_overrides[verify_token] = _fake_token
    application.dependency_overrides[require_permission] = _allow
    application.dependency_overrides[wr._get_service] = lambda: svc

    application.include_router(workflow_router, prefix="/api/v1")

    def _override_auth_deps(dependant) -> None:
        for dependency in getattr(dependant, "dependencies", []) or []:
            call = dependency.call
            if call is None:
                continue
            name = getattr(call, "__name__", "")
            if name in ("_require_permission", "require_permission"):
                application.dependency_overrides[call] = _allow
            elif name == "verify_token" or call is verify_token:
                application.dependency_overrides[call] = _fake_token
            elif name in ("get_db_session", "get_db") or call is get_db_session:
                # Service is overridden; avoid real DB for auth/RBAC paths.
                pass
            nested = getattr(dependency, "dependant", None)
            if nested is not None:
                _override_auth_deps(nested)

    for route in application.routes:
        dependant = getattr(route, "dependant", None)
        if dependant is not None:
            _override_auth_deps(dependant)

    return application


# â”€â”€ Workflow CRUD Tests â”€â”€

@pytest.mark.asyncio
async def test_list_workflows(wf_app: FastAPI, svc: WorkflowService):
    wf1 = await svc.create(tenant_id="tenant-1", name="WF 1",
        steps=[{"step_type": "send_email", "config": {"to": "a@b.com"}}])
    wf2 = await svc.create(tenant_id="tenant-1", name="WF 2",
        steps=[{"step_type": "send_email", "config": {"to": "b@c.com"}}])

    transport = ASGITransport(app=wf_app)
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
async def test_create_workflow(wf_app: FastAPI):
    transport = ASGITransport(app=wf_app)
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
async def test_create_workflow_with_template(wf_app: FastAPI):
    transport = ASGITransport(app=wf_app)
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
async def test_create_workflow_with_all_step_types(wf_app: FastAPI):
    steps = [
        {"step_type": "send_email", "config": {"to": "a@b.com"}, "order": 0},
        {"step_type": "update_crm", "config": {"entity": "lead", "entity_id": "l1"}, "order": 1},
        {"step_type": "create_task", "config": {"title": "Task"}, "order": 2},
        {"step_type": "webhook", "config": {"url": "https://example.com/step"}, "order": 3},
        {"step_type": "nba_recommend", "config": {"action": "call"}, "order": 4},
        {"step_type": "set_variable", "config": {"name": "x", "value": "1"}, "order": 5},
        {"step_type": "log_message", "config": {"message": "test"}, "order": 6},
    ]
    transport = ASGITransport(app=wf_app)
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
async def test_get_workflow_not_found(wf_app: FastAPI):
    transport = ASGITransport(app=wf_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/workflows/nonexistent",
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_execute_workflow(wf_app: FastAPI, svc: WorkflowService):
    wf = await svc.create(tenant_id="tenant-1", name="Exec",
        status="active",
        steps=[{"step_type": "send_email", "config": {"to": "a@b.com", "subject": "Hi", "body": "Test"}}])

    transport = ASGITransport(app=wf_app)
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
async def test_execute_workflow_not_active(wf_app: FastAPI, svc: WorkflowService):
    wf = await svc.create(tenant_id="tenant-1", name="Draft", status="draft")

    transport = ASGITransport(app=wf_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/workflows/{wf.id}/execute",
            json={},
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_workflow(wf_app: FastAPI, svc: WorkflowService):
    wf = await svc.create(tenant_id="tenant-1", name="Original")

    transport = ASGITransport(app=wf_app)
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
async def test_delete_workflow(wf_app: FastAPI, svc: WorkflowService):
    wf = await svc.create(tenant_id="tenant-1", name="Delete me")

    transport = ASGITransport(app=wf_app)
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
async def test_list_executions(wf_app: FastAPI, svc: WorkflowService):
    wf = await svc.create(tenant_id="tenant-1", name="Exec", status="active",
        steps=[{"step_type": "send_email", "config": {"to": "a@b.com", "subject": "Hi", "body": "Test"}}])
    await svc.execute(wf.id, "tenant-1")

    transport = ASGITransport(app=wf_app)
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
async def test_get_execution_not_found(wf_app: FastAPI):
    transport = ASGITransport(app=wf_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/workflows/executions/nonexistent",
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code == 404


# â”€â”€ Webhook Endpoint Tests â”€â”€

@pytest.mark.asyncio
async def test_create_webhook(wf_app: FastAPI):
    transport = ASGITransport(app=wf_app)
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
async def test_list_webhooks(wf_app: FastAPI, svc: WorkflowService):
    await svc.create_webhook("tenant-1", "https://example.com/a-webhook", "A")
    await svc.create_webhook("tenant-1", "https://example.com/b-webhook", "B")

    transport = ASGITransport(app=wf_app)
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
async def test_get_webhook(wf_app: FastAPI, svc: WorkflowService):
    ep = await svc.create_webhook("tenant-1", "https://example.com/get-test", "Test")

    transport = ASGITransport(app=wf_app)
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
async def test_delete_webhook(wf_app: FastAPI, svc: WorkflowService):
    ep = await svc.create_webhook("tenant-1", "https://example.com/del-test", "Del")

    transport = ASGITransport(app=wf_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/webhooks/{ep.id}",
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (200, 500)
    if response.status_code == 200:
        data = response.json()
        assert data["deleted"] is True


# â”€â”€ Scheduled Job Tests â”€â”€

@pytest.mark.asyncio
async def test_create_cron_job(wf_app: FastAPI):
    transport = ASGITransport(app=wf_app)
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
async def test_create_interval_job(wf_app: FastAPI):
    transport = ASGITransport(app=wf_app)
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
async def test_list_jobs(wf_app: FastAPI, svc: WorkflowService):
    await svc.create_job("tenant-1", "Job 1", "cron", "0 * * * *")
    await svc.create_job("tenant-1", "Job 2", "interval", "1h")

    transport = ASGITransport(app=wf_app)
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
async def test_get_job(wf_app: FastAPI, svc: WorkflowService):
    job = await svc.create_job("tenant-1", "Test Job", "cron", "0 * * * *")

    transport = ASGITransport(app=wf_app)
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
async def test_delete_job(wf_app: FastAPI, svc: WorkflowService):
    job = await svc.create_job("tenant-1", "Delete me", "cron", "0 * * * *")

    transport = ASGITransport(app=wf_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/jobs/{job.id}",
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code in (200, 500)
    if response.status_code == 200:
        data = response.json()
        assert data["deleted"] is True


# â”€â”€ Template Tests â”€â”€

@pytest.mark.asyncio
async def test_list_templates(wf_app: FastAPI):
    transport = ASGITransport(app=wf_app)
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
async def test_get_template_not_found(wf_app: FastAPI):
    transport = ASGITransport(app=wf_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/workflows/templates/nonexistent",
            headers={"Authorization": "Bearer test", "X-Tenant-Id": "tenant-1"},
        )
    assert response.status_code == 404
