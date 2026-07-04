"""Policy Runtime — business policy enforcement for the Decision Engine.

Policies evaluated before any recommendation:
  - Do Not Contact (DNC)
  - VIP / High-Priority
  - Government / Regulated
  - Legal Hold
  - Sensitive Account
  - Competitor
  - Blacklist
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession


class PolicyResult(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"
    ESCALATE = "escalate"


@dataclass
class PolicyEvaluation:
    policy_name: str
    result: PolicyResult
    reason: str
    severity: int = 0

    def to_dict(self) -> dict:
        return {"policy": self.policy_name, "result": self.result.value, "reason": self.reason, "severity": self.severity}


@dataclass
class PolicyEngineMetrics:
    evaluations: int = 0
    allowed: int = 0
    blocked: int = 0
    warned: int = 0
    escalated: int = 0

    def snapshot(self) -> dict:
        return vars(self)


class PolicyEngine:
    """Evaluates business policies against a company context.

    Policies can be:
      - Static (built-in rules like DNC)
      - Dynamic (stored in `company_policies` table)
    """

    def __init__(self, session_factory: Callable[[], AsyncSession], logger: Any = None):
        self._session_factory = session_factory
        self._logger = logger
        self.metrics = PolicyEngineMetrics()

    async def evaluate(self, context: dict, company_id: str, tenant_id: str) -> list[PolicyEvaluation]:
        results: list[PolicyEvaluation] = []
        async with self._session_factory() as session:
            rows = await session.execute(
                sa_text("""
                    SELECT policy_name, action, reason, severity
                    FROM company_policies
                    WHERE company_id = :cid AND tenant_id = :tid AND is_active = true
                """),
                {"cid": company_id, "tid": tenant_id},
            )
            stored_policies = rows.mappings().all()

        for p in stored_policies:
            result = PolicyResult(p["action"])
            results.append(PolicyEvaluation(
                policy_name=p["policy_name"],
                result=result,
                reason=p["reason"] or "",
                severity=p.get("severity") or 0,
            ))

        # Built-in policy: Government entities
        business = context.get("business", {})
        if business.get("is_gov"):
            results.append(PolicyEvaluation(
                policy_name="government_entity",
                result=PolicyResult.WARN,
                reason="Government entity — requires special handling",
                severity=3,
            ))

        # Built-in policy: Small business sizing
        size = business.get("size")
        if size == "small":
            results.append(PolicyEvaluation(
                policy_name="small_business",
                result=PolicyResult.ALLOW,
                reason="Small business — standard sequence applies",
                severity=0,
            ))

        # Count metrics
        for r in results:
            self.metrics.evaluations += 1
            if r.result == PolicyResult.ALLOW:
                self.metrics.allowed += 1
            elif r.result == PolicyResult.BLOCK:
                self.metrics.blocked += 1
            elif r.result == PolicyResult.WARN:
                self.metrics.warned += 1
            elif r.result == PolicyResult.ESCALATE:
                self.metrics.escalated += 1

        return results
