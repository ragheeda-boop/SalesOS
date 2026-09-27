"""app.state.approval_service was READ in exactly 2 places (both in
app/routers/approval.py's _get_service()/_get_optional_service()) and was
NEVER SET anywhere in the entire codebase -- confirmed via repo-wide grep.
The router IS genuinely mounted at /api/v1 (app/boot/routers.py:512), so
every real call to the entire Approval/HITL REST API
(POST/GET /approvals, decision endpoints, etc.) has always returned
503 Service Unavailable, unconditionally, since the router was created.

Independently, app/routers/copilot.py's Recommend-mode branch (P3-1: "HITL
approval gate, no auto-execute") constructed a BRAND NEW
ApprovalService(repository=InMemoryApprovalRepository()) on every single
call -- a disposable, request-scoped, empty in-memory store immediately
garbage-collected once the HTTP response returns. The returned approval_id
looked like a real, trackable identifier, but could never be retrieved
again by anyone -- not via the (also-broken) REST API, not via any other
path. The "human must approve before this executes" gate was, in the
shipped code, completely unenforceable in two independent ways at once.

Fixed by:
  1. Adding _init_approval() to app/boot/startup.py (Phase 1, alongside the
     already-correct _init_decision_center/_init_feature_store_domain
     pattern), wiring a real, tenant-GUC-pinned, Postgres-backed
     ApprovalService onto app.state.approval_service.
  2. Changing copilot.py's Recommend-mode branch to read that same shared
     service via request.app.state.approval_service (failing closed with
     503 if it's somehow not initialized) instead of constructing a
     disposable one.

This test proves the fix works end to end against a real, fully-migrated,
RLS-enforced disposable database: an approval request created exactly the
way _init_approval's wiring would create it is genuinely persisted and
retrievable from a completely separate session -- the actual defect this
fix closes.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.boot.startup import _init_approval
from app.database import apply_tenant_guc, async_session, engine
from domains.approval.contracts.models import ApprovalLevel, ApprovalTargetType
from domains.approval.engine.service import ApprovalService


class _StubLogger:
    def info(self, *a, **k):
        pass

    def exception(self, *a, **k):
        pass


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    async with engine.connect() as conn:
        db_name = await conn.scalar(text("SELECT current_database()"))
    assert db_name != "salesos", (
        f"REFUSING: connected to {db_name!r} — this is the persistent "
        "local dev database, not a disposable/test one."
    )
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_init_approval_wires_a_real_persistent_service():
    """_init_approval() must set app.state.approval_service to a real,
    working ApprovalService — not leave it unset (the original defect)."""
    fake_app = SimpleNamespace(state=SimpleNamespace())

    await _init_approval(fake_app, _StubLogger())

    svc = getattr(fake_app.state, "approval_service", None)
    assert svc is not None, "approval_service was never set — the original bug"
    assert isinstance(svc, ApprovalService)

    tenant_id = str(uuid.uuid4())
    async with async_session() as s:
        await apply_tenant_guc(s, tenant_id)
        from app.modules.identity.models import Tenant

        s.add(Tenant(id=uuid.UUID(tenant_id), name="T", slug=f"slug-{tenant_id}"))
        await s.commit()

    created = await svc.create_request(
        tenant_id=tenant_id,
        target_type=ApprovalTargetType.NBA_RECOMMENDATION,
        target_id="copilot_conv_1",
        requested_by="user-1",
        action_summary="Test recommendation requiring approval",
        required_level=ApprovalLevel.MANAGER,
    )

    # The wired service must genuinely persist — retrievable through the
    # exact same service object (proxied per-call via FactoryBoundRepository,
    # a fresh session each time, not an in-memory dict tied to this object).
    fetched = await svc.get(created.id)
    assert fetched is not None, (
        "approval request not found on retrieval — still behaving like a "
        "disposable, per-call in-memory store"
    )
    assert fetched.id == created.id
    assert fetched.action_summary == "Test recommendation requiring approval"
    assert fetched.tenant_id == tenant_id


@pytest.mark.asyncio
async def test_approval_router_service_lookup_finds_the_wired_service():
    """app/routers/approval.py's _get_service()/_get_optional_service()
    read app.state.approval_service via a bare getattr — confirm that once
    _init_approval() has run, that exact lookup succeeds (previously it
    always found None and every endpoint 503'd)."""
    fake_app = SimpleNamespace(state=SimpleNamespace())
    await _init_approval(fake_app, _StubLogger())

    from app.routers.approval import _get_optional_service

    fake_request = SimpleNamespace(app=fake_app)
    svc = _get_optional_service(fake_request)
    assert svc is not None
    assert isinstance(svc, ApprovalService)
