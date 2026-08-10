"""IL-2A: Signal → AgentTask Trigger.

Maps intelligence decisions/recommendations to durable AgentRuntime tasks.
Uses schedule_task() for idempotent creation with bounded lease windows.

Design:
  - SignalTaskMapper: signal_type → task_kind mapping
  - trigger_tasks(): batch-creates tasks from decision records
  - Idempotency: {tenant_id}:decision:{entity_type}:{entity_id}:{task_kind}
  - Does NOT replace or redesign AgentRuntime — uses existing schedule_task() API
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ── Signal → Task Kind Mapping ─────────────────────────────────────

SIGNAL_TO_TASK_KIND: dict[str, str] = {
    "funding": "research_company",
    "hiring": "research_company",
    "expansion": "investigate_expansion",
    "contract": "research_company",
    "project": "research_company",
    "tender": "research_company",
    "merger": "research_company",
    "partnership": "research_company",
    "leadership": "executive_change",
    "competitor": "assess_icp",
    "regulatory": "verify_license",
    "news": "research_company",
}

DEFAULT_TASK_KIND = "research_company"


class SignalTaskMapper:
    """Maps signal/decision types to durable AgentTask kinds."""

    @staticmethod
    def task_kind_for_signal(signal_category: str) -> str:
        key = (signal_category or "").lower()
        return SIGNAL_TO_TASK_KIND.get(key, DEFAULT_TASK_KIND)

    @staticmethod
    def task_kind_for_decision(decision_category: str) -> str:
        """Maps DecisionCategory → task kind."""
        mapping = {
            "opportunity": "research_company",
            "revenue": "research_company",
            "risk": "verify_license",
            "resource": "assess_icp",
            "strategy": "investigate_expansion",
        }
        return mapping.get((decision_category or "").lower(), DEFAULT_TASK_KIND)

    @staticmethod
    def build_idempotency_key(
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        task_kind: str,
    ) -> str:
        return f"{tenant_id}:decision:{entity_type}:{entity_id}:{task_kind}"

    @staticmethod
    def priority_for_signal_intensity(intensity: float) -> int:
        if intensity >= 0.9:
            return 10
        if intensity >= 0.7:
            return 5
        return 0


async def trigger_tasks_from_decisions(
    session: AsyncSession,
    decisions: list[dict[str, Any]],
    tenant_id: str,
) -> dict[str, Any]:
    """Create AgentRuntime tasks from intelligence decisions.

    Args:
        session: Active DB session
        decisions: List of decision dicts with keys:
            category, entity_type, entity_id, intensity, title, confidence
        tenant_id: Tenant scope

    Returns:
        Dict with stats: created, skipped, errors
    """
    stats: dict[str, int] = {"created": 0, "skipped": 0, "errors": 0}

    from runtime.agent_runtime.queue import schedule_task  # lazy to avoid DB init at import

    for dec in decisions:
        try:
            category = dec.get("category", "")
            entity_type = dec.get("entity_type", "company")
            entity_id = dec.get("entity_id", "")
            intensity = float(dec.get("intensity", 0.5))
            confidence = float(dec.get("confidence", 0.5))

            if not entity_id:
                stats["skipped"] += 1
                continue

            task_kind = SignalTaskMapper.task_kind_for_decision(category)
            priority = SignalTaskMapper.priority_for_signal_intensity(intensity)
            idem_key = SignalTaskMapper.build_idempotency_key(
                tenant_id, entity_type, entity_id, task_kind,
            )

            due_at = datetime.now(timezone.utc) + timedelta(seconds=5)
            reason = dec.get("title", f"Decision: {category}")[:200]

            await schedule_task(
                session=session,
                tenant_id=tenant_id,
                kind=task_kind,
                reason=reason,
                entity_type=entity_type,
                entity_id=entity_id,
                due_at=due_at,
                priority=priority,
                budget=4,
                idempotency_key=idem_key,
            )
            stats["created"] += 1

            logger.info(
                "AgentTask triggered: kind=%s entity=%s/%s tenant=%s priority=%d",
                task_kind, entity_type, entity_id, tenant_id, priority,
            )

        except Exception:
            stats["errors"] += 1
            logger.exception(
                "Failed to create AgentTask for decision: %s",
                dec.get("title", "unknown"),
            )

    return stats


async def trigger_tasks_from_signals(
    session: AsyncSession,
    signals: list[dict[str, Any]],
    tenant_id: str,
) -> dict[str, Any]:
    """Create AgentRuntime tasks directly from signal data.

    Args:
        session: Active DB session
        signals: List of signal dicts with keys:
            signal_type, company_id, tenant_id, intensity, title
        tenant_id: Tenant scope (overrides per-signal tenant_id if provided)

    Returns:
        Dict with stats
    """
    stats: dict[str, int] = {"created": 0, "skipped": 0, "errors": 0}

    from runtime.agent_runtime.queue import schedule_task  # lazy to avoid DB init at import

    for sig in signals:
        try:
            signal_type = sig.get("signal_type", "news")
            entity_type = "company"
            entity_id = sig.get("company_id", "")
            intensity = float(sig.get("intensity", 0.5))
            sig_tenant = sig.get("tenant_id", tenant_id)

            if not entity_id:
                stats["skipped"] += 1
                continue

            task_kind = SignalTaskMapper.task_kind_for_signal(signal_type)
            priority = SignalTaskMapper.priority_for_signal_intensity(intensity)
            idem_key = SignalTaskMapper.build_idempotency_key(
                sig_tenant, entity_type, entity_id, task_kind,
            )

            due_at = datetime.now(timezone.utc) + timedelta(seconds=5)
            reason = sig.get("title", f"Signal: {signal_type}")[:200]

            await schedule_task(
                session=session,
                tenant_id=sig_tenant,
                kind=task_kind,
                reason=reason,
                entity_type=entity_type,
                entity_id=entity_id,
                due_at=due_at,
                priority=priority,
                budget=4,
                idempotency_key=idem_key,
            )
            stats["created"] += 1

        except Exception:
            stats["errors"] += 1
            logger.exception(
                "Failed to create AgentTask for signal: %s",
                sig.get("title", "unknown"),
            )

    return stats
