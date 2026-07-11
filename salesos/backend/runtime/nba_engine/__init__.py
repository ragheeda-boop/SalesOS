"""Next Best Action Engine — Decision pipeline for Revenue Execution."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Optional

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class Evidence:
    id: str
    type: str  # business_rule | signal | ai_analysis | company_score | activity | risk_factor
    description: str
    source: str
    confidence: float
    timestamp: str
    data: dict | None = None


@dataclass
class Alternative:
    action: str
    reason: str
    confidence: float
    expected_impact: dict | None = None


@dataclass
class Impact:
    description: str
    estimated_revenue: float | None = None
    estimated_probability: float | None = None
    category: str = "information_gathering"  # revenue | relationship | risk_mitigation | information_gathering


@dataclass
class RiskFactor:
    type: str
    level: str  # low | medium | high
    description: str
    detected_at: str


@dataclass
class NBAResult:
    id: str
    opportunity_id: str
    action: str
    reason: str
    evidence: list[Evidence]
    confidence: float
    confidence_label: str  # high | medium | low
    source: str  # rule | ai | hybrid
    alternatives: list[Alternative]
    expected_impact: Impact
    potential_risks: list[RiskFactor]
    due_by: str | None = None
    status: str = "pending"
    pipeline_trace: dict | None = None
    created_at: str = ""
    updated_at: str = ""


@dataclass
class NormalizedSignal:
    source: str
    entity_type: str
    entity_id: str
    opportunity_id: str | None = None
    tenant_id: str = ""
    timestamp: str = ""
    data: dict = field(default_factory=dict)
    context: dict = field(default_factory=dict)


class NBAEngine:
    """Orchestrates the complete NBA decision pipeline."""

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        feature_store: Any = None,
        event_runtime: Any = None,
        logger: Any = None,
    ):
        self._session_factory = session_factory
        self._feature_store = feature_store
        self._event_runtime = event_runtime
        self._logger = logger

    async def get_or_compute(self, opportunity_id: str, tenant_id: str) -> NBAResult | None:
        """Return cached NBA if fresh, otherwise compute."""
        cached = await self._load_cached(opportunity_id, tenant_id)
        if cached:
            return cached
        return await self.recompute(opportunity_id, tenant_id)

    async def recompute(self, opportunity_id: str, tenant_id: str) -> NBAResult | None:
        """Run the full NBA pipeline for an opportunity."""
        t0 = time.monotonic()
        trace: dict[str, float] = {}

        # 1. Normalize — load opportunity + context
        t1 = time.monotonic()
        signal = await self._normalize(opportunity_id, tenant_id)
        trace["normalization_ms"] = (time.monotonic() - t1) * 1000
        if not signal:
            return None

        # 2. Business Rules
        t1 = time.monotonic()
        rule_candidates = await self._apply_rules(signal)
        trace["rules_ms"] = (time.monotonic() - t1) * 1000

        # 3. Scoring
        t1 = time.monotonic()
        scored = await self._score_candidates(signal, rule_candidates)
        trace["scoring_ms"] = (time.monotonic() - t1) * 1000

        # 4. AI Reasoning (optional — falls back to rule-only)
        t1 = time.monotonic()
        ai_ranking = await self._ai_evaluate(signal, scored)
        trace["ai_ms"] = (time.monotonic() - t1) * 1000

        # 5. Risk Assessment
        t1 = time.monotonic()
        risks = await self._assess_risk(signal)
        trace["risk_ms"] = (time.monotonic() - t1) * 1000

        # 6. Confidence + Ranking
        t1 = time.monotonic()
        nba = self._build_recommendation(signal, scored, ai_ranking, risks, trace)
        trace["confidence_ms"] = (time.monotonic() - t1) * 1000
        trace["total_ms"] = (time.monotonic() - t0) * 1000
        nba.pipeline_trace = trace

        await self._cache_result(nba, tenant_id)
        await self._emit_event(nba, tenant_id)
        return nba

    async def record_feedback(
        self, opportunity_id: str, nba_id: str, user_id: str,
        action: str, reason: str | None = None,
    ):
        """Record user feedback on an NBA recommendation."""
        from sqlalchemy import text
        async with self._session_factory() as session:
            await session.execute(
                text("""
                    INSERT INTO nba_feedback (id, nba_id, opportunity_id, user_id, action, reason, created_at)
                    VALUES (:id, :nba_id, :opp_id, :user_id, :action, :reason, NOW())
                """),
                {
                    "id": str(uuid.uuid4()),
                    "nba_id": nba_id,
                    "opp_id": opportunity_id,
                    "user_id": user_id,
                    "action": action,
                    "reason": reason or "",
                },
            )
            await session.commit()

    # ── Pipeline stages ─────────────────────────────────────────

    async def _normalize(self, opportunity_id: str, tenant_id: str) -> NormalizedSignal | None:
        """Load opportunity and enrich with company context + recent activities."""
        from sqlalchemy import text
        async with self._session_factory() as session:
            row = await session.execute(
                text("""
                    SELECT o.*, c.name_ar as company_name_ar, c.industry, c.city,
                           c.employees_count, c.annual_revenue
                    FROM commercial_opportunities o
                    LEFT JOIN companies c ON c.id::text = o.company_id
                    WHERE o.id = :oid AND o.tenant_id = :tid
                """),
                {"oid": opportunity_id, "tid": tenant_id},
            )
            opp = row.mappings().one_or_none()
            if not opp:
                return None

            # Recent activities
            activities = await session.execute(
                text("""
                    SELECT id, action, timestamp, description
                    FROM activity_records
                    WHERE tenant_id = :tid AND entity_id = :eid
                    ORDER BY timestamp DESC LIMIT 20
                """),
                {"tid": tenant_id, "eid": opportunity_id},
            )

            return NormalizedSignal(
                source="manual_refresh",
                entity_type="opportunity",
                entity_id=opportunity_id,
                opportunity_id=opportunity_id,
                tenant_id=tenant_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                data=dict(opp),
                context={
                    "opportunity": dict(opp),
                    "recent_activities": [dict(a) for a in activities.mappings().all()],
                },
            )

    async def _apply_rules(self, signal: NormalizedSignal) -> list[dict]:
        """Evaluate business rules: stage-based, time-based, health-based, signal-based."""
        from domains.commercial.opportunity.contracts.models import OpportunityStage

        candidates = []
        opp = signal.context.get("opportunity", {})
        stage = opp.get("stage", "prospecting")
        activities = signal.context.get("recent_activities", [])

        # Rule 1: Stage-based actions
        stage_actions = {
            "prospecting": ("send_introduction_email", "أرسل بريد تعريف للعميل", 0.85),
            "qualification": ("schedule_discovery_call", "جد موعد مكالمة اكتشاف", 0.90),
            "proposal": ("send_proposal", "أرسل عرض السعر", 0.90),
            "negotiation": ("review_contract_terms", "راجع بنود العقد", 0.85),
            "closed_won": ("schedule_onboarding", "جد موعد بدء الخدمة", 0.80),
            "closed_lost": ("analyze_loss", "حلل أسباب الخسارة", 0.70),
        }
        if stage in stage_actions:
            action, reason, score = stage_actions[stage]
            candidates.append({
                "action": action, "reason": reason, "score": score,
                "rule_name": f"stage_{stage}", "metadata": {"stage": stage},
            })

        # Rule 2: Stagnation (no activity for 7+ days)
        if activities:
            last_activity = activities[0].get("timestamp", "")
            if last_activity:
                days_since = (datetime.now(timezone.utc) - last_activity).days if isinstance(last_activity, datetime) else 14
                if days_since >= 14:
                    candidates.append({
                        "action": "send_follow_up", "reason": "أرسل متابعة — لا نشاط منذ 14 يومًا",
                        "score": min(0.95, 0.7 + days_since * 0.02),
                        "rule_name": "stagnation_14d", "metadata": {"days_since": days_since},
                    })

        return candidates

    async def _score_candidates(self, signal: NormalizedSignal, candidates: list[dict]) -> list[dict]:
        """Score candidates by opportunity score, urgency, and effort."""
        opp = signal.context.get("opportunity", {})
        activities = signal.context.get("recent_activities", [])

        # Opportunity score components
        deal_value_score = min(opp.get("value", 0) / 1000000, 1.0) * 25
        stage_scores = {"prospecting": 5, "qualification": 10, "proposal": 15, "negotiation": 20}
        stage_score = stage_scores.get(opp.get("stage", ""), 5)
        engagement_score = min(len(activities) * 3, 15)

        opportunity_score = (deal_value_score + stage_score + engagement_score) / 100

        for c in candidates:
            c["opportunity_score"] = opportunity_score
            c["combined_score"] = c["score"] * 0.6 + opportunity_score * 0.4

        candidates.sort(key=lambda c: -c["combined_score"])
        return candidates

    async def _ai_evaluate(self, signal: NormalizedSignal, candidates: list[dict]) -> list[str] | None:
        """Optional AI reasoning. Falls back to None if unavailable."""
        return None  # AI integration in Sprint 5

    async def _assess_risk(self, signal: NormalizedSignal) -> list[RiskFactor]:
        """Detect risk factors: stagnation, competition, engagement drop."""
        risks = []
        opp = signal.context.get("opportunity", {})
        activities = signal.context.get("recent_activities", [])

        if not activities:
            risks.append(RiskFactor(
                type="stagnation", level="high",
                description="لا يوجد أي نشاط منذ إنشاء الفرصة",
                detected_at=datetime.now(timezone.utc).isoformat(),
            ))
        return risks

    def _build_recommendation(
        self, signal: NormalizedSignal, candidates: list[dict],
        ai_ranking: list[str] | None, risks: list[RiskFactor],
        trace: dict,
    ) -> NBAResult:
        """Build the final NBA recommendation from pipeline outputs."""
        now = datetime.now(timezone.utc)

        if not candidates:
            return NBAResult(
                id=str(uuid.uuid4()),
                opportunity_id=signal.opportunity_id or signal.entity_id,
                action="no_action_needed",
                reason="لا توجد توصيات متاحة حاليًا",
                evidence=[], confidence=0.0, confidence_label="low",
                source="rule", alternatives=[], expected_impact=Impact(description=""),
                potential_risks=risks,
                created_at=now.isoformat(), updated_at=now.isoformat(),
            )

        top = candidates[0]
        combined_score = top.get("combined_score", 0.5)
        conf_label = "high" if combined_score >= 0.8 else "medium" if combined_score >= 0.5 else "low"

        evidence = [
            Evidence(
                id=str(uuid.uuid4()),
                type="business_rule",
                description=c["reason"],
                source=f"Rule: {c['rule_name']}",
                confidence=c["score"],
                timestamp=now.isoformat(),
            )
            for c in candidates[:3]
        ]

        alts = [
            Alternative(action=c["action"], reason=c["reason"], confidence=c["combined_score"])
            for c in candidates[1:4]
        ]

        return NBAResult(
            id=str(uuid.uuid4()),
            opportunity_id=signal.opportunity_id or signal.entity_id,
            action=top["action"],
            reason=top["reason"],
            evidence=evidence,
            confidence=combined_score,
            confidence_label=conf_label,
            source="rule",
            alternatives=alts,
            expected_impact=Impact(
                description=f"تنفيذ {top['action']} لفرصة {signal.data.get('name', '')}",
                category="revenue" if top["action"] in ("send_proposal", "review_contract_terms") else "information_gathering",
            ),
            potential_risks=risks,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
        )

    async def _load_cached(self, opportunity_id: str, tenant_id: str) -> NBAResult | None:
        """Check opportunity_features table for cached NBA."""
        from sqlalchemy import text
        async with self._session_factory() as session:
            row = await session.execute(
                text("""
                    SELECT score, signals, explanation, computed_at
                    FROM company_features
                    WHERE company_id = :cid AND tenant_id = :tid AND feature_name = 'nba'
                    AND computed_at >= NOW() - INTERVAL '1 hour'
                """),
                {"cid": opportunity_id, "tid": tenant_id},
            )
            r = row.mappings().one_or_none()
            if r:
                return NBAResult(
                    id="cached", opportunity_id=opportunity_id,
                    action="cached", reason=r["explanation"] or "",
                    evidence=[], confidence=float(r["score"]),
                    confidence_label="medium", source="rule",
                    alternatives=[], expected_impact=Impact(description=""),
                    potential_risks=[],
                )
            return None

    async def _cache_result(self, nba: NBAResult, tenant_id: str):
        """Store NBA result in company_features for caching."""
        from sqlalchemy import text
        async with self._session_factory() as session:
            await session.execute(
                text("""
                    INSERT INTO company_features (tenant_id, company_id, feature_name, score, signals, explanation, computed_at)
                    VALUES (:tid, :cid, 'nba', :score, :signals, :explanation, NOW())
                    ON CONFLICT (tenant_id, company_id, feature_name)
                    DO UPDATE SET score = :score, signals = :signals, explanation = :explanation, computed_at = NOW()
                """),
                {
                    "tid": tenant_id,
                    "cid": nba.opportunity_id,
                    "score": nba.confidence,
                    "signals": {"action": nba.action, "reason": nba.reason},
                    "explanation": nba.reason,
                },
            )
            await session.commit()

    async def _emit_event(self, nba: NBAResult, tenant_id: str):
        """Publish NBA result as domain event."""
        if self._event_runtime:
            from sdk.events.base import DomainEvent
            await self._event_runtime.publish(DomainEvent(
                event_type="nba.generated",
                aggregate_id=nba.opportunity_id,
                aggregate_type="opportunity",
                tenant_id=tenant_id,
                data={
                    "nba_id": nba.id,
                    "action": nba.action,
                    "confidence": nba.confidence,
                    "source": nba.source,
                },
            ))
