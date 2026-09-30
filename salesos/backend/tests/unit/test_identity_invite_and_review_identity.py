"""Invite fail-closed role assignment + review decider identity from the JWT."""

from __future__ import annotations

import inspect
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.dependencies import get_current_tenant_id, get_current_user_id, get_db_session
from app.modules.identity.router import invite_user
from app.modules.identity.schemas import InviteUserRequest
from app.routers import commercial
from app.routers.commercial import decide_review
from domains.commercial.review.contracts.models import ReviewType
from domains.commercial.review.engine.in_memory_repo import InMemoryReviewRepository
from domains.commercial.review.engine.service import ReviewService


def _service(update_side_effect=None, update_role="admin"):
    created = SimpleNamespace(id="u-1", role="user")
    svc = SimpleNamespace(
        create_user=AsyncMock(return_value=created),
        update_user_role=AsyncMock(
            side_effect=update_side_effect,
            return_value=SimpleNamespace(id="u-1", role=update_role),
        ),
    )
    return svc


@pytest.mark.asyncio
async def test_invite_fails_closed_when_role_assignment_raises():
    svc = _service(update_side_effect=RuntimeError("db down"))
    db = SimpleNamespace(rollback=AsyncMock())

    with pytest.raises(HTTPException) as exc:
        await invite_user(
            InviteUserRequest(email="new@example.com", role="manager"),
            tenant_id="tenant-1",
            service=svc,
            db=db,
            _=None,
        )

    assert exc.value.status_code == 500
    db.rollback.assert_awaited_once()
    assert "password" not in str(exc.value.detail).lower()


@pytest.mark.asyncio
async def test_invite_fails_closed_when_role_not_applied():
    svc = _service(update_role="user")
    db = SimpleNamespace(rollback=AsyncMock())

    with pytest.raises(HTTPException) as exc:
        await invite_user(
            InviteUserRequest(email="new@example.com", role="manager"),
            tenant_id="tenant-1",
            service=svc,
            db=db,
            _=None,
        )

    assert exc.value.status_code == 500
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_default_invite_creates_ordinary_user():
    svc = _service()
    db = SimpleNamespace(rollback=AsyncMock())

    result = await invite_user(
        InviteUserRequest(email="new@example.com"),
        tenant_id="tenant-1",
        service=svc,
        db=db,
        _=None,
    )

    assert result["role"] == "user"
    svc.update_user_role.assert_not_awaited()
    db.rollback.assert_not_awaited()


def test_decide_review_actor_comes_from_verified_token_dependency():
    param = inspect.signature(decide_review).parameters["decided_by"]
    assert param.default.dependency is get_current_user_id


@pytest.fixture
def review_service(monkeypatch):
    svc = ReviewService(InMemoryReviewRepository())
    monkeypatch.setattr(commercial, "_get_review", lambda db: svc)
    return svc


@pytest.mark.asyncio
async def test_decide_review_records_jwt_subject(review_service):
    review = await review_service.create_review(
        "tenant-1", ReviewType.DEAL_REVIEW, "opp-1", "opportunity"
    )

    await decide_review(
        review.id,
        decision="approve",
        comments="",
        tenant_id="tenant-1",
        decided_by="jwt-user-1",
        db=None,
        _rbac=None,
    )

    stored = await review_service.get(review.id)
    assert stored.decisions[-1].decided_by == "jwt-user-1"


@pytest.mark.asyncio
async def test_decide_review_ignores_spoofed_query_parameter(review_service):
    review = await review_service.create_review(
        "tenant-1", ReviewType.DEAL_REVIEW, "opp-1", "opportunity"
    )
    rbac = inspect.signature(decide_review).parameters["_rbac"].default.dependency

    app = FastAPI()
    app.include_router(commercial.router)
    app.dependency_overrides[get_current_tenant_id] = lambda: "tenant-1"
    app.dependency_overrides[get_current_user_id] = lambda: "jwt-user-1"
    app.dependency_overrides[get_db_session] = lambda: None
    app.dependency_overrides[rbac] = lambda: None

    resp = TestClient(app).post(
        f"/reviews/{review.id}/decide",
        params={"decision": "approve", "decided_by": "spoofed-manager"},
    )

    assert resp.status_code == 200, resp.text
    stored = await review_service.get(review.id)
    assert stored.decisions[-1].decided_by == "jwt-user-1"
