"""Decision Intelligence Engine (DIE) — orchestrates context, policies, decision engine, and NBA generation."""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from runtime.context_runtime import ContextBuilder, CompanyContext
from runtime.policy_runtime import PolicyEngine, PolicyResult
from runtime.recommendation_runtime import RecommendationEngine, Recommendation

from runtime.decision_runtime.models import (
    DecisionObject,
    DecisionFeedback,
    DecisionMetricsSnapshot,
    DecisionStatus,
    DecisionType,
    RequiredAction,
)
from runtime.decision_runtime.events import DecisionEvent, DecisionEventType
from sdk.events.base import DomainEvent as BaseDomainEvent


def _to_domain_event(raw: dict) -> BaseDomainEvent:
    return BaseDomainEvent(
        event_id=raw.get("event_id", str(uuid.uuid4())),
        event_type=raw.get("event_type", ""),
        event_version=raw.get("event_version", 1),
        aggregate_id=raw.get("aggregate_id", ""),
        aggregate_type=raw.get("aggregate_type", ""),
        tenant_id=raw.get("tenant_id", ""),
        data=raw.get("data", {}),
        metadata=raw.get("metadata", {}),
    )


logger = logging.getLogger(__name__)

_DEFAULT_MAX_DECISIONS = 10000
_DEFAULT_DECISION_TTL_SECONDS = 3600

# Identity register already hit this: EventRuntime store + subscriber fan-out
# (RetryPolicy 3× asyncio.wait_for(..., 10) per handler) blocks the awaiter
# ~30s while pool shows idle. Evaluate must return decision_id first; IL-2A
# AgentTask still runs via create_task fan-out (same pattern as
# app.modules.identity.service._publish_best_effort).
_EVENT_PUBLISH_SAFETY_TIMEOUT_SECONDS = 60.0


def _publish_decision_event_best_effort(
    event_runtime: Any,
    event: BaseDomainEvent,
    *,
    decision_id: str = "",
) -> None:
    """Schedule EventRuntime.publish off the HTTP critical path."""
    if event_runtime is None:
        return

    async def _run() -> None:
        t0 = time.monotonic()
        try:
            logger.info(
                "decision_engine.event_publish start",
                extra={
                    "decision_id": decision_id,
                    "event_type": getattr(event, "event_type", ""),
                    "step": "start",
                },
            )
            await asyncio.wait_for(
                event_runtime.publish(event),
                timeout=_EVENT_PUBLISH_SAFETY_TIMEOUT_SECONDS,
            )
            logger.info(
                "decision_engine.event_publish done",
                extra={
                    "decision_id": decision_id,
                    "step": "done",
                    "elapsed_ms": round((time.monotonic() - t0) * 1000, 1),
                },
            )
        except TimeoutError:
            logger.warning(
                "decision_engine.event_publish safety_timeout",
                extra={
                    "decision_id": decision_id,
                    "step": "safety_timeout",
                    "timeout_s": _EVENT_PUBLISH_SAFETY_TIMEOUT_SECONDS,
                    "elapsed_ms": round((time.monotonic() - t0) * 1000, 1),
                },
            )
        except Exception:
            logger.exception(
                "decision_engine.event_publish failed",
                extra={"decision_id": decision_id, "step": "failed"},
            )

    try:
        asyncio.get_running_loop().create_task(_run())
        logger.info(
            "decision_engine.event_publish scheduled",
            extra={
                "decision_id": decision_id,
                "event_type": getattr(event, "event_type", ""),
                "step": "scheduled",
            },
        )
    except Exception:
        logger.exception(
            "decision_engine.event_publish schedule_failed",
            extra={"decision_id": decision_id, "step": "schedule_failed"},
        )


@dataclass
class DecisionEngineMetrics:
    evaluations: int = 0
    decisions_created: int = 0
    decisions_accepted: int = 0
    decisions_executed: int = 0
    policies_checked: int = 0
    total_eval_ms: float = 0.0

    def snapshot(self) -> dict:
        return {
            "evaluations": self.evaluations,
            "decisions_created": self.decisions_created,
            "decisions_accepted": self.decisions_accepted,
            "decisions_executed": self.decisions_executed,
            "policies_checked": self.policies_checked,
            "total_eval_ms": round(self.total_eval_ms, 2),
            "avg_eval_ms": round(self.total_eval_ms / max(self.evaluations, 1), 2),
        }


class DecisionEngine:
    """Core engine — evaluates context against rules + policies → produces Next Best Action decision.

    Flow:
      1. Build full CompanyContext
      2. Evaluate policies
      3. Score features against rules
      4. Calculate confidence with reasoning
      5. Check blocked_by conditions
      6. Create DecisionObject
      7. Generate Recommendation from template
      8. Publish decision.created event
      9. Return NBA
    """

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        context_builder: ContextBuilder,
        policy_engine: PolicyEngine,
        recommendation_engine: RecommendationEngine,
        event_runtime: EventRuntime,
        feature_store: Any = None,
        logger: Any = None,
    ):
        self._session_factory = session_factory
        self._context_builder = context_builder
        self._policy_engine = policy_engine
        self._recommendation_engine = recommendation_engine
        self._event_runtime = event_runtime
        self._feature_store = feature_store
        self._logger = logger
        self.metrics = DecisionEngineMetrics()

        # In-memory decision store with eviction
        self._decisions: dict[str, DecisionObject] = {}
        self._max_decisions = _DEFAULT_MAX_DECISIONS
        self._decision_ttl = _DEFAULT_DECISION_TTL_SECONDS

    async def evaluate(self, company_id: str, tenant_id: str) -> Optional[dict]:
        """Evaluate company and return Next Best Action."""
        t0 = time.monotonic()
        self.metrics.evaluations += 1

        def _step(step: str) -> None:
            # IL-2A: identify which await hangs (no DecisionEngine errors today).
            elapsed_ms = (time.monotonic() - t0) * 1000
            logger.info(
                "decision_engine.evaluate step=%s elapsed_ms=%.1f company_id=%s",
                step,
                elapsed_ms,
                company_id,
            )

        _step("start")

        # 1. Build context
        context = await self._context_builder.build(company_id, tenant_id)
        _step("context_built")

        # 2. Evaluate policies
        policies = await self._policy_engine.evaluate(context.to_dict(), company_id, tenant_id)
        self.metrics.policies_checked += len(policies)
        _step("policies_evaluated")

        # 3. Check for blocks
        blocked = [p for p in policies if p.result == PolicyResult.BLOCK]
        if blocked:
            _step("blocked")
            return {
                "decision_id": None,
                "company_id": company_id,
                "action": "blocked",
                "reason": blocked[0].reason,
                "policy": blocked[0].policy_name,
            }

        # 4. Determine decision type and confidence
        decision_type, confidence, reasoning = await self._score_decision(context, tenant_id)
        _step("scored")

        # 5. Check existing non-expired decisions
        existing = await self._find_active_decisions(company_id, tenant_id)
        blocked_by = [d.decision_id for d in existing if d.status == DecisionStatus.SUGGESTED]

        # 6. Create DecisionObject
        decision = DecisionObject(
            decision_id=str(uuid.uuid4()),
            company_id=company_id,
            tenant_id=tenant_id,
            decision_type=decision_type,
            priority=self._calc_priority(confidence, context),
            confidence=confidence,
            expected_revenue=self._estimate_revenue(context),
            expected_probability=self._estimate_probability(context, decision_type),
            reasoning=reasoning,
            evidence=[p.reason for p in policies],
            supporting_features=context.features,
            context_snapshot=context.to_dict(),
            blocked_by=blocked_by[:5],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        # 7. Persist (in-memory NBA still returned if DB persist fails)
        try:
            await self._save_decision(decision)
        except Exception:
            logger.exception(
                "decision_engine.evaluate persist_failed decision_id=%s company_id=%s",
                decision.decision_id,
                company_id,
            )
        self._evict_decisions()
        self._decisions[decision.decision_id] = decision
        self.metrics.decisions_created += 1
        _step("decision_saved")

        # 8. Generate recommendation
        rec = await self._recommendation_engine.generate(
            decision_id=decision.decision_id,
            company_id=company_id,
            tenant_id=tenant_id,
            decision_type=decision.decision_type.value,
            priority=decision.priority,
            confidence=decision.confidence,
            reasoning=decision.reasoning,
            evidence=decision.evidence,
            context=context.to_dict(),
        )
        _step("recommendation_generated")

        # 9. Publish event (non-blocking — fan-out must not stall NBA HTTP)
        _step("event_publish_begin")
        event = DecisionEvent(
            event_type=DecisionEventType.CREATED,
            decision_id=decision.decision_id,
            company_id=company_id,
            tenant_id=tenant_id,
            decision_type=decision.decision_type.value,
        )
        _publish_decision_event_best_effort(
            self._event_runtime,
            _to_domain_event(event.to_domain_event()),
            decision_id=decision.decision_id,
        )
        _step("event_published")

        elapsed = (time.monotonic() - t0) * 1000
        self.metrics.total_eval_ms += elapsed
        _step("done")

        return self._build_nba_response(decision, rec, context)

    async def get_next_best_action(self, company_id: str, tenant_id: str) -> Optional[dict]:
        """Return the highest-priority actionable decision for a company."""
        active = sorted(
            [d for d in self._decisions.values()
             if d.company_id == company_id and d.tenant_id == tenant_id
             and d.status == DecisionStatus.SUGGESTED and not d.blocked_by],
            key=lambda d: d.priority, reverse=True,
        )
        if not active:
            return await self.evaluate(company_id, tenant_id)
        best = active[0]
        return {"decision_id": best.decision_id, "action": "existing", "decision": best.to_dict()}

    async def accept_decision(self, decision_id: str, tenant_id: str, user_id: Optional[str] = None) -> bool:
        decision = self._decisions.get(decision_id)
        if not decision or decision.tenant_id != tenant_id or decision.status != DecisionStatus.SUGGESTED:
            return False
        decision.status = DecisionStatus.ACCEPTED
        self.metrics.decisions_accepted += 1
        await self._update_status(decision_id, "accepted", tenant_id)
        event = DecisionEvent(
            event_type=DecisionEventType.ACCEPTED,
            decision_id=decision_id,
            company_id=decision.company_id,
            tenant_id=decision.tenant_id,
            decision_type=decision.decision_type.value,
            new_status="accepted",
        )
        _publish_decision_event_best_effort(
            self._event_runtime,
            _to_domain_event(event.to_domain_event()),
            decision_id=decision_id,
        )
        return True

    async def execute_decision(self, decision_id: str, tenant_id: str, user_id: Optional[str] = None) -> bool:
        decision = self._decisions.get(decision_id)
        if not decision or decision.tenant_id != tenant_id or decision.status != DecisionStatus.ACCEPTED:
            return False
        decision.status = DecisionStatus.EXECUTED
        decision.executed_at = datetime.now(timezone.utc)
        self.metrics.decisions_executed += 1
        await self._update_status(decision_id, "executed", tenant_id)
        event = DecisionEvent(
            event_type=DecisionEventType.EXECUTED,
            decision_id=decision_id,
            company_id=decision.company_id,
            tenant_id=decision.tenant_id,
            decision_type=decision.decision_type.value,
            new_status="executed",
        )
        _publish_decision_event_best_effort(
            self._event_runtime,
            _to_domain_event(event.to_domain_event()),
            decision_id=decision_id,
        )
        return True

    async def submit_feedback(
        self,
        decision_id: str,
        accepted: bool,
        tenant_id: str,
        executed: bool = False,
        outcome: Optional[str] = None,
        outcome_value: Optional[float] = None,
        notes: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        decision = self._decisions.get(decision_id)
        if not decision or decision.tenant_id != tenant_id:
            return False
        decision.feedback = DecisionFeedback(
            decision_id=decision_id,
            accepted=accepted,
            executed=executed,
            outcome=outcome,
            outcome_value=outcome_value,
            notes=notes,
            user_id=user_id,
        )
        event = DecisionEvent(
            event_type=DecisionEventType.FEEDBACK_RECEIVED,
            decision_id=decision_id,
            company_id=decision.company_id,
            tenant_id=decision.tenant_id,
            decision_type=decision.decision_type.value,
            feedback=vars(decision.feedback),
        )
        _publish_decision_event_best_effort(
            self._event_runtime,
            _to_domain_event(event.to_domain_event()),
            decision_id=decision_id,
        )
        return True

    def get_decision(self, decision_id: str, tenant_id: str) -> Optional[dict]:
        d = self._decisions.get(decision_id)
        if not d or d.tenant_id != tenant_id:
            return None
        return d.to_dict()

    def get_decisions(self, company_id: str, tenant_id: str, limit: int = 20) -> list[dict]:
        matching = [d.to_dict() for d in self._decisions.values()
                    if d.company_id == company_id and d.tenant_id == tenant_id]
        return sorted(matching, key=lambda x: x["created_at"], reverse=True)[:limit]

    def get_history(self, company_id: str, tenant_id: str) -> list[dict]:
        return self.get_decisions(company_id, tenant_id, limit=100)

    async def get_reasoning(self, decision_id: str, tenant_id: str) -> Optional[dict]:
        d = self._decisions.get(decision_id)
        if not d or d.tenant_id != tenant_id:
            return None
        return {
            "decision_id": d.decision_id,
            "reasoning": d.reasoning,
            "evidence": d.evidence,
            "supporting_features": d.supporting_features,
            "rules_applied": [p for p in d.evidence],
            "confidence": d.confidence,
            "why": f"{d.reasoning} Evidence: {'; '.join(d.evidence[:3])}. Features: {', '.join(f'{k}={v}' for k, v in list(d.supporting_features.items())[:5])}.",
        }

    def get_metrics(self) -> dict:
        return self.metrics.snapshot()

    # ── Private helpers ────────────────────────────────────────

    def _evict_decisions(self) -> int:
        """Evict expired and overflow decisions. Returns number evicted."""
        evicted = 0
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self._decision_ttl)

        expired = [
            did for did, d in self._decisions.items()
            if d.created_at and d.created_at < cutoff
        ]
        for did in expired:
            del self._decisions[did]
            evicted += 1

        overflow = len(self._decisions) - self._max_decisions
        if overflow > 0:
            oldest = sorted(
                self._decisions.items(),
                key=lambda x: x[1].created_at or datetime.min.replace(tzinfo=timezone.utc),
            )[:overflow]
            for did, _ in oldest:
                del self._decisions[did]
                evicted += 1

        if evicted > 0 and self._logger:
            self._logger.warning(
                "Decision store evicted %d entries (expired=%d, overflow=%d). Current size: %d",
                evicted, len(expired), max(0, overflow), len(self._decisions),
            )

        return evicted

    async def _score_decision(self, context: CompanyContext, tenant_id: str) -> tuple[DecisionType, float, str]:
        features = context.features
        intent = features.get("intent_score", 0)
        funding = features.get("funding_score", 0)
        hiring = features.get("hiring_score", 0)
        expansion = features.get("expansion_score", 0)
        revenue = features.get("revenue_score", 0)

        scores = [
            ("recommend_demo", intent, "High buying intent detected"),
            ("recommend_outreach", funding, "Funding event — executive outreach recommended"),
            ("recommend_campaign", hiring, "Hiring surge — HR campaign opportunity"),
            ("recommend_campaign", expansion, "Expansion potential detected"),
            ("recommend_call", revenue, "Revenue opportunity — call recommended"),
        ]

        best_type = DecisionType.RECOMMEND_CALL
        best_score = 0.0
        best_reason = "Standard follow-up based on available data"
        signals_used: list[str] = []

        for dt_name, score, reason in scores:
            if score > best_score:
                best_score = score
                best_type = DecisionType(dt_name)
                best_reason = reason
                signals_used.append(dt_name)

        # Confidence calculation
        confidence_parts: list[str] = []
        confidence = 0.5
        if intent > 50:
            confidence += 0.12
            confidence_parts.append("Intent")
        if funding > 50:
            confidence += 0.10
            confidence_parts.append("Funding")
        if hiring > 50:
            confidence += 0.08
            confidence_parts.append("Hiring")
        if expansion > 50:
            confidence += 0.08
            confidence_parts.append("Expansion")
        if revenue > 50:
            confidence += 0.12
            confidence_parts.append("Revenue")

        confidence = min(confidence, 0.95)

        # Reasoning
        reasoning_parts = [best_reason]
        if confidence_parts:
            reasoning_parts.append(f"Confidence driven by: {' + '.join(confidence_parts)}")
        reasoning = ". ".join(reasoning_parts)

        return best_type, round(confidence, 2), reasoning

    def _calc_priority(self, confidence: float, context: CompanyContext) -> int:
        base = int(confidence * 100)
        features = context.features
        if context.revenue.days_to_renewal is not None and context.revenue.days_to_renewal <= 30:
            base += 20
        if features.get("intent_score", 0) > 80:
            base += 10
        if features.get("funding_score", 0) > 80:
            base += 10
        return min(base, 100)

    def _estimate_revenue(self, context: CompanyContext) -> Optional[float]:
        features = context.features
        revenue_score = features.get("revenue_score", 0)
        if revenue_score > 70:
            base = context.revenue.annual_revenue or 100000
            return base * 0.15
        return None

    def _estimate_probability(self, context: CompanyContext, decision_type: DecisionType) -> Optional[float]:
        features = context.features
        intent = features.get("intent_score", 0)
        base = intent / 100
        if decision_type == DecisionType.RECOMMEND_DEMO:
            return round(base * 0.4, 2)
        if decision_type == DecisionType.RECOMMEND_CALL:
            return round(base * 0.3, 2)
        if decision_type == DecisionType.RECOMMEND_PROPOSAL:
            return round(base * 0.6, 2)
        return round(base * 0.35, 2)

    def _build_nba_response(self, decision: DecisionObject, rec: Recommendation, context: CompanyContext) -> dict:
        return {
            "decision_id": decision.decision_id,
            "company_id": decision.company_id,
            "decision_type": decision.decision_type.value,
            "priority": decision.priority,
            "confidence": decision.confidence,
            "confidence_explanation": self._explain_confidence(decision),
            "reasoning": decision.reasoning,
            "evidence": decision.evidence,
            "supporting_features": decision.supporting_features,
            "expected_revenue": decision.expected_revenue,
            "expected_probability": decision.expected_probability,
            "recommendation": rec.to_dict(),
            "policies": self._policy_engine.metrics.snapshot(),
        }

    def _explain_confidence(self, decision: DecisionObject) -> str:
        features = decision.supporting_features
        parts = [f"{k}={v}" for k, v in sorted(features.items(), key=lambda x: -x[1])[:5]]
        return f"Confidence: {decision.confidence*100:.0f}%. Based on: {' + '.join(parts)}."

    async def _save_decision(self, decision: DecisionObject) -> None:
        """Persist DecisionObject. JSONB must be json.dumps + CAST (asyncpg text binds)."""
        from sqlalchemy import text as sa_text

        from app.database import apply_tenant_guc

        t0 = time.monotonic()

        def _save_step(step: str) -> None:
            logger.info(
                "decision_engine._save_decision step=%s elapsed_ms=%.1f decision_id=%s",
                step,
                (time.monotonic() - t0) * 1000,
                decision.decision_id,
            )

        async def _persist() -> None:
            _save_step("enter")
            async with self._session_factory() as session:
                _save_step("checkout")
                await apply_tenant_guc(session, decision.tenant_id)
                _save_step("tenant_guc")
                existing = await session.execute(
                    sa_text("SELECT id FROM decisions WHERE decision_id = :did"),
                    {"did": decision.decision_id},
                )
                if existing.scalar_one_or_none():
                    _save_step("already_exists")
                    return
                _save_step("select_done")
                # IL-2A: raw list/dict binds → asyncpg DataError ('list' has no encode);
                # under PgBouncer that failure path can stall ~pool_timeout (30s).
                await session.execute(
                    sa_text("""
                        INSERT INTO decisions (decision_id, company_id, tenant_id, decision_type,
                            priority, confidence, expected_revenue, expected_probability,
                            reasoning, evidence, supporting_features, context_snapshot,
                            status, created_at, expires_at)
                        VALUES (:did, :cid, :tid, :dt, :pri, :conf, :rev, :prob,
                            :reason, CAST(:evidence AS jsonb), CAST(:features AS jsonb),
                            CAST(:ctx AS jsonb), :status, :created, :expires)
                    """),
                    {
                        "did": decision.decision_id,
                        "cid": decision.company_id,
                        "tid": decision.tenant_id,
                        "dt": decision.decision_type.value,
                        "pri": decision.priority,
                        "conf": decision.confidence,
                        "rev": decision.expected_revenue,
                        "prob": decision.expected_probability,
                        "reason": decision.reasoning,
                        "evidence": json.dumps(decision.evidence),
                        "features": json.dumps(decision.supporting_features),
                        "ctx": json.dumps(decision.context_snapshot, default=str),
                        "status": decision.status.value,
                        "created": decision.created_at,
                        "expires": decision.expires_at,
                    },
                )
                _save_step("inserted")
                await session.commit()
                _save_step("committed")

        try:
            await asyncio.wait_for(_persist(), timeout=12.0)
        except TimeoutError:
            logger.error(
                "decision_engine._save_decision timeout decision_id=%s elapsed_ms=%.1f",
                decision.decision_id,
                (time.monotonic() - t0) * 1000,
            )
            raise

    async def _update_status(self, decision_id: str, status: str, tenant_id: str) -> None:
        from sqlalchemy import text as sa_text

        from app.database import apply_tenant_guc

        async with self._session_factory() as session:
            await apply_tenant_guc(session, tenant_id)
            await session.execute(
                sa_text(
                    "UPDATE decisions SET status = :s, updated_at = NOW() "
                    "WHERE decision_id = :did AND tenant_id = :tid"
                ),
                {"s": status, "did": decision_id, "tid": tenant_id},
            )
            await session.commit()

    async def _find_active_decisions(self, company_id: str, tenant_id: str) -> list[DecisionObject]:
        return [
            d for d in self._decisions.values()
            if d.company_id == company_id and d.tenant_id == tenant_id
            and d.status in (DecisionStatus.SUGGESTED, DecisionStatus.ACCEPTED)
        ]

    async def close(self) -> None:
        """Clear in-memory state and release references."""
        self._decisions.clear()
        self._session_factory = None  # type: ignore
        self._context_builder = None  # type: ignore
        self._policy_engine = None  # type: ignore
        self._recommendation_engine = None  # type: ignore
        self._event_runtime = None  # type: ignore
        self._feature_store = None  # type: ignore
