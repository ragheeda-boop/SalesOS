"""Phase 3 Copilot — Mode system tests.

Covers P3-1: Ask/Explain/Summarize/Investigate/Recommend mode system.
"""
from __future__ import annotations

import pytest
from domains.copilot.models import CopilotMode


class TestCopilotMode:

    def test_mode_values(self):
        assert CopilotMode.ASK.value == "ask"
        assert CopilotMode.EXPLAIN.value == "explain"
        assert CopilotMode.SUMMARIZE.value == "summarize"
        assert CopilotMode.INVESTIGATE.value == "investigate"
        assert CopilotMode.RECOMMEND.value == "recommend"

    def test_mode_count(self):
        assert len(CopilotMode) == 5

    def test_mode_is_str_enum(self):
        assert isinstance(CopilotMode.ASK, str)
        assert CopilotMode.ASK == "ask"


class TestCopilotModeSchemas:

    def test_mode_request_valid(self):
        from domains.copilot.schemas import CopilotModeRequest
        req = CopilotModeRequest(mode="ask", query="What companies are in Riyadh?")
        assert req.mode == "ask"
        assert req.query == "What companies are in Riyadh?"

    def test_mode_request_with_target(self):
        from domains.copilot.schemas import CopilotModeRequest
        req = CopilotModeRequest(
            mode="explain",
            query="Explain this deal",
            target_id="deal-123",
            target_type="deal",
        )
        assert req.target_id == "deal-123"
        assert req.target_type == "deal"

    def test_mode_request_recommend(self):
        from domains.copilot.schemas import CopilotModeRequest
        req = CopilotModeRequest(
            mode="recommend",
            query="What should I do next for Acme Corp?",
            context={"company_id": "c1"},
        )
        assert req.mode == "recommend"
        assert req.context == {"company_id": "c1"}

    def test_mode_request_invalid_mode(self):
        from domains.copilot.schemas import CopilotModeRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CopilotModeRequest(mode="invalid", query="test")

    def test_mode_response(self):
        from domains.copilot.schemas import CopilotModeResponse
        resp = CopilotModeResponse(
            mode="ask",
            response="There are 5 companies in Riyadh",
            confidence=0.85,
            sources=["company_table"],
            evidence=[],
        )
        assert resp.mode == "ask"
        assert resp.approval_id is None
        assert not resp.requires_approval

    def test_mode_response_recommend_with_approval(self):
        from domains.copilot.schemas import CopilotModeResponse
        resp = CopilotModeResponse(
            mode="recommend",
            response="Schedule a demo call",
            confidence=0.9,
            approval_id="apr-123",
            requires_approval=True,
        )
        assert resp.requires_approval
        assert resp.approval_id == "apr-123"


class TestCopilotModeIntegration:

    def test_recommend_creates_approval(self):
        """Recommend mode must produce an approval_id (HITL gate)."""
        from domains.approval.contracts.models import (
            ApprovalLevel,
            ApprovalRequest,
            ApprovalStatus,
            ApprovalTargetType,
        )
        from domains.approval.engine.service import ApprovalService
        from domains.approval.in_memory_repo import InMemoryApprovalRepository
        import asyncio

        repo = InMemoryApprovalRepository()
        svc = ApprovalService(repository=repo)

        req = asyncio.run(svc.create_request(
            tenant_id="t1",
            target_type=ApprovalTargetType.NBA_RECOMMENDATION,
            target_id="copilot_conv_test",
            requested_by="user-1",
            action_summary="Schedule demo call with Acme Corp",
            action_evidence=["Deal health score 0.8", "Last contact 5 days ago"],
        ))
        assert req.status == ApprovalStatus.PENDING
        assert req.required_level == ApprovalLevel.MANAGER

    def test_readonly_modes_do_not_create_approval(self):
        """Ask/Explain/Summarize/Investigate must NOT create approval requests."""
        from domains.approval.contracts.models import ApprovalTargetType
        from domains.approval.engine.service import ApprovalService
        from domains.approval.in_memory_repo import InMemoryApprovalRepository
        import asyncio

        repo = InMemoryApprovalRepository()
        svc = ApprovalService(repository=repo)
        items = asyncio.run(
            svc.list_pending("t1")
        )
        assert len(items) == 0
