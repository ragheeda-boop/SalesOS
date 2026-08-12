"""IL-2A: Signal → AgentTask Trigger.

Maps intelligence decisions/recommendations to durable AgentRuntime tasks.
Uses schedule_task() for idempotent creation with bounded lease windows.

Design:
  - SignalTaskMapper: signal_type → task_kind mapping
  - trigger_tasks(): batch-creates tasks from decision records
  - Idempotency: {tenant_id}:decision:{entity_type}:{entity_id}:{task_kind}
  - Does NOT replace or redesign AgentRuntime — uses existing schedule_task() API

IL-2A Decision → AgentTask contract:
  - Eligibility and task-kind mapping are SEPARATE decisions.
  - should_create_agent_task(): only DecisionTypes with a defined execution
    contract (recommend_* → research_company, the sole kind with a real
    ResearchAgent handler) are task-generating.
  - alert / task_suggested / workflow_suggested / crm_update are intelligence
    or metadata outputs, NOT research requests — no AgentTask (fail-closed).
  - Unknown DecisionTypes are fail-closed (no task).
  - decision.created handler loads the canonical Decision via get_decision();
    event payload is routing only (decision_id / tenant_id).
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Bound decision.created → AgentTask so idle-DB checkout cannot hang fan-out.
_IL2A_HANDLER_TIMEOUT_SECONDS = 8.0

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

# IL-2A: DecisionType → task kind contract. Single source of truth for BOTH
# eligibility and mapping. Only types present here generate AgentTasks.
DECISION_TYPE_TO_TASK_KIND: dict[str, str] = {
    "recommend_demo": "research_company",
    "recommend_call": "research_company",
    "recommend_proposal": "research_company",
    "recommend_sequence": "research_company",
    "recommend_outreach": "research_company",
    "recommend_campaign": "research_company",
    "recommend_escalate": "research_company",
}

# Documented non-task-generating DecisionTypes (intelligence/metadata outputs,
# not research requests). Eligibility is decided by DECISION_TYPE_TO_TASK_KIND
# membership — NOT by absence from this set.
NON_TASK_GENERATING_DECISION_TYPES: frozenset[str] = frozenset({
    "alert", "task_suggested", "workflow_suggested", "crm_update",
})


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

    @staticmethod
    def should_create_agent_task(decision_type: str) -> bool:
        """Return True only for DecisionTypes with a defined AgentTask contract.

        Fail-closed: unknown types are not task-generating. The mapping dict
        is the single eligibility source — non-actionable types
        (alert, task_suggested, workflow_suggested, crm_update) are simply
        absent from it.
        """
        return (decision_type or "").lower() in DECISION_TYPE_TO_TASK_KIND

    @staticmethod
    def task_kind_for_decision_type(decision_type: str) -> str | None:
        """Map an actionable DecisionType → task kind. None when no contract."""
        return DECISION_TYPE_TO_TASK_KIND.get((decision_type or "").lower())


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

    from sqlalchemy.exc import IntegrityError
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

            task_kind = dec.get("task_kind") or SignalTaskMapper.task_kind_for_decision(category)
            priority = SignalTaskMapper.priority_for_signal_intensity(intensity)
            idem_key = SignalTaskMapper.build_idempotency_key(
                tenant_id, entity_type, entity_id, task_kind,
            )

            due_at = datetime.now(timezone.utc) + timedelta(seconds=5)
            reason = dec.get("title", f"Decision: {category}")[:200]

            task = await schedule_task(
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
            # Finished row returned via idempotency_key → skip (not a new task).
            if task is not None and getattr(task, "finished_at", None) is not None:
                stats["skipped"] += 1
                logger.info(
                    "AgentTask idempotent skip: kind=%s entity=%s/%s tenant=%s",
                    task_kind, entity_type, entity_id, tenant_id,
                )
            else:
                stats["created"] += 1
                logger.info(
                    "AgentTask triggered: kind=%s entity=%s/%s tenant=%s priority=%d",
                    task_kind, entity_type, entity_id, tenant_id, priority,
                )

        except IntegrityError:
            # Defensive: schedule_task should absorb UniqueViolation; if not, skip.
            stats["skipped"] += 1
            logger.info(
                "AgentTask idempotent UniqueViolation skip: %s",
                dec.get("title", "unknown"),
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

    from sqlalchemy.exc import IntegrityError
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

            task = await schedule_task(
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
            if task is not None and getattr(task, "finished_at", None) is not None:
                stats["skipped"] += 1
            else:
                stats["created"] += 1

        except IntegrityError:
            stats["skipped"] += 1
            logger.info(
                "AgentTask idempotent UniqueViolation skip (signal): %s",
                sig.get("title", "unknown"),
            )
        except Exception:
            stats["errors"] += 1
            logger.exception(
                "Failed to create AgentTask for signal: %s",
                sig.get("title", "unknown"),
            )

    return stats


async def on_decision_created_event(
    session_factory,
    event: Any,
    decision_engine: Any = None,
) -> dict:
    """Handle a ``decision.created`` event → create one AgentTask.

    Flow (canonical-first — event payload is routing only):
      event.tenant_id + decision_id
        → set_current_tenant_id()
        → apply_tenant_guc(session)
        → get_decision(decision_id)
        → eligibility (should_create_agent_task)
        → task_kind_for_decision_type
        → trigger_tasks_from_decisions
        → commit
        → finally: reset_current_tenant_id

    Eligibility and mapping are SEPARATE. Non-actionable DecisionTypes
    (alert, task_suggested, …) return reason ``not_task_generating`` and
    create no AgentTask.

    Args:
        session_factory: AsyncSession factory (e.g. app.database.async_session)
        event: DomainEvent with event_type='decision.created' and data carrying
            at least ``decision_id``. ``decision_type`` / ``company_id`` on the
            event are NOT used for eligibility or entity binding.
        decision_engine: DecisionEngine with get_decision(decision_id, tenant_id).
            Required — without a canonical Decision we fail closed.

    Returns:
        Stats dict plus ``task_kind`` and a ``reason`` for non-creating paths.
    """
    event_type = getattr(event, "event_type", "")
    tenant_id = getattr(event, "tenant_id", "")
    data = getattr(event, "data", {}) or {}

    if event_type != "decision.created" or not tenant_id:
        return {"created": 0, "skipped": 0, "errors": 0, "reason": "not_decision_created"}

    decision_id = data.get("decision_id", "")
    if not decision_id:
        return {"created": 0, "skipped": 0, "errors": 0, "reason": "no_decision_id"}

    if decision_engine is None:
        return {"created": 0, "skipped": 0, "errors": 0, "reason": "no_decision_engine"}

    from app.database import (
        apply_tenant_guc,
        reset_current_tenant_id,
        set_current_tenant_id,
    )

    token = set_current_tenant_id(tenant_id)
    t0 = time.monotonic()
    # Idle-DB / PgBouncer can sit 5–10s with checked_out=0; bound the whole
    # handler so fan-out cannot stack on evaluate's background publish.
    logger.info(
        "IL-2A on_decision_created enter",
        extra={
            "decision_id": decision_id,
            "tenant_id": tenant_id,
            "event_type": event_type,
            "step": "enter",
        },
    )

    async def _handle() -> dict:
        async with session_factory() as session:
            await apply_tenant_guc(session, tenant_id)
            logger.info(
                "IL-2A on_decision_created step",
                extra={
                    "decision_id": decision_id,
                    "step": "tenant_guc",
                    "elapsed_ms": round((time.monotonic() - t0) * 1000, 1),
                },
            )

            decision = decision_engine.get_decision(decision_id, tenant_id)
            if not decision:
                logger.info(
                    "IL-2A on_decision_created",
                    extra={
                        "decision_id": decision_id,
                        "step": "decision_not_found",
                        "reason": "decision_not_found",
                    },
                )
                return {
                    "created": 0, "skipped": 0, "errors": 0,
                    "reason": "decision_not_found",
                }

            decision_type = (decision.get("decision_type") or "").lower()
            company_id = decision.get("company_id") or ""
            if not company_id:
                return {"created": 0, "skipped": 0, "errors": 0, "reason": "no_company_id"}

            if not SignalTaskMapper.should_create_agent_task(decision_type):
                logger.info(
                    "IL-2A skip",
                    extra={
                        "decision_id": decision_id,
                        "decision_type": decision_type,
                        "step": "skip",
                        "reason": "not_task_generating",
                    },
                )
                return {
                    "created": 0, "skipped": 0, "errors": 0,
                    "reason": "not_task_generating",
                    "decision_type": decision_type,
                }

            task_kind = SignalTaskMapper.task_kind_for_decision_type(decision_type)
            confidence = float(decision.get("confidence") or 0.5)
            priority = int(decision.get("priority") or 0)
            reasoning = str(
                decision.get("reasoning") or f"Decision {decision_type}"
            )[:200]
            intensity = min(max(priority / 100.0, 0.0), 1.0)

            logger.info(
                "IL-2A on_decision_created step",
                extra={
                    "decision_id": decision_id,
                    "step": "schedule_begin",
                    "task_kind": task_kind,
                    "elapsed_ms": round((time.monotonic() - t0) * 1000, 1),
                },
            )
            stats = await trigger_tasks_from_decisions(
                session,
                [{
                    "category": decision_type,
                    "task_kind": task_kind,
                    "entity_type": "company",
                    "entity_id": company_id,
                    "intensity": intensity,
                    "confidence": confidence,
                    "title": reasoning,
                }],
                tenant_id,
            )
            await session.commit()
            # Do not put "created" in LogRecord extra — it is a reserved attribute
            # (KeyError on UniqueViolation/idempotent residual path after stats return).
            if stats.get("created", 0):
                outcome_reason = "created"
            elif stats.get("skipped", 0):
                outcome_reason = "skipped"
            elif stats.get("errors", 0):
                outcome_reason = "error"
            else:
                outcome_reason = "noop"
            if stats.get("errors", 0):
                try:
                    from app.metrics.collector import collector

                    collector.track_agent_dispatch_error("il2a_schedule_error")
                except Exception:
                    pass
            logger.info(
                "IL-2A on_decision_created done",
                extra={
                    "decision_id": decision_id,
                    "step": "done",
                    "reason": outcome_reason,
                    "tasks_created": stats.get("created", 0),
                    "tasks_skipped": stats.get("skipped", 0),
                    "tasks_errors": stats.get("errors", 0),
                    "elapsed_ms": round((time.monotonic() - t0) * 1000, 1),
                },
            )
            return {
                **stats,
                "task_kind": task_kind,
                "decision_type": decision_type,
                "reason": outcome_reason,
            }

    try:
        return await asyncio.wait_for(_handle(), timeout=_IL2A_HANDLER_TIMEOUT_SECONDS)
    except TimeoutError:
        logger.warning(
            "IL-2A on_decision_created handler_timeout",
            extra={
                "decision_id": decision_id,
                "step": "handler_timeout",
                "timeout_s": _IL2A_HANDLER_TIMEOUT_SECONDS,
                "elapsed_ms": round((time.monotonic() - t0) * 1000, 1),
            },
        )
        try:
            from app.metrics.collector import collector

            collector.track_agent_dispatch_error("il2a_handler_timeout")
        except Exception:
            pass
        return {
            "created": 0,
            "skipped": 0,
            "errors": 1,
            "reason": "handler_timeout",
        }
    except Exception:
        logger.exception(
            "IL-2A on_decision_created failed",
            extra={
                "decision_id": decision_id,
                "step": "failed",
                "elapsed_ms": round((time.monotonic() - t0) * 1000, 1),
            },
        )
        try:
            from app.metrics.collector import collector

            collector.track_agent_dispatch_error("il2a_handler_failed")
        except Exception:
            pass
        raise
    finally:
        reset_current_tenant_id(token)
