"""Phase 3 HITL — Approval workflow domain tests.

Covers P3-5: Human-in-the-loop approval workflow for AI recommendations.
"""
from __future__ import annotations

import asyncio
import pytest
from datetime import datetime, timezone, timedelta

from domains.approval.contracts.models import (
    ApprovalDecision,
    ApprovalLevel,
    ApprovalRequest,
    ApprovalStatus,
    ApprovalTargetType,
)
from domains.approval.engine.service import ApprovalService
from domains.approval.in_memory_repo import InMemoryApprovalRepository


@pytest.fixture
def repo():
    return InMemoryApprovalRepository()


@pytest.fixture
def service(repo):
    return ApprovalService(repository=repo)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ═══ Model tests ═══

class TestApprovalModels:

    def test_target_type_values(self):
        assert ApprovalTargetType.NBA_RECOMMENDATION.value == "nba_recommendation"
        assert ApprovalTargetType.AI_ACTION.value == "ai_action"

    def test_status_values(self):
        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.REJECTED.value == "rejected"

    def test_level_values(self):
        assert ApprovalLevel.SELF.value == "self"
        assert ApprovalLevel.MANAGER.value == "manager"
        assert ApprovalLevel.VP.value == "vp"
        assert ApprovalLevel.EXECUTIVE.value == "executive"

    def test_request_creation(self):
        req = ApprovalRequest(
            id="r1", tenant_id="t1",
            target_type=ApprovalTargetType.NBA_RECOMMENDATION,
            target_id="nba-1", requested_by="user-1",
            action_summary="Schedule demo call",
        )
        assert req.status == ApprovalStatus.PENDING
        assert not req.is_terminal
        assert not req.is_approved
        assert req.decision_count == 0

    def test_request_terminal_statuses(self):
        for status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED,
                       ApprovalStatus.CANCELLED, ApprovalStatus.EXPIRED]:
            req = ApprovalRequest(
                id="r2", tenant_id="t1",
                target_type=ApprovalTargetType.AI_ACTION,
                target_id="a1", requested_by="system",
                action_summary="Test", status=status,
            )
            assert req.is_terminal

    def test_request_to_dict(self):
        req = ApprovalRequest(
            id="r3", tenant_id="t1",
            target_type=ApprovalTargetType.NBA_RECOMMENDATION,
            target_id="nba-1", requested_by="user-1",
            action_summary="Test action",
        )
        d = req.to_dict()
        assert d["id"] == "r3"
        assert d["target_type"] == "nba_recommendation"
        assert d["status"] == "pending"
        assert "decisions" in d

    def test_request_with_decision(self):
        dec = ApprovalDecision(
            decision="approve", decided_by="mgr-1",
            comments="Looks good",
        )
        req = ApprovalRequest(
            id="r4", tenant_id="t1",
            target_type=ApprovalTargetType.NBA_RECOMMENDATION,
            target_id="nba-1", requested_by="user-1",
            action_summary="Test",
        )
        req.decisions.append(dec)
        assert req.decision_count == 1
        assert req.latest_decision.decision == "approve"


# ═══ Service tests ═══

class TestApprovalService:

    def test_create_request(self, service):
        req = _run(service.create_request(
            tenant_id="t1",
            target_type=ApprovalTargetType.NBA_RECOMMENDATION,
            target_id="nba-1",
            requested_by="user-1",
            action_summary="Schedule demo call with Acme Corp",
            action_evidence=["E1: Deal health score 0.8", "E2: Last contact 5 days ago"],
        ))
        assert req.status == ApprovalStatus.PENDING
        assert req.target_id == "nba-1"
        assert len(req.action_evidence) == 2
        assert req.required_level == ApprovalLevel.MANAGER

    def test_approve_request(self, service):
        req = _run(service.create_request(
            tenant_id="t1",
            target_type=ApprovalTargetType.NBA_RECOMMENDATION,
            target_id="nba-1",
            requested_by="user-1",
            action_summary="Schedule demo call",
        ))
        approved = _run(service.approve(
            req.id, approved_by="mgr-1",
            authority_level=ApprovalLevel.MANAGER,
            comments="Approved",
        ))
        assert approved.status == ApprovalStatus.APPROVED
        assert approved.is_approved
        assert approved.is_terminal
        assert approved.decision_count == 1
        assert approved.latest_decision.decided_by == "mgr-1"

    def test_reject_request(self, service):
        req = _run(service.create_request(
            tenant_id="t1",
            target_type=ApprovalTargetType.AI_ACTION,
            target_id="ai-1",
            requested_by="system",
            action_summary="Auto-send follow-up email",
        ))
        rejected = _run(service.reject(
            req.id, rejected_by="mgr-1",
            authority_level=ApprovalLevel.MANAGER,
            comments="Not yet",
        ))
        assert rejected.status == ApprovalStatus.REJECTED
        assert rejected.is_rejected
        assert rejected.is_terminal

    def test_escalate_request(self, service):
        req = _run(service.create_request(
            tenant_id="t1",
            target_type=ApprovalTargetType.NBA_RECOMMENDATION,
            target_id="nba-1",
            requested_by="user-1",
            action_summary="Override pricing",
            required_level=ApprovalLevel.VP,
        ))
        escalated = _run(service.escalate(req.id, escalated_by="mgr-1", comments="Need VP"))
        assert escalated.status == ApprovalStatus.ESCALATED
        assert escalated.decision_count == 1
        assert escalated.latest_decision.decision == "escalate"

    def test_cancel_request(self, service):
        req = _run(service.create_request(
            tenant_id="t1",
            target_type=ApprovalTargetType.NBA_RECOMMENDATION,
            target_id="nba-1",
            requested_by="user-1",
            action_summary="Test",
        ))
        cancelled = _run(service.cancel(req.id))
        assert cancelled.status == ApprovalStatus.CANCELLED
        assert cancelled.is_terminal

    def test_cannot_approve_terminal_request(self, service):
        req = _run(service.create_request(
            tenant_id="t1",
            target_type=ApprovalTargetType.NBA_RECOMMENDATION,
            target_id="nba-1",
            requested_by="user-1",
            action_summary="Test",
        ))
        _run(service.approve(req.id, approved_by="mgr-1", authority_level=ApprovalLevel.MANAGER))
        with pytest.raises(ValueError, match="Cannot approve"):
            _run(service.approve(req.id, approved_by="mgr-1", authority_level=ApprovalLevel.MANAGER))

    def test_insufficient_authority_rejected(self, service):
        req = _run(service.create_request(
            tenant_id="t1",
            target_type=ApprovalTargetType.NBA_RECOMMENDATION,
            target_id="nba-1",
            requested_by="user-1",
            action_summary="High-value deal action",
            required_level=ApprovalLevel.VP,
        ))
        with pytest.raises(PermissionError, match="Insufficient authority"):
            _run(service.approve(
                req.id, approved_by="mgr-1",
                authority_level=ApprovalLevel.MANAGER,
            ))

    def test_vp_can_approve_manager_level(self, service):
        req = _run(service.create_request(
            tenant_id="t1",
            target_type=ApprovalTargetType.NBA_RECOMMENDATION,
            target_id="nba-1",
            requested_by="user-1",
            action_summary="Test",
            required_level=ApprovalLevel.MANAGER,
        ))
        approved = _run(service.approve(
            req.id, approved_by="vp-1",
            authority_level=ApprovalLevel.VP,
        ))
        assert approved.status == ApprovalStatus.APPROVED

    def test_check_expiration(self, service):
        req = _run(service.create_request(
            tenant_id="t1",
            target_type=ApprovalTargetType.NBA_RECOMMENDATION,
            target_id="nba-1",
            requested_by="user-1",
            action_summary="Test",
            ttl_hours=-1,  # already expired
        ))
        expired = _run(service.check_expiration(req.id))
        assert expired is not None
        assert expired.status == ApprovalStatus.EXPIRED

    def test_check_no_expiration(self, service):
        req = _run(service.create_request(
            tenant_id="t1",
            target_type=ApprovalTargetType.NBA_RECOMMENDATION,
            target_id="nba-1",
            requested_by="user-1",
            action_summary="Test",
            ttl_hours=48,
        ))
        result = _run(service.check_expiration(req.id))
        assert result is None

    def test_list_pending(self, service):
        _run(service.create_request(
            tenant_id="t1", target_type=ApprovalTargetType.NBA_RECOMMENDATION,
            target_id="nba-1", requested_by="u1", action_summary="A",
        ))
        _run(service.create_request(
            tenant_id="t1", target_type=ApprovalTargetType.NBA_RECOMMENDATION,
            target_id="nba-2", requested_by="u1", action_summary="B",
        ))
        pending = _run(service.list_pending("t1"))
        assert len(pending) == 2

    def test_list_pending_with_assignment(self, service):
        _run(service.create_request(
            tenant_id="t1", target_type=ApprovalTargetType.NBA_RECOMMENDATION,
            target_id="nba-1", requested_by="u1", action_summary="A",
            assigned_to="mgr-1",
        ))
        _run(service.create_request(
            tenant_id="t1", target_type=ApprovalTargetType.NBA_RECOMMENDATION,
            target_id="nba-2", requested_by="u1", action_summary="B",
            assigned_to="mgr-2",
        ))
        pending_m1 = _run(service.list_pending("t1", assigned_to="mgr-1"))
        assert len(pending_m1) == 1
        assert pending_m1[0].assigned_to == "mgr-1"

    def test_kpis(self, service):
        _run(service.create_request(
            tenant_id="t1", target_type=ApprovalTargetType.NBA_RECOMMENDATION,
            target_id="nba-1", requested_by="u1", action_summary="A",
        ))
        req2 = _run(service.create_request(
            tenant_id="t1", target_type=ApprovalTargetType.AI_ACTION,
            target_id="ai-1", requested_by="system", action_summary="B",
        ))
        _run(service.approve(req2.id, approved_by="mgr-1", authority_level=ApprovalLevel.MANAGER))
        kpis = _run(service.kpis("t1"))
        assert kpis["total"] == 2
        assert kpis["pending"] == 1
        assert kpis["approved"] == 1

    def test_nonexistent_request(self, service):
        with pytest.raises(ValueError, match="not found"):
            _run(service.approve("fake-id", approved_by="mgr-1", authority_level=ApprovalLevel.MANAGER))
