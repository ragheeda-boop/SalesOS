from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.dependencies import get_current_user_id
from app.routers.approval import (
    ApprovalDecisionRequest,
    ApprovalRequestCreate,
    create_approval,
    decide_approval,
)
from domains.approval.contracts.models import ApprovalStatus, ApprovalTargetType
from domains.approval.engine.service import ApprovalService
from domains.approval.in_memory_repo import InMemoryApprovalRepository


def _request(service: ApprovalService):
    return SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(approval_service=service))
    )


def test_approval_write_routes_derive_actor_from_verified_token_dependency():
    for route in (create_approval, decide_approval):
        assert inspect.signature(route).parameters["user_id"].default.dependency is (
            get_current_user_id
        )


@pytest.mark.asyncio
async def test_create_approval_uses_authenticated_actor_id():
    service = ApprovalService(InMemoryApprovalRepository())
    result = await create_approval(
        ApprovalRequestCreate(
            target_type="ai_action",
            target_id="action-1",
            action_summary="Review proposed company fact",
        ),
        _request(service),
        user_id="authenticated-user-1",
        tenant_id="tenant-1",
    )

    assert result["requested_by"] == "authenticated-user-1"
    assert result["tenant_id"] == "tenant-1"


@pytest.mark.asyncio
async def test_decision_uses_authenticated_actor_and_tenant_scope():
    service = ApprovalService(InMemoryApprovalRepository())
    created = await service.create_request(
        tenant_id="tenant-1",
        target_type=ApprovalTargetType.AI_ACTION,
        target_id="action-1",
        requested_by="creator-1",
        action_summary="Review proposed company fact",
    )

    result = await decide_approval(
        created.id,
        ApprovalDecisionRequest(decision="approve", authority_level="manager"),
        _request(service),
        user_id="authenticated-approver-1",
        tenant_id="tenant-1",
    )
    assert result["status"] == ApprovalStatus.APPROVED.value
    assert result["decisions"][0]["decided_by"] == "authenticated-approver-1"

    with pytest.raises(HTTPException) as exc:
        await decide_approval(
            created.id,
            ApprovalDecisionRequest(decision="approve", authority_level="manager"),
            _request(service),
            user_id="other-tenant-user",
            tenant_id="tenant-2",
        )
    assert exc.value.status_code == 404
