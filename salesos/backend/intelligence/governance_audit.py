"""AI Governance Audit — persistent audit trail for AI policy enforcement and HITL decisions.

P3-4: Extends AIAuditService with:
- Policy enforcement logging (block/deny/warn)
- HITL approval audit trail (approve/reject/escalate)
- Governance event aggregation for dashboards
"""

from __future__ import annotations

from typing import Any

from app.modules.audit.ai_audit_service import AIAuditService


# ── AI Governance action constants ────────────────────────────────

POLICY_ACTIONS = {
    "blocked": "ai:policy:blocked",
    "denied": "ai:policy:denied",
    "warned": "ai:policy:warned",
    "allowed": "ai:policy:allowed",
}

HITL_ACTIONS = {
    "requested": "ai:hitl:requested",
    "approved": "ai:hitl:approved",
    "rejected": "ai:hitl:rejected",
    "escalated": "ai:hitl:escalated",
    "expired": "ai:hitl:expired",
    "cancelled": "ai:hitl:cancelled",
}

RESOURCE_TYPES = {
    "policy": "ai:governance/policy",
    "approval": "ai:governance/approval",
    "guardrail": "ai:governance/guardrail",
    "pii_scrub": "ai:governance/pii",
}


class AIGovernanceAudit:
    """P3-4: Persistent audit trail for AI governance events."""

    def __init__(self, audit_service: AIAuditService):
        self._audit = audit_service

    async def log_policy_enforcement(
        self,
        tenant_id: str,
        user_id: str | None,
        policy_name: str,
        action: str,  # blocked / denied / warned / allowed
        resource_type: str,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        await self._audit.log_ai_call(
            tenant_id=tenant_id,
            user_id=user_id,
            action=POLICY_ACTIONS.get(action, f"ai:policy:{action}"),
            resource_type=RESOURCE_TYPES.get(resource_type, f"ai:governance/{resource_type}"),
            entity_id=resource_id,
            metadata={
                "policy_name": policy_name,
                "enforcement_action": action,
                **(details or {}),
            },
            request_id=request_id,
        )

    async def log_hitl_decision(
        self,
        tenant_id: str,
        user_id: str,
        approval_id: str,
        decision: str,  # approved / rejected / escalated
        target_type: str,
        target_id: str,
        authority_level: str = "",
        comments: str = "",
        details: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        await self._audit.log_ai_call(
            tenant_id=tenant_id,
            user_id=user_id,
            action=HITL_ACTIONS.get(decision, f"ai:hitl:{decision}"),
            resource_type=RESOURCE_TYPES["approval"],
            entity_id=approval_id,
            metadata={
                "decision": decision,
                "target_type": target_type,
                "target_id": target_id,
                "authority_level": authority_level,
                "comments": comments,
                **(details or {}),
            },
            request_id=request_id,
        )

    async def log_pii_enforcement(
        self,
        tenant_id: str,
        user_id: str | None,
        action: str,  # blocked / scrubbed
        redaction_count: int = 0,
        text_length: int = 0,
        details: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        await self._audit.log_ai_call(
            tenant_id=tenant_id,
            user_id=user_id,
            action=f"ai:pii:{action}",
            resource_type=RESOURCE_TYPES["pii_scrub"],
            metadata={
                "action": action,
                "redaction_count": redaction_count,
                "text_length": text_length,
                **(details or {}),
            },
            request_id=request_id,
        )
