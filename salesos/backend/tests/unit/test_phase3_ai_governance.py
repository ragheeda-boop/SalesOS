"""Phase 3 AI Governance — Audit trail tests.

Covers P3-4: Persistent audit trail for AI policy enforcement and HITL decisions.
"""
from __future__ import annotations

import asyncio
import pytest

from app.modules.audit.ai_audit_service import AIAuditService
from app.modules.audit.service import AuditService, InMemoryAuditRepository
from intelligence.governance_audit import (
    AIGovernanceAudit,
    HITL_ACTIONS,
    POLICY_ACTIONS,
    RESOURCE_TYPES,
)


@pytest.fixture
def audit_repo():
    return InMemoryAuditRepository()


@pytest.fixture
def audit_service(audit_repo):
    return AuditService(repository=audit_repo)


@pytest.fixture
def ai_audit(audit_service):
    return AIAuditService(audit_service)


@pytest.fixture
def gov_audit(ai_audit):
    return AIGovernanceAudit(ai_audit)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ═══ Constants tests ═══

class TestGovernanceConstants:

    def test_policy_actions(self):
        assert POLICY_ACTIONS["blocked"] == "ai:policy:blocked"
        assert POLICY_ACTIONS["denied"] == "ai:policy:denied"
        assert POLICY_ACTIONS["warned"] == "ai:policy:warned"
        assert POLICY_ACTIONS["allowed"] == "ai:policy:allowed"

    def test_hitl_actions(self):
        assert HITL_ACTIONS["approved"] == "ai:hitl:approved"
        assert HITL_ACTIONS["rejected"] == "ai:hitl:rejected"
        assert HITL_ACTIONS["escalated"] == "ai:hitl:escalated"
        assert HITL_ACTIONS["expired"] == "ai:hitl:expired"

    def test_resource_types(self):
        assert RESOURCE_TYPES["policy"] == "ai:governance/policy"
        assert RESOURCE_TYPES["approval"] == "ai:governance/approval"
        assert RESOURCE_TYPES["guardrail"] == "ai:governance/guardrail"


# ═══ Policy enforcement audit tests ═══

class TestPolicyEnforcementAudit:

    def test_log_policy_blocked(self, gov_audit, audit_repo):
        _run(gov_audit.log_policy_enforcement(
            tenant_id="t1",
            user_id="user-1",
            policy_name="PII_SCRUB",
            action="blocked",
            resource_type="guardrail",
            details={"reason": "PII detected in RAG query"},
        ))
        entries, total = _run(audit_repo.query("t1"))
        assert total == 1
        assert entries[0].action == "ai:policy:blocked"
        assert entries[0].resource_type == "ai:governance/guardrail"
        assert entries[0].details["metadata"]["policy_name"] == "PII_SCRUB"

    def test_log_policy_denied(self, gov_audit, audit_repo):
        _run(gov_audit.log_policy_enforcement(
            tenant_id="t1",
            user_id="user-1",
            policy_name="MODEL_TIER",
            action="denied",
            resource_type="policy",
            resource_id="policy-1",
        ))
        entries, total = _run(audit_repo.query("t1"))
        assert total == 1
        assert entries[0].action == "ai:policy:denied"
        assert entries[0].resource_id == "policy-1"


# ═══ HITL approval audit tests ═══

class TestHITAudit:

    def test_log_hitl_approved(self, gov_audit, audit_repo):
        _run(gov_audit.log_hitl_decision(
            tenant_id="t1",
            user_id="mgr-1",
            approval_id="apr-123",
            decision="approved",
            target_type="nba_recommendation",
            target_id="nba-1",
            authority_level="manager",
            comments="Looks good",
        ))
        entries, total = _run(audit_repo.query("t1"))
        assert total == 1
        assert entries[0].action == "ai:hitl:approved"
        assert entries[0].resource_type == "ai:governance/approval"
        assert entries[0].resource_id == "apr-123"
        assert entries[0].details["metadata"]["authority_level"] == "manager"

    def test_log_hitl_rejected(self, gov_audit, audit_repo):
        _run(gov_audit.log_hitl_decision(
            tenant_id="t1",
            user_id="mgr-1",
            approval_id="apr-456",
            decision="rejected",
            target_type="ai_action",
            target_id="ai-1",
            comments="Not yet",
        ))
        entries, total = _run(audit_repo.query("t1"))
        assert total == 1
        assert entries[0].action == "ai:hitl:rejected"
        assert entries[0].details["metadata"]["comments"] == "Not yet"

    def test_log_hitl_escalated(self, gov_audit, audit_repo):
        _run(gov_audit.log_hitl_decision(
            tenant_id="t1",
            user_id="mgr-1",
            approval_id="apr-789",
            decision="escalated",
            target_type="nba_recommendation",
            target_id="nba-1",
        ))
        entries, total = _run(audit_repo.query("t1"))
        assert entries[0].action == "ai:hitl:escalated"


# ═══ PII enforcement audit tests ═══

class TestPIIAudit:

    def test_log_pii_scrubbed(self, gov_audit, audit_repo):
        _run(gov_audit.log_pii_enforcement(
            tenant_id="t1",
            user_id="user-1",
            action="scrubbed",
            redaction_count=3,
            text_length=500,
        ))
        entries, total = _run(audit_repo.query("t1"))
        assert total == 1
        assert entries[0].action == "ai:pii:scrubbed"
        assert entries[0].details["metadata"]["redaction_count"] == 3

    def test_log_pii_blocked(self, gov_audit, audit_repo):
        _run(gov_audit.log_pii_enforcement(
            tenant_id="t1",
            user_id="user-1",
            action="blocked",
            redaction_count=0,
        ))
        entries, total = _run(audit_repo.query("t1"))
        assert entries[0].action == "ai:pii:blocked"


# ═══ Audit query tests ═══

class TestAuditQuery:

    def test_query_by_action(self, gov_audit, audit_repo):
        _run(gov_audit.log_policy_enforcement(
            tenant_id="t1", user_id="u1", policy_name="P1",
            action="blocked", resource_type="guardrail",
        ))
        _run(gov_audit.log_hitl_decision(
            tenant_id="t1", user_id="mgr-1", approval_id="a1",
            decision="approved", target_type="nba_recommendation", target_id="n1",
        ))
        entries, total = _run(audit_repo.query("t1", {"action": "ai:policy:blocked"}))
        assert total == 1
        assert entries[0].details["metadata"]["policy_name"] == "P1"

    def test_query_by_resource_type(self, gov_audit, audit_repo):
        _run(gov_audit.log_policy_enforcement(
            tenant_id="t1", user_id="u1", policy_name="P1",
            action="blocked", resource_type="guardrail",
        ))
        _run(gov_audit.log_hitl_decision(
            tenant_id="t1", user_id="mgr-1", approval_id="a1",
            decision="approved", target_type="nba_recommendation", target_id="n1",
        ))
        entries, total = _run(audit_repo.query("t1", {"resource_type": "ai:governance/approval"}))
        assert total == 1
        assert entries[0].action == "ai:hitl:approved"

    def test_audit_stats(self, gov_audit, audit_repo):
        _run(gov_audit.log_policy_enforcement(
            tenant_id="t1", user_id="u1", policy_name="P1",
            action="blocked", resource_type="guardrail",
        ))
        _run(gov_audit.log_hitl_decision(
            tenant_id="t1", user_id="mgr-1", approval_id="a1",
            decision="approved", target_type="nba_recommendation", target_id="n1",
        ))
        _run(gov_audit.log_hitl_decision(
            tenant_id="t1", user_id="mgr-1", approval_id="a2",
            decision="rejected", target_type="ai_action", target_id="ai-1",
        ))
        stats = _run(audit_repo.stats("t1"))
        assert stats["total_events"] == 3
        assert len(stats["top_actions"]) == 3
