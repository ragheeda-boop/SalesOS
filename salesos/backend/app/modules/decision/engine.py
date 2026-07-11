import time
import uuid
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict

from app.modules.decision.schemas import (
    DecisionContext,
    DecisionResult,
    DecisionHistoryItem,
    DecisionHistoryRecommendation,
    EvidenceItem,
    DecisionRule,
    Score,
    ScoreFactor,
    Recommendation,
    AlternativeRecommendation,
    Risk,
    Explainability,
    ExpectedImpact,
    Feedback,
    FeedbackRecord,
    FeedbackStats,
    LearningEvent,
    QualityMetrics,
    LearningTrend,
    Telemetry,
)


def _generate_id() -> str:
    return str(uuid.uuid4())


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


BASE_RULES: list[DecisionRule] = [
    DecisionRule(
        id="rule-high-intent",
        name="High Intent Signal",
        description="Trigger when entity shows strong buying intent",
        priority=1,
        category="intent",
        version="1.0.0",
        conditions={"signalStrength": "high"},
        action="accelerate",
        weight=0.9,
    ),
    DecisionRule(
        id="rule-risk-check",
        name="Risk Assessment",
        description="Evaluate risk level for the entity",
        priority=2,
        category="risk",
        version="1.0.0",
        conditions={"entityType": ["company", "opportunity"]},
        action="assess_risk",
        weight=0.7,
    ),
    DecisionRule(
        id="rule-engagement",
        name="Engagement Recency",
        description="Check how recently the entity was engaged",
        priority=3,
        category="engagement",
        version="1.0.0",
        conditions={"maxDaysSinceContact": 30},
        action="re_engage",
        weight=0.5,
    ),
    DecisionRule(
        id="rule-data-quality",
        name="Data Quality Gate",
        description="Ensure minimum data quality before action",
        priority=0,
        category="quality",
        version="1.0.0",
        conditions={"minConfidence": 0.3},
        action="validate",
        weight=1.0,
    ),
]


def _collect_evidence(context: DecisionContext) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    ts = _now_iso()

    if context.metadata:
        for key, value in context.metadata.items():
            if value is not None:
                evidence.append(
                    EvidenceItem(
                        id=_generate_id(),
                        type="signal",
                        description=f"{key}: {str(value)}",
                        source="context.metadata",
                        confidence=0.7,
                        freshness="current",
                        timestamp=ts,
                        data={"key": key, "rawValue": value},
                    )
                )

    if context.entity_type:
        evidence.append(
            EvidenceItem(
                id=_generate_id(),
                type="document",
                description=f"Entity type identified: {context.entity_type}",
                source="context.entityType",
                confidence=1.0,
                freshness="current",
                timestamp=ts,
                data={"entityType": context.entity_type},
            )
        )

    if context.company_id:
        evidence.append(
            EvidenceItem(
                id=_generate_id(),
                type="signal",
                description=f"Company context provided: {context.company_id}",
                source="context.companyId",
                confidence=1.0,
                freshness="current",
                timestamp=ts,
                data={"companyId": context.company_id},
            )
        )

    if context.opportunity_id:
        evidence.append(
            EvidenceItem(
                id=_generate_id(),
                type="timeline",
                description=f"Opportunity context provided: {context.opportunity_id}",
                source="context.opportunityId",
                confidence=1.0,
                freshness="current",
                timestamp=ts,
                data={"opportunityId": context.opportunity_id},
            )
        )

    if not evidence:
        evidence.append(
            EvidenceItem(
                id=_generate_id(),
                type="search",
                description="No contextual evidence available — default evaluation",
                source="decision-engine.default",
                confidence=0.3,
                freshness="stale",
                timestamp=ts,
            )
        )

    return evidence


def _apply_rules(context: DecisionContext, evidence: list[EvidenceItem]) -> list[DecisionRule]:
    applied: list[DecisionRule] = []

    for rule in BASE_RULES:
        if rule.category == "quality":
            applied.append(rule)
            continue

        if rule.category == "intent":
            has_high_intent = any(
                e.data
                and isinstance(e.data, dict)
                and e.data.get("strength") == "high"
                for e in evidence
            )
            if has_high_intent or len(evidence) > 3:
                applied.append(rule)
            continue

        if rule.category == "risk":
            if context.entity_type in ("company", "opportunity"):
                applied.append(rule)
            continue

        if rule.category == "engagement":
            applied.append(rule)
            continue

    applied.sort(key=lambda r: (-r.priority, -r.weight))
    return applied


def _compute_scores(
    context: DecisionContext,
    evidence: list[EvidenceItem],
    rules_applied: list[DecisionRule],
) -> list[Score]:
    ts = _now_iso()
    scores: list[Score] = []

    evidence_confidence = (
        sum(e.confidence for e in evidence) / len(evidence) if evidence else 0
    )
    rule_weight = (
        sum(r.weight for r in rules_applied) / len(rules_applied) if rules_applied else 0
    )
    combined = round((evidence_confidence * 0.6 + rule_weight * 0.4) * 100) / 100

    # Confidence score
    if combined >= 0.7:
        conf_label = "High"
    elif combined >= 0.4:
        conf_label = "Medium"
    else:
        conf_label = "Low"

    scores.append(
        Score(
            type="confidence",
            value=combined,
            confidence=evidence_confidence,
            label=conf_label,
            factors=[
                ScoreFactor(
                    name="evidence_strength",
                    value=evidence_confidence,
                    weight=0.6,
                    description="Average confidence of collected evidence items",
                    source="decision-engine.evidence",
                ),
                ScoreFactor(
                    name="rule_alignment",
                    value=rule_weight,
                    weight=0.4,
                    description="Average weight of applicable rules",
                    source="decision-engine.rules",
                ),
            ],
            timestamp=ts,
        )
    )

    # Company score
    if context.entity_type == "company" or not context.entity_type:
        ctx_completeness = 0.8 if len(evidence) > 2 else 0.5 if evidence else 0.2
        entity_match = 1.0 if context.entity_type else 0.3
        if combined >= 0.7:
            co_label = "Strong"
        elif combined >= 0.4:
            co_label = "Moderate"
        else:
            co_label = "Weak"
        scores.append(
            Score(
                type="company",
                value=combined,
                confidence=evidence_confidence,
                label=co_label,
                factors=[
                    ScoreFactor(
                        name="context_completeness",
                        value=ctx_completeness,
                        weight=0.5,
                        description="Completeness of available context",
                        source="decision-engine.context",
                    ),
                    ScoreFactor(
                        name="entity_type_match",
                        value=entity_match,
                        weight=0.5,
                        description="Whether entity type is specified",
                        source="decision-engine.context",
                    ),
                ],
                timestamp=ts,
            )
        )

    # Revenue score
    if context.entity_type == "opportunity":
        rev_value = _clamp(combined * 1.1)
        rev_confidence = _clamp(evidence_confidence * 0.9)
        rev_label = "High potential" if combined >= 0.7 else "Moderate potential"
        scores.append(
            Score(
                type="revenue",
                value=rev_value,
                confidence=rev_confidence,
                label=rev_label,
                factors=[
                    ScoreFactor(
                        name="opportunity_signals",
                        value=combined,
                        weight=0.7,
                        description="Signals indicating revenue potential",
                        source="decision-engine.scoring",
                    ),
                    ScoreFactor(
                        name="risk_adjustment",
                        value=1 - rule_weight * 0.3,
                        weight=0.3,
                        description="Risk-adjusted revenue factor",
                        source="decision-engine.risk",
                    ),
                ],
                timestamp=ts,
            )
        )

    # Relationship score
    if context.entity_type == "person":
        if combined >= 0.7:
            rel_label = "Strong"
        elif combined >= 0.4:
            rel_label = "Developing"
        else:
            rel_label = "Weak"
        scores.append(
            Score(
                type="relationship",
                value=combined,
                confidence=evidence_confidence,
                label=rel_label,
                factors=[
                    ScoreFactor(
                        name="engagement_level",
                        value=evidence_confidence,
                        weight=0.6,
                        description="Level of engagement signals",
                        source="decision-engine.evidence",
                    ),
                    ScoreFactor(
                        name="recency",
                        value=0.7,
                        weight=0.4,
                        description="Recency of interactions",
                        source="decision-engine.timeline",
                    ),
                ],
                timestamp=ts,
            )
        )

    return scores


def _generate_recommendation(
    context: DecisionContext,
    evidence: list[EvidenceItem],
    scores: list[Score],
    rules_applied: list[DecisionRule],
    decision_id: str,
) -> Recommendation:
    ts = _now_iso()
    confidence_score = next((s for s in scores if s.type == "confidence"), None)
    value = confidence_score.value if confidence_score else 0.5
    conf_label: str = "high" if value >= 0.7 else "medium" if value >= 0.4 else "low"

    if value >= 0.7:
        action, action_label = "pursue", "Pursue Immediately"
    elif value >= 0.4:
        action, action_label = "nurture", "Nurture & Monitor"
    else:
        action, action_label = "deprioritize", "Deprioritize"

    if context.entity_type == "opportunity" and value >= 0.6:
        action, action_label = "accelerate", "Accelerate Deal"

    risks: list[Risk] = []
    if value < 0.4:
        risks.append(
            Risk(
                type="low_confidence",
                level="high",
                description="Low overall confidence in the decision",
                mitigation="Gather more evidence before proceeding",
            )
        )
    if len(evidence) < 2:
        risks.append(
            Risk(
                type="insufficient_data",
                level="medium",
                description="Limited evidence available for this decision",
                mitigation="Collect additional data points",
            )
        )
    if not rules_applied:
        risks.append(
            Risk(
                type="no_rules_matched",
                level="medium",
                description="No business rules matched this context",
                mitigation="Review rule configuration",
            )
        )

    alternatives: list[AlternativeRecommendation] = []
    if action not in ("pursue", "accelerate"):
        alternatives.append(
            AlternativeRecommendation(
                action="pursue",
                action_label="Pursue",
                reason="If additional evidence is gathered, pursuing may become viable",
                confidence=_clamp(value + 0.2),
            )
        )
    if action != "deprioritize":
        alternatives.append(
            AlternativeRecommendation(
                action="deprioritize",
                action_label="Deprioritize",
                reason="Conservative approach to focus resources elsewhere",
                confidence=1.0 - value,
            )
        )
    alternatives.append(
        AlternativeRecommendation(
            action="gather_evidence",
            action_label="Gather More Evidence",
            reason="Delay decision until more data is available",
            confidence=0.6,
        )
    )

    source: str = "hybrid" if rules_applied else "rule"
    priority = 1 if value >= 0.7 else 2 if value >= 0.4 else 3
    impact_label = "High" if value >= 0.7 else "Medium" if value >= 0.4 else "Low"

    return Recommendation(
        id=decision_id,
        action=action,
        action_label=action_label,
        reason=f"Based on {len(evidence)} evidence items and {len(rules_applied)} rules, the combined score is {round(value * 100)}%.",
        confidence=value,
        confidence_label=conf_label,
        source=source,
        priority=priority,
        business_impact=f"Impact level: {impact_label}",
        alternatives=alternatives,
        evidence=evidence,
        risks=risks,
        status="pending",
        created_at=ts,
        updated_at=ts,
    )


def _build_explainability(
    context: DecisionContext,
    evidence: list[EvidenceItem],
    rules_applied: list[DecisionRule],
    recommendation: Recommendation,
    scores: list[Score],
) -> Explainability:
    confidence_score = next((s for s in scores if s.type == "confidence"), None)
    value = confidence_score.value if confidence_score else 0.5
    risk_level: str = "low" if value >= 0.7 else "medium" if value >= 0.4 else "high"

    why_parts: list[str] = []
    if evidence:
        why_parts.append(f"{len(evidence)} evidence items were collected from context")
    if rules_applied:
        why_parts.append(f"{len(rules_applied)} business rules matched")

    why = "; ".join(why_parts) if why_parts else "Limited context available — default evaluation applied"
    entity_ref = context.entity_id or context.entity_type or "unknown"
    why_now = f"Decision requested at {_now_iso()} for entity {entity_ref}"
    why_this = (
        f"The '{recommendation.action}' action was recommended with "
        f"{round(recommendation.confidence * 100)}% confidence based on combined scoring"
    )
    why_not = [
        f"{a.action_label}: confidence {round(a.confidence * 100)}% — {a.reason}"
        for a in recommendation.alternatives
    ]

    timeframe = "30 days" if value >= 0.7 else "90 days" if value >= 0.4 else "180+ days"

    return Explainability(
        why=why,
        why_now=why_now,
        why_this_action=why_this,
        why_not_alternative=why_not,
        evidence=evidence,
        rules_applied=rules_applied,
        ai_reasoning=None,
        confidence=value,
        risk=risk_level,
        expected_impact=ExpectedImpact(
            revenue=round(value * 100000),
            timeframe=timeframe,
        ),
    )


# ---------------------------------------------------------------------------
# DecisionEngine
# ---------------------------------------------------------------------------

class DecisionEngine:
    def __init__(self) -> None:
        self._history: dict[str, DecisionResult] = {}
        self._tenant_history: dict[str, list[str]] = {}
        self._feedback_store: dict[str, FeedbackRecord] = {}
        self._tenant_feedback: dict[str, list[str]] = {}
        self._learning_events: list[tuple[str, LearningEvent]] = []
        self._custom_rules: dict[str, DecisionRule] = {}

    # -- Public rules registry --

    def list_rules(self, category: Optional[str] = None) -> list[DecisionRule]:
        all_rules = list(BASE_RULES) + list(self._custom_rules.values())
        if category:
            all_rules = [r for r in all_rules if r.category == category]
        return all_rules

    def create_rule(self, rule: DecisionRule) -> DecisionRule:
        if rule.id in {r.id for r in BASE_RULES} or rule.id in self._custom_rules:
            raise ValueError(f"Rule with id '{rule.id}' already exists")
        self._custom_rules[rule.id] = rule
        return rule

    # -- Core evaluation pipeline --

    def evaluate(self, context: DecisionContext) -> DecisionResult:
        decision_id = _generate_id()
        eval_start = time.perf_counter()

        t = time.perf_counter()
        evidence = _collect_evidence(context)
        evidence_ms = round((time.perf_counter() - t) * 1000, 2)

        t = time.perf_counter()
        rules_applied = _apply_rules(context, evidence)
        rules_ms = round((time.perf_counter() - t) * 1000, 2)

        t = time.perf_counter()
        scores = _compute_scores(context, evidence, rules_applied)
        scoring_ms = round((time.perf_counter() - t) * 1000, 2)

        t = time.perf_counter()
        recommendation = _generate_recommendation(context, evidence, scores, rules_applied, decision_id)
        rec_ms = round((time.perf_counter() - t) * 1000, 2)

        explainability = _build_explainability(context, evidence, rules_applied, recommendation, scores)
        eval_total = round((time.perf_counter() - eval_start) * 1000, 2)

        result = DecisionResult(
            decision_id=decision_id,
            context=context,
            recommendation=recommendation,
            scores=scores,
            rules_applied=rules_applied,
            evidence=evidence,
            explainability=explainability,
            telemetry=Telemetry(
                evaluation_time_ms=eval_total,
                rules_time_ms=rules_ms,
                scoring_time_ms=scoring_ms,
                evidence_time_ms=evidence_ms,
                recommendation_time_ms=rec_ms,
            ),
            timestamp=_now_iso(),
        )

        self._history[decision_id] = result
        self._tenant_history.setdefault(context.tenant_id, []).append(decision_id)

        return result

    def evaluate_batch(self, contexts: list[DecisionContext]) -> list[DecisionResult]:
        return [self.evaluate(ctx) for ctx in contexts]

    def explain(self, decision_id: str) -> Optional[Explainability]:
        result = self._history.get(decision_id)
        if result:
            return result.explainability
        return None

    def get_history(
        self,
        tenant_id: str,
        limit: Optional[int] = None,
    ) -> list[DecisionHistoryItem]:
        ids = self._tenant_history.get(tenant_id, [])
        sliced = ids[-limit:] if limit else ids
        items: list[DecisionHistoryItem] = []
        for did in sliced:
            result = self._history.get(did)
            if result:
                fb = self._get_feedback_for_decision(did)
                items.append(
                    DecisionHistoryItem(
                        decision_id=result.decision_id,
                        context=result.context,
                        recommendation=DecisionHistoryRecommendation(
                            action=result.recommendation.action,
                            action_label=result.recommendation.action_label,
                            confidence=result.recommendation.confidence,
                        ),
                        outcome=fb.outcome if fb else None,
                        revenue_impact=fb.revenue_impact if fb else None,
                        created_at=result.timestamp,
                        updated_at=result.timestamp,
                    )
                )
        items.sort(key=lambda i: i.created_at, reverse=True)
        return items

    def get_recommendations(
        self,
        tenant_id: str,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        status: Optional[str] = "pending",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Recommendation], int]:
        recs: list[Recommendation] = []
        for did in self._tenant_history.get(tenant_id, []):
            result = self._history.get(did)
            if not result:
                continue
            rec = result.recommendation
            if status and rec.status != status:
                continue
            if entity_id and result.context.entity_id != entity_id:
                continue
            if entity_type and result.context.entity_type != entity_type:
                continue
            recs.append(rec)

        recs.sort(key=lambda r: (r.priority, -r.confidence))
        total = len(recs)
        return recs[offset : offset + limit], total

    def get_scores(
        self,
        tenant_id: str,
        entity_id: str,
        entity_type: str,
    ) -> list[Score]:
        for did in reversed(self._tenant_history.get(tenant_id, [])):
            result = self._history.get(did)
            if result and result.context.entity_id == entity_id:
                return result.scores
        return []

    def get_evidence(
        self,
        tenant_id: str,
        entity_id: str,
        evidence_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[EvidenceItem], int]:
        all_evidence: list[EvidenceItem] = []
        for did in self._tenant_history.get(tenant_id, []):
            result = self._history.get(did)
            if result and result.context.entity_id == entity_id:
                all_evidence.extend(result.evidence)
        if evidence_type:
            all_evidence = [e for e in all_evidence if e.type == evidence_type]
        all_evidence.sort(key=lambda e: -e.confidence)
        total = len(all_evidence)
        return all_evidence[offset : offset + limit], total

    # -- Feedback --

    def submit_feedback(self, feedback: Feedback) -> tuple[str, bool]:
        problems = self._validate_feedback(feedback)
        if problems:
            return "", False

        fb_id = _generate_id()
        record = FeedbackRecord(
            id=fb_id,
            decision_id=feedback.decision_id,
            tenant_id=feedback.tenant_id,
            actor_id=feedback.actor_id,
            outcome=feedback.outcome,
            reason=feedback.reason,
            revenue_impact=feedback.revenue_impact,
            time_to_execution=feedback.time_to_execution,
            actual_effort=feedback.actual_effort,
            metadata=feedback.metadata,
            timestamp=feedback.timestamp,
            created_at=_now_iso(),
        )
        self._feedback_store[fb_id] = record
        self._tenant_feedback.setdefault(feedback.tenant_id, []).append(fb_id)

        event_value = 1.0 if feedback.outcome == "accepted" else 0.0 if feedback.outcome == "rejected" else 0.5
        event = LearningEvent(
            id=_generate_id(),
            type="acceptance_rate",
            decision_id=feedback.decision_id,
            metric=feedback.outcome,
            value=event_value,
            factors={
                "revenueImpact": feedback.revenue_impact or 0,
                "timeToExecution": feedback.time_to_execution or 0,
            },
            timestamp=record.created_at,
        )
        self._learning_events.append((feedback.tenant_id, event))

        return fb_id, True

    def get_feedback_stats(self, tenant_id: str) -> FeedbackStats:
        fb_ids = self._tenant_feedback.get(tenant_id, [])
        records = [self._feedback_store[fid] for fid in fb_ids if fid in self._feedback_store]

        total = len(records)
        accepted = sum(1 for r in records if r.outcome == "accepted")
        rejected = sum(1 for r in records if r.outcome == "rejected")
        ignored = sum(1 for r in records if r.outcome == "ignored")
        total_revenue = sum(r.revenue_impact or 0 for r in records)

        timed = [r for r in records if r.time_to_execution is not None]
        avg_time = sum(r.time_to_execution for r in timed) / len(timed) if timed else None

        return FeedbackStats(
            total=total,
            accepted=accepted,
            rejected=rejected,
            ignored=ignored,
            acceptance_rate=accepted / total if total > 0 else 0,
            total_revenue_impact=total_revenue,
            average_time_to_execution=avg_time,
        )

    def get_learning_quality(self, tenant_id: str) -> QualityMetrics:
        tenant_events = [e for tid, e in self._learning_events if tid == tenant_id]
        quality_events = [e for e in tenant_events if e.type == "recommendation_quality"]
        acceptance_events = [e for e in tenant_events if e.type == "acceptance_rate"]

        if not quality_events:
            return QualityMetrics(
                average_confidence=0,
                average_acceptance_rate=0,
                total_recommendations=0,
                high_confidence_rate=0,
                medium_confidence_rate=0,
                low_confidence_rate=0,
            )

        total = len(quality_events)
        avg_conf = sum(e.factors.get("confidence", e.value) for e in quality_events) / total
        avg_accept = (
            sum(e.value for e in acceptance_events) / len(acceptance_events)
            if acceptance_events
            else 0
        )

        high = sum(1 for e in quality_events if e.factors.get("confidence", e.value) >= 0.8)
        medium = sum(
            1 for e in quality_events
            if 0.5 <= e.factors.get("confidence", e.value) < 0.8
        )
        low = sum(1 for e in quality_events if e.factors.get("confidence", e.value) < 0.5)

        return QualityMetrics(
            average_confidence=avg_conf,
            average_acceptance_rate=avg_accept,
            total_recommendations=total,
            high_confidence_rate=high / total if total else 0,
            medium_confidence_rate=medium / total if total else 0,
            low_confidence_rate=low / total if total else 0,
        )

    def get_learning_trends(self, tenant_id: str) -> list[LearningTrend]:
        import datetime as _dt

        tenant_events = [e for tid, e in self._learning_events if tid == tenant_id]
        now = _dt.datetime.now(_dt.timezone.utc)
        period = _dt.timedelta(days=7)
        current_start = now - period
        previous_start = current_start - period

        def _parse_ts(ts: str) -> _dt.datetime:
            try:
                return _dt.datetime.fromisoformat(ts)
            except Exception:
                return now

        def _avg(events: list[LearningEvent]) -> float:
            return sum(e.value for e in events) / len(events) if events else 0

        trend_defs = [
            ("acceptance_rate", "acceptance_rate"),
            ("recommendation_quality", "recommendation_quality"),
            ("rule_effectiveness", "rule_effectiveness"),
            ("signal_usefulness", "signal_usefulness"),
        ]

        trends: list[LearningTrend] = []
        for metric_name, event_type in trend_defs:
            curr = [
                e for e in tenant_events
                if e.type == event_type and _parse_ts(e.timestamp) >= current_start
            ]
            prev = [
                e for e in tenant_events
                if e.type == event_type and previous_start <= _parse_ts(e.timestamp) < current_start
            ]
            curr_val = _avg(curr)
            prev_val = _avg(prev)

            delta = curr_val - prev_val
            threshold = max(abs(prev_val) * 0.05, 0.001)
            if delta > threshold:
                trend_dir = "up"
            elif delta < -threshold:
                trend_dir = "down"
            else:
                trend_dir = "stable"

            if prev_val != 0:
                change_pct = ((curr_val - prev_val) / abs(prev_val)) * 100
            elif curr_val > 0:
                change_pct = 100.0
            else:
                change_pct = 0.0

            trends.append(
                LearningTrend(
                    metric=metric_name,
                    current_value=curr_val,
                    previous_value=prev_val,
                    trend=trend_dir,
                    change_percent=round(change_pct, 2),
                )
            )

        return trends

    # -- Helpers --

    def _get_feedback_for_decision(self, decision_id: str) -> Optional[FeedbackRecord]:
        for record in self._feedback_store.values():
            if record.decision_id == decision_id:
                return record
        return None

    @staticmethod
    def _validate_feedback(feedback: Feedback) -> list[str]:
        problems: list[str] = []
        if not feedback.decision_id:
            problems.append("decisionId is required")
        if not feedback.tenant_id:
            problems.append("tenantId is required")
        if not feedback.actor_id:
            problems.append("actorId is required")
        if not feedback.outcome or feedback.outcome not in ("accepted", "rejected", "ignored"):
            problems.append("outcome must be accepted, rejected, or ignored")
        if feedback.revenue_impact is not None and feedback.revenue_impact < 0:
            problems.append("revenueImpact cannot be negative")
        if feedback.time_to_execution is not None and feedback.time_to_execution < 0:
            problems.append("timeToExecution cannot be negative")
        return problems


decision_engine = DecisionEngine()
