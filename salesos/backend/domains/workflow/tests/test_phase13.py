"""Phase 13 Automation Backend Tests — advanced engine, webhook auth, scheduler, templates."""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from domains.workflow.engine import WorkflowEngine, _eval_condition, _resolve_config
from domains.workflow.models import (
    JobExecution,
    ScheduledJob,
    WebhookEndpoint,
    Workflow,
    WorkflowExecution,
    WorkflowStep,
)
from domains.workflow.repository import InMemoryWorkflowRepository
from domains.workflow.scheduler import (
    JobScheduler,
    parse_cron_next_run,
    parse_interval_next_run,
    parse_one_time_next_run,
)
from domains.workflow.service import WorkflowService, WorkflowValidationError
from domains.workflow.webhook_auth import (
    WebhookAuthenticator,
    compute_hmac_signature,
    verify_hmac_signature,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_step(step_id="step1", step_type="webhook", config=None, order=0, condition=None, **kwargs):
    return WorkflowStep(
        id=step_id,
        workflow_id="wf1",
        step_type=step_type,
        config=config or {},
        order=order,
        condition=condition,
        timeout_seconds=kwargs.get("timeout_seconds"),
        on_failure=kwargs.get("on_failure", "fail_workflow"),
    )


def _make_repo():
    return InMemoryWorkflowRepository()


def _make_engine():
    return WorkflowEngine(repository=_make_repo())


# ── B-1: IF/ELSE Conditional Tests ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_if_else_takes_then_branch():
    engine = _make_engine()
    result = await engine._handle_if_else(
        {"condition": "amount > 100", "then_steps": [{"step_type": "log_message", "config": {"message": "high"}}], "else_steps": []},
        {"amount": 200},
        _make_step(),
    )
    assert result["branch"] == "then"
    assert len(result["results"]) == 1
    assert result["results"][0]["status"] == "completed"


@pytest.mark.asyncio
async def test_if_else_takes_else_branch():
    engine = _make_engine()
    result = await engine._handle_if_else(
        {"condition": "amount > 100", "then_steps": [], "else_steps": [{"step_type": "log_message", "config": {"message": "low"}}]},
        {"amount": 50},
        _make_step(),
    )
    assert result["branch"] == "else"
    assert len(result["results"]) == 1


@pytest.mark.asyncio
async def test_if_else_no_handler_skips():
    engine = _make_engine()
    result = await engine._handle_if_else(
        {"condition": "amount > 100", "then_steps": [{"step_type": "nonexistent", "config": {}}], "else_steps": []},
        {"amount": 200},
        _make_step(),
    )
    assert result["results"][0]["status"] == "skipped"


# ── B-1: FOR Loop Tests ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_for_each_iterates_collection():
    engine = _make_engine()
    result = await engine._handle_for_each(
        {"collection_key": "items", "item_var": "item", "steps": [{"step_type": "log_message", "config": {"message": "processing {{context.item}}"}}]},
        {"items": ["a", "b", "c"]},
        _make_step(),
    )
    assert result["iterations"] == 3
    assert len(result["results"]) == 3
    assert all(r["status"] == "completed" for r in result["results"])


@pytest.mark.asyncio
async def test_for_each_empty_collection():
    engine = _make_engine()
    result = await engine._handle_for_each(
        {"collection_key": "items", "item_var": "item", "steps": [{"step_type": "log_message", "config": {"message": "x"}}]},
        {"items": []},
        _make_step(),
    )
    assert result["iterations"] == 0
    assert len(result["results"]) == 0


@pytest.mark.asyncio
async def test_for_each_non_list_coerced():
    engine = _make_engine()
    result = await engine._handle_for_each(
        {"collection_key": "item", "item_var": "x", "steps": [{"step_type": "log_message", "config": {"message": "ok"}}]},
        {"item": "single"},
        _make_step(),
    )
    assert result["iterations"] == 1


# ── B-1: Parallel Branch Tests ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_parallel_executes_concurrently():
    engine = _make_engine()
    result = await engine._handle_parallel(
        {
            "branches": [
                [{"step_type": "log_message", "config": {"message": "branch1"}}],
                [{"step_type": "log_message", "config": {"message": "branch2"}}],
            ]
        },
        {},
        _make_step(),
    )
    assert result["branches_count"] == 2
    assert len(result["results"]) == 2
    assert all(r["status"] == "completed" for r in result["results"])


@pytest.mark.asyncio
async def test_parallel_handles_failure_in_branch():
    engine = _make_engine()
    result = await engine._handle_parallel(
        {
            "branches": [
                [{"step_type": "log_message", "config": {"message": "ok"}}],
                [{"step_type": "webhook", "config": {"url": ""}}],
            ]
        },
        {},
        _make_step(),
    )
    assert result["results"][0]["status"] == "completed"
    assert result["results"][1]["status"] == "failed"


# ── B-1: Timeout Tests ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_step_timeout_triggers():
    engine = _make_engine()

    async def slow_handler(config, context, step=None):
        await asyncio.sleep(10)
        return {}

    engine.register_handler("slow_handler", slow_handler)
    step = _make_step(step_type="slow_handler", timeout_seconds=0.1)
    result = await engine._execute_step(step, {})
    assert result.status == "timed_out"
    assert "timed out" in (result.error or "")


@pytest.mark.asyncio
async def test_workflow_level_timeout():
    repo = _make_repo()
    engine = WorkflowEngine(repository=repo)
    wf = Workflow(
        id="wf1", tenant_id="t1", name="Timeout WF", status="active",
        timeout_seconds=0.1,
        steps=[_make_step("s1", "send_email", {"to": "a@b.com", "subject": "Hi"}, order=0)],
    )
    await repo.create(wf)
    # Patch the handler to be slow
    async def slow(config, ctx, step=None):
        await asyncio.sleep(10)
        return {}
    engine.register_handler("send_email", slow)
    execution = await engine.execute(wf, {})
    assert execution.status == "timed_out"


# ── B-1: Step State Machine Tests ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_step_on_failure_skip():
    engine = _make_engine()
    step = _make_step(step_type="webhook", config={"url": ""}, on_failure="skip")
    result = await engine._execute_step(step, {})
    assert result.status == "failed"  # _execute_step returns failed; on_failure is handled at _run_steps level


@pytest.mark.asyncio
async def test_set_variable_handler():
    engine = _make_engine()
    ctx: dict = {}
    result = await engine._handle_set_variable({"name": "myvar", "value": "hello"}, ctx, _make_step())
    assert result["set"] is True
    assert ctx["myvar"] == "hello"


@pytest.mark.asyncio
async def test_log_message_handler():
    engine = _make_engine()
    result = await engine._handle_log_message({"level": "info", "message": "test log"}, {}, _make_step())
    assert result["logged"] is True


# ── B-2: Webhook Auth Tests ─────────────────────────────────────────────────


def test_hmac_signature_computation():
    payload = b'{"key": "value"}'
    secret = "my-secret"
    sig = compute_hmac_signature(payload, secret)
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert sig == expected


def test_hmac_signature_verification():
    payload = b'{"key": "value"}'
    secret = "my-secret"
    sig = compute_hmac_signature(payload, secret)
    assert verify_hmac_signature(payload, sig, secret) is True
    assert verify_hmac_signature(payload, "wrong-sig", secret) is False


@pytest.mark.asyncio
async def test_webhook_authenticator_sign_hmac():
    auth = WebhookAuthenticator()
    endpoint = WebhookEndpoint(
        id="ep1", tenant_id="t1",         url="https://example.com/hmac-auth", auth_type="hmac", secret="s3cret",
    )
    payload = {"data": "test"}
    headers = auth.sign_request(endpoint, payload)
    assert "X-Webhook-Signature" in headers
    assert headers["X-Webhook-Signature"].startswith("sha256=")


@pytest.mark.asyncio
async def test_webhook_authenticator_sign_jwt():
    auth = WebhookAuthenticator()
    endpoint = WebhookEndpoint(
        id="ep1", tenant_id="t1", url="https://hooks.example.com/jwt-auth", auth_type="jwt", secret="jwt-secret",
    )
    headers = auth.sign_request(endpoint, {"data": "test"})
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Bearer ")


@pytest.mark.asyncio
async def test_webhook_authenticator_sign_none():
    auth = WebhookAuthenticator()
    endpoint = WebhookEndpoint(
        id="ep1", tenant_id="t1", url="https://hooks.example.com/none-auth", auth_type="none",
    )
    headers = auth.sign_request(endpoint, {"data": "test"})
    assert "X-Webhook-Signature" not in headers
    assert "Authorization" not in headers


@pytest.mark.asyncio
async def test_webhook_authenticator_validate_hmac():
    auth = WebhookAuthenticator()
    endpoint = WebhookEndpoint(
        id="ep1", tenant_id="t1", url="https://example.com/hmac-validate", auth_type="hmac", secret="s3cret",
    )
    payload = b'{"data": "test"}'
    sig = compute_hmac_signature(payload, "s3cret")
    headers = {"X-Webhook-Signature": f"sha256={sig}"}
    assert auth.validate_incoming(endpoint, payload, headers) is True
    headers_bad = {"X-Webhook-Signature": "sha256=wrong"}
    assert auth.validate_incoming(endpoint, payload, headers_bad) is False


@pytest.mark.asyncio
async def test_webhook_authenticator_validate_no_signature():
    auth = WebhookAuthenticator()
    endpoint = WebhookEndpoint(
        id="ep1", tenant_id="t1", url="https://example.com/hmac-no-sig", auth_type="hmac", secret="s3cret",
    )
    assert auth.validate_incoming(endpoint, b'{}', {}) is False


@pytest.mark.asyncio
async def test_webhook_authenticator_validate_jwt():
    auth = WebhookAuthenticator()
    endpoint = WebhookEndpoint(
        id="ep1", tenant_id="t1", url="https://hooks.example.com/jwt-auth", auth_type="jwt", secret="jwt-secret",
    )
    from domains.workflow.webhook_auth import generate_jwt_token
    token = generate_jwt_token("jwt-secret", {"tenant_id": "t1", "endpoint_id": "ep1"})
    headers = {"Authorization": f"Bearer {token}"}
    assert auth.validate_incoming(endpoint, b'{}', headers) is True
    bad_headers = {"Authorization": "Bearer invalid-token"}
    assert auth.validate_incoming(endpoint, b'{}', bad_headers) is False


@pytest.mark.asyncio
async def test_webhook_authenticator_validate_none():
    auth = WebhookAuthenticator()
    endpoint = WebhookEndpoint(
        id="ep1", tenant_id="t1", url="https://hooks.example.com/none-auth", auth_type="none",
    )
    assert auth.validate_incoming(endpoint, b'{}', {}) is True


# ── B-3: Scheduler Tests ────────────────────────────────────────────────────


def test_parse_cron_next_run_simple():
    now = datetime(2026, 7, 16, 10, 0, 0, tzinfo=timezone.utc)
    result = parse_cron_next_run("0 12 * * *", now)
    assert result is not None
    assert result.hour == 12
    assert result > now


def test_parse_cron_next_run_every_5_min():
    now = datetime(2026, 7, 16, 10, 2, 0, tzinfo=timezone.utc)
    result = parse_cron_next_run("*/5 * * * *", now)
    assert result is not None
    assert result.minute == 5


def test_parse_cron_next_run_invalid():
    assert parse_cron_next_run("invalid") is None


def test_parse_interval_next_run_minutes():
    now = datetime(2026, 7, 16, 10, 0, 0, tzinfo=timezone.utc)
    result = parse_interval_next_run("30m", now, now)
    assert result is not None
    assert result == now + timedelta(minutes=30)


def test_parse_interval_next_run_hours():
    now = datetime(2026, 7, 16, 10, 0, 0, tzinfo=timezone.utc)
    result = parse_interval_next_run("2h", now, now)
    assert result is not None
    assert result == now + timedelta(hours=2)


def test_parse_interval_next_run_days():
    now = datetime(2026, 7, 16, 10, 0, 0, tzinfo=timezone.utc)
    result = parse_interval_next_run("7d", now, now)
    assert result is not None
    assert result == now + timedelta(days=7)


def test_parse_interval_next_run_invalid():
    assert parse_interval_next_run("invalid") is None


def test_parse_one_time_next_run():
    result = parse_one_time_next_run("2026-08-01T09:00:00Z")
    assert result is not None
    assert result.year == 2026
    assert result.month == 8


def test_parse_one_time_next_run_invalid():
    assert parse_one_time_next_run("not-a-date") is None


@pytest.mark.asyncio
async def test_job_scheduler_tick_cron():
    repo = _make_repo()
    scheduler = JobScheduler(repo)

    now = datetime(2026, 7, 16, 10, 0, 0, tzinfo=timezone.utc)
    job = ScheduledJob(
        id="j1", tenant_id="t1", job_type="cron", name="test-cron",
        schedule="0 * * * *", status="active",
        next_run_at=now - timedelta(minutes=1),
    )
    await repo.create_job(job)

    handler_called = {"called": False}

    async def test_handler(config, payload, tenant_id):
        handler_called["called"] = True
        return {"ok": True}

    scheduler.register_handler("cron", test_handler)
    executions = await scheduler.tick(now)
    assert len(executions) == 1
    assert executions[0].status == "completed"
    assert handler_called["called"] is True


@pytest.mark.asyncio
async def test_job_scheduler_tick_no_due_jobs():
    repo = _make_repo()
    scheduler = JobScheduler(repo)
    now = datetime(2026, 7, 16, 10, 0, 0, tzinfo=timezone.utc)
    job = ScheduledJob(
        id="j1", tenant_id="t1", job_type="cron", name="test",
        schedule="0 * * * *", status="active",
        next_run_at=now + timedelta(hours=1),
    )
    await repo.create_job(job)
    executions = await scheduler.tick(now)
    assert len(executions) == 0


@pytest.mark.asyncio
async def test_job_scheduler_handles_failure():
    repo = _make_repo()
    scheduler = JobScheduler(repo)
    now = datetime(2026, 7, 16, 10, 0, 0, tzinfo=timezone.utc)
    job = ScheduledJob(
        id="j1", tenant_id="t1", job_type="cron", name="test",
        schedule="0 * * * *", status="active",
        next_run_at=now - timedelta(minutes=1), max_retries=1,
    )
    await repo.create_job(job)

    async def failing_handler(config, payload, tenant_id):
        raise ValueError("handler failed")

    scheduler.register_handler("cron", failing_handler)
    executions = await scheduler.tick(now)
    assert len(executions) == 1
    assert executions[0].status == "failed"
    updated_job = await repo.get_job("j1", "t1")
    assert updated_job.retry_count == 1


@pytest.mark.asyncio
async def test_job_scheduler_no_handler():
    repo = _make_repo()
    scheduler = JobScheduler(repo)
    now = datetime(2026, 7, 16, 10, 0, 0, tzinfo=timezone.utc)
    job = ScheduledJob(
        id="j1", tenant_id="t1", job_type="unknown", name="test",
        schedule="0 * * * *", status="active",
        next_run_at=now - timedelta(minutes=1),
    )
    await repo.create_job(job)
    executions = await scheduler.tick(now)
    assert len(executions) == 1
    assert executions[0].status == "failed"
    assert "No handler" in (executions[0].error or "")


# ── B-3: Scheduler Job CRUD via Service ─────────────────────────────────────


@pytest.mark.asyncio
async def test_service_create_cron_job():
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    job = await svc.create_job("t1", "Daily Report", "cron", "0 9 * * *")
    assert job.id is not None
    assert job.status == "active"
    assert job.next_run_at is not None


@pytest.mark.asyncio
async def test_service_create_interval_job():
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    job = await svc.create_job("t1", "Health Check", "interval", "5m")
    assert job.next_run_at is not None


@pytest.mark.asyncio
async def test_service_create_one_time_job():
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    job = await svc.create_job("t1", "One Shot", "one_time", "2026-08-01T09:00:00Z")
    assert job.next_run_at is not None


@pytest.mark.asyncio
async def test_service_create_job_invalid_type():
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    with pytest.raises(WorkflowValidationError, match="Invalid job_type"):
        await svc.create_job("t1", "Bad", "invalid", "0 * * * *")


@pytest.mark.asyncio
async def test_service_list_jobs():
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    await svc.create_job("t1", "Job 1", "cron", "0 * * * *")
    await svc.create_job("t1", "Job 2", "interval", "1h")
    await svc.create_job("t2", "Job 3", "cron", "0 * * * *")
    jobs = await svc.list_jobs("t1")
    assert len(jobs) == 2


# ── B-4: Template Tests ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_service_list_templates():
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    templates = await svc.list_templates()
    assert len(templates) >= 5
    categories = {t.category for t in templates}
    assert "lead" in categories
    assert "deal" in categories
    assert "renewal" in categories
    assert "onboarding" in categories
    assert "follow_up" in categories


@pytest.mark.asyncio
async def test_service_get_template():
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    templates = await svc.list_templates()
    first = templates[0]
    fetched = await svc.get_template(first.id)
    assert fetched is not None
    assert fetched.name == first.name


@pytest.mark.asyncio
async def test_service_get_template_not_found():
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    fetched = await svc.get_template("nonexistent")
    assert fetched is None


@pytest.mark.asyncio
async def test_all_templates_have_required_fields():
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    templates = await svc.list_templates()
    for t in templates:
        assert t.id
        assert t.name
        assert t.description
        assert t.category
        assert t.steps
        assert t.trigger_type


# ── B-4: Webhook CRUD via Service ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_service_create_webhook():
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    ep = await svc.create_webhook("t1", "https://example.com/svc-create", "Test Hook", "hmac", secret="s3cret")
    assert ep.id is not None
    assert ep.auth_type == "hmac"


@pytest.mark.asyncio
async def test_service_list_webhooks():
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    await svc.create_webhook("t1", "https://example.com/a-svc", "A")
    await svc.create_webhook("t1", "https://example.com/b-svc", "B")
    await svc.create_webhook("t2", "https://example.com/c-svc", "C")
    eps = await svc.list_webhooks("t1")
    assert len(eps) == 2


@pytest.mark.asyncio
async def test_service_delete_webhook():
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    ep = await svc.create_webhook("t1", "https://example.com/svc-del", "Del")
    await svc.delete_webhook(ep.id, "t1")
    assert await svc.get_webhook(ep.id, "t1") is None


@pytest.mark.asyncio
async def test_service_delete_webhook_not_found():
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    with pytest.raises(WorkflowValidationError, match="not found"):
        await svc.delete_webhook("nonexistent", "t1")


# ── SSRF Adversarial Tests ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_webhook_rejects_http():
    """SSRF-01: create_webhook must reject plain HTTP URLs."""
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    from app.modules.webhooks.url_safety import UnsafeWebhookURLError
    with pytest.raises(UnsafeWebhookURLError, match="HTTPS"):
        await svc.create_webhook("t1", "http://example.com", "SSRF Test")


@pytest.mark.asyncio
async def test_create_webhook_rejects_localhost():
    """SSRF-02: create_webhook must reject localhost URLs."""
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    from app.modules.webhooks.url_safety import UnsafeWebhookURLError
    with pytest.raises(UnsafeWebhookURLError):
        await svc.create_webhook("t1", "https://localhost:8080/hook", "SSRF Test")


@pytest.mark.asyncio
async def test_create_webhook_rejects_private_ip():
    """SSRF-03: create_webhook must reject private IP URLs."""
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    from app.modules.webhooks.url_safety import UnsafeWebhookURLError
    with pytest.raises(UnsafeWebhookURLError):
        await svc.create_webhook("t1", "https://10.0.0.1/hook", "SSRF Test")
    with pytest.raises(UnsafeWebhookURLError):
        await svc.create_webhook("t1", "https://192.168.1.1/hook", "SSRF Test")
    with pytest.raises(UnsafeWebhookURLError):
        await svc.create_webhook("t1", "https://127.0.0.1/hook", "SSRF Test")


@pytest.mark.asyncio
async def test_create_webhook_rejects_loopback_hostname():
    """SSRF-04: create_webhook must reject loopback hostname."""
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    from app.modules.webhooks.url_safety import UnsafeWebhookURLError
    with pytest.raises(UnsafeWebhookURLError):
        await svc.create_webhook("t1", "https://127.0.0.1.nip.io/hook", "SSRF Test")


@pytest.mark.asyncio
async def test_update_webhook_rejects_http():
    """SSRF-05: update_webhook must reject plain HTTP URLs."""
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    ep = await svc.create_webhook("t1", "https://example.com/update-ssrf", "SSRF Test")
    from app.modules.webhooks.url_safety import UnsafeWebhookURLError
    with pytest.raises(UnsafeWebhookURLError, match="HTTPS"):
        await svc.update_webhook(ep.id, "t1", url="http://evil.com/hook")


@pytest.mark.asyncio
async def test_update_webhook_rejects_localhost():
    """SSRF-06: update_webhook must reject localhost URLs."""
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    ep = await svc.create_webhook("t1", "https://example.com/update-ssrf2", "SSRF Test")
    from app.modules.webhooks.url_safety import UnsafeWebhookURLError
    with pytest.raises(UnsafeWebhookURLError):
        await svc.update_webhook(ep.id, "t1", url="https://localhost:443/hook")


@pytest.mark.asyncio
async def test_valid_https_webhook_passes():
    """SSRF-07: valid HTTPS URLs must pass through create_webhook."""
    repo = _make_repo()
    svc = WorkflowService(repository=repo)
    ep = await svc.create_webhook("t1", "https://example.com/valid-hook", "Valid")
    assert ep.url == "https://example.com/valid-hook"
