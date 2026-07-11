from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.dependencies import get_current_tenant_id, verify_token
from app.modules.decision.engine import decision_engine, DecisionEngine
from app.modules.decision.schemas import (
    DecisionContext,
    DecisionContextAPI,
    DecisionResultAPI,
    DecisionRuleAPI,
    FeedbackRequest,
    FeedbackSubmitResponseAPI,
    FeedbackStatsAPI,
    ExplainResponseAPI,
    HistoryResponseAPI,
    RecommendationsResponseAPI,
    ScoresResponseAPI,
    EvidenceResponseAPI,
    RulesResponseAPI,
    RuleCreateRequest,
    LearningTrendsResponseAPI,
    QualityMetricsAPI,
    BatchResponseAPI,
    BatchSummaryAPI,
)

router = APIRouter(prefix="/api/v1/decision")

API_VERSION = "1.0.0"


def _engine() -> DecisionEngine:
    return decision_engine


def _context_to_api(ctx: DecisionContext) -> DecisionContextAPI:
    return DecisionContextAPI(
        tenantId=ctx.tenant_id,
        actorId=ctx.actor_id,
        entityId=ctx.entity_id,
        entityType=ctx.entity_type,
        opportunityId=ctx.opportunity_id,
        companyId=ctx.company_id,
        signalId=ctx.signal_id,
        metadata=ctx.metadata,
    )


def _result_to_api(result) -> DecisionResultAPI:
    from app.modules.decision.schemas import (
        RecommendationAPI,
        AlternativeRecommendationAPI,
        RiskAPI,
        EvidenceItemAPI,
        ScoreAPI,
        ScoreFactorAPI,
        DecisionRuleAPI,
        ExplainabilityAPI,
        ExpectedImpactAPI,
        TelemetryAPI,
    )

    rec = result.recommendation
    return DecisionResultAPI(
        decisionId=result.decision_id,
        context=_context_to_api(result.context),
        recommendation=RecommendationAPI(
            id=rec.id,
            action=rec.action,
            actionLabel=rec.action_label,
            reason=rec.reason,
            confidence=rec.confidence,
            confidenceLabel=rec.confidence_label,
            source=rec.source,
            priority=rec.priority,
            expectedRevenue=rec.expected_revenue,
            expectedEffort=rec.expected_effort,
            expectedTime=rec.expected_time,
            businessImpact=rec.business_impact,
            alternatives=[
                AlternativeRecommendationAPI(
                    action=a.action,
                    actionLabel=a.action_label,
                    reason=a.reason,
                    confidence=a.confidence,
                    expectedRevenue=a.expected_revenue,
                )
                for a in rec.alternatives
            ],
            evidence=[
                EvidenceItemAPI(
                    id=e.id, type=e.type, description=e.description,
                    source=e.source, confidence=e.confidence,
                    freshness=e.freshness, timestamp=e.timestamp,
                    severity=e.severity, url=e.url, data=e.data,
                )
                for e in rec.evidence
            ],
            risks=[
                RiskAPI(type=r.type, level=r.level, description=r.description, mitigation=r.mitigation)
                for r in rec.risks
            ],
            status=rec.status,
            createdAt=rec.created_at,
            updatedAt=rec.updated_at,
        ),
        scores=[
            ScoreAPI(
                type=s.type, value=s.value, confidence=s.confidence, label=s.label,
                factors=[
                    ScoreFactorAPI(
                        name=f.name, value=f.value, weight=f.weight,
                        description=f.description, source=f.source,
                    )
                    for f in s.factors
                ],
                timestamp=s.timestamp,
            )
            for s in result.scores
        ],
        rulesApplied=[
            DecisionRuleAPI(
                id=r.id, name=r.name, description=r.description,
                priority=r.priority, category=r.category, version=r.version,
                conditions=r.conditions, action=r.action, weight=r.weight,
            )
            for r in result.rules_applied
        ],
        evidence=[
            EvidenceItemAPI(
                id=e.id, type=e.type, description=e.description,
                source=e.source, confidence=e.confidence,
                freshness=e.freshness, timestamp=e.timestamp,
                severity=e.severity, url=e.url, data=e.data,
            )
            for e in result.evidence
        ],
        explainability=ExplainabilityAPI(
            why=result.explainability.why,
            whyNow=result.explainability.why_now,
            whyThisAction=result.explainability.why_this_action,
            whyNotAlternative=result.explainability.why_not_alternative,
            evidence=[
                EvidenceItemAPI(
                    id=e.id, type=e.type, description=e.description,
                    source=e.source, confidence=e.confidence,
                    freshness=e.freshness, timestamp=e.timestamp,
                    severity=e.severity, url=e.url, data=e.data,
                )
                for e in result.explainability.evidence
            ],
            rulesApplied=[
                DecisionRuleAPI(
                    id=r.id, name=r.name, description=r.description,
                    priority=r.priority, category=r.category, version=r.version,
                    conditions=r.conditions, action=r.action, weight=r.weight,
                )
                for r in result.explainability.rules_applied
            ],
            aiReasoning=result.explainability.ai_reasoning,
            confidence=result.explainability.confidence,
            risk=result.explainability.risk,
            expectedImpact=ExpectedImpactAPI(
                revenue=result.explainability.expected_impact.revenue,
                timeframe=result.explainability.expected_impact.timeframe,
            ),
        ),
        telemetry=TelemetryAPI(
            evaluationTimeMs=result.telemetry.evaluation_time_ms,
            rulesTimeMs=result.telemetry.rules_time_ms,
            scoringTimeMs=result.telemetry.scoring_time_ms,
            evidenceTimeMs=result.telemetry.evidence_time_ms,
            recommendationTimeMs=result.telemetry.recommendation_time_ms,
        ),
        timestamp=result.timestamp,
    )


# ---------------------------------------------------------------------------
# Decision Evaluation
# ---------------------------------------------------------------------------

@router.post("/evaluate", response_model=DecisionResultAPI)
async def evaluate_decision(
    body: DecisionContext,
    tenant_id: str = Depends(get_current_tenant_id),
    _token: dict = Depends(verify_token),
):
    if body.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch")
    engine = _engine()
    result = engine.evaluate(body)
    return _result_to_api(result)


@router.post("/batch", response_model=BatchResponseAPI)
async def evaluate_batch(
    contexts: list[DecisionContext],
    tenant_id: str = Depends(get_current_tenant_id),
    _token: dict = Depends(verify_token),
):
    if len(contexts) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 contexts per batch")
    for ctx in contexts:
        if ctx.tenant_id != tenant_id:
            raise HTTPException(status_code=403, detail="Tenant mismatch in batch context")

    engine = _engine()
    import time
    start = time.perf_counter()
    results = engine.evaluate_batch(contexts)
    total_ms = round((time.perf_counter() - start) * 1000, 2)

    return BatchResponseAPI(
        results=[_result_to_api(r) for r in results],
        summary=BatchSummaryAPI(
            total=len(results),
            succeeded=len(results),
            failed=0,
            totalTimeMs=total_ms,
        ),
    )


@router.get("/{decision_id}/explain", response_model=ExplainResponseAPI)
async def explain_decision(
    decision_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    _token: dict = Depends(verify_token),
):
    engine = _engine()
    explainability = engine.explain(decision_id)
    if explainability is None:
        raise HTTPException(status_code=404, detail="Decision not found")

    from app.modules.decision.schemas import ExplainabilityAPI, ExpectedImpactAPI, EvidenceItemAPI, DecisionRuleAPI
    return ExplainResponseAPI(
        decisionId=decision_id,
        explainability=ExplainabilityAPI(
            why=explainability.why,
            whyNow=explainability.why_now,
            whyThisAction=explainability.why_this_action,
            whyNotAlternative=explainability.why_not_alternative,
            evidence=[
                EvidenceItemAPI(
                    id=e.id, type=e.type, description=e.description,
                    source=e.source, confidence=e.confidence,
                    freshness=e.freshness, timestamp=e.timestamp,
                    severity=e.severity, url=e.url, data=e.data,
                )
                for e in explainability.evidence
            ],
            rulesApplied=[
                DecisionRuleAPI(
                    id=r.id, name=r.name, description=r.description,
                    priority=r.priority, category=r.category, version=r.version,
                    conditions=r.conditions, action=r.action, weight=r.weight,
                )
                for r in explainability.rules_applied
            ],
            aiReasoning=explainability.ai_reasoning,
            confidence=explainability.confidence,
            risk=explainability.risk,
            expectedImpact=ExpectedImpactAPI(
                revenue=explainability.expected_impact.revenue,
                timeframe=explainability.expected_impact.timeframe,
            ),
        ),
    )


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

@router.get("/history", response_model=HistoryResponseAPI)
async def get_history(
    tenant_id: str = Depends(get_current_tenant_id),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    entity_type: Optional[str] = Query(None),
    outcome: Optional[str] = Query(None),
    _token: dict = Depends(verify_token),
):
    engine = _engine()
    items = engine.get_history(tenant_id, limit=offset + limit)
    filtered = items[offset:]

    if entity_type:
        filtered = [i for i in filtered if i.context.entity_type == entity_type]
    if outcome:
        if outcome == "null":
            filtered = [i for i in filtered if i.outcome is None]
        else:
            filtered = [i for i in filtered if i.outcome == outcome]

    from app.modules.decision.schemas import DecisionHistoryItemAPI, DecisionHistoryRecommendationAPI
    api_items = [
        DecisionHistoryItemAPI(
            decisionId=i.decision_id,
            context=_context_to_api(i.context),
            recommendation=DecisionHistoryRecommendationAPI(
                action=i.recommendation.action,
                actionLabel=i.recommendation.action_label,
                confidence=i.recommendation.confidence,
            ),
            outcome=i.outcome,
            revenueImpact=i.revenue_impact,
            createdAt=i.created_at,
            updatedAt=i.updated_at,
        )
        for i in filtered
    ]
    return HistoryResponseAPI(items=api_items, total=len(api_items))


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

@router.get("/recommendations", response_model=RecommendationsResponseAPI)
async def get_recommendations(
    tenant_id: str = Depends(get_current_tenant_id),
    entity_id: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    status: Optional[str] = Query("pending"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _token: dict = Depends(verify_token),
):
    engine = _engine()
    recs, total = engine.get_recommendations(
        tenant_id, entity_id=entity_id, entity_type=entity_type,
        status=status, limit=limit, offset=offset,
    )

    from app.modules.decision.schemas import (
        RecommendationAPI, AlternativeRecommendationAPI,
        EvidenceItemAPI, RiskAPI,
    )

    def _rec_to_api(rec):
        return RecommendationAPI(
            id=rec.id, action=rec.action, actionLabel=rec.action_label,
            reason=rec.reason, confidence=rec.confidence,
            confidenceLabel=rec.confidence_label, source=rec.source,
            priority=rec.priority, expectedRevenue=rec.expected_revenue,
            expectedEffort=rec.expected_effort, expectedTime=rec.expected_time,
            businessImpact=rec.business_impact,
            alternatives=[
                AlternativeRecommendationAPI(
                    action=a.action, actionLabel=a.action_label,
                    reason=a.reason, confidence=a.confidence,
                    expectedRevenue=a.expected_revenue,
                )
                for a in rec.alternatives
            ],
            evidence=[
                EvidenceItemAPI(
                    id=e.id, type=e.type, description=e.description,
                    source=e.source, confidence=e.confidence,
                    freshness=e.freshness, timestamp=e.timestamp,
                    severity=e.severity, url=e.url, data=e.data,
                )
                for e in rec.evidence
            ],
            risks=[
                RiskAPI(type=r.type, level=r.level, description=r.description, mitigation=r.mitigation)
                for r in rec.risks
            ],
            status=rec.status, createdAt=rec.created_at, updatedAt=rec.updated_at,
        )

    return RecommendationsResponseAPI(items=[_rec_to_api(r) for r in recs], total=total)


# ---------------------------------------------------------------------------
# Scores
# ---------------------------------------------------------------------------

@router.get("/scores", response_model=ScoresResponseAPI)
async def get_scores(
    tenant_id: str = Depends(get_current_tenant_id),
    entity_id: str = Query(...),
    entity_type: str = Query(...),
    _token: dict = Depends(verify_token),
):
    engine = _engine()
    scores = engine.get_scores(tenant_id, entity_id, entity_type)

    from app.modules.decision.schemas import ScoreAPI, ScoreFactorAPI
    api_scores = [
        ScoreAPI(
            type=s.type, value=s.value, confidence=s.confidence, label=s.label,
            factors=[
                ScoreFactorAPI(
                    name=f.name, value=f.value, weight=f.weight,
                    description=f.description, source=f.source,
                )
                for f in s.factors
            ],
            timestamp=s.timestamp,
        )
        for s in scores
    ]
    return ScoresResponseAPI(scores=api_scores)


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

@router.get("/evidence", response_model=EvidenceResponseAPI)
async def get_evidence(
    tenant_id: str = Depends(get_current_tenant_id),
    entity_id: str = Query(...),
    entity_type: str = Query(...),
    type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _token: dict = Depends(verify_token),
):
    engine = _engine()
    items, total = engine.get_evidence(
        tenant_id, entity_id, evidence_type=type, limit=limit, offset=offset,
    )

    from app.modules.decision.schemas import EvidenceItemAPI
    api_items = [
        EvidenceItemAPI(
            id=e.id, type=e.type, description=e.description,
            source=e.source, confidence=e.confidence,
            freshness=e.freshness, timestamp=e.timestamp,
            severity=e.severity, url=e.url, data=e.data,
        )
        for e in items
    ]
    return EvidenceResponseAPI(items=api_items, total=total)


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------

@router.post("/feedback", response_model=FeedbackSubmitResponseAPI)
async def submit_feedback(
    body: FeedbackRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    _token: dict = Depends(verify_token),
):
    if body.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch")

    from app.modules.decision.schemas import Feedback
    feedback = Feedback(
        decision_id=body.decision_id,
        tenant_id=body.tenant_id,
        actor_id=body.actor_id,
        outcome=body.outcome,
        reason=body.reason,
        revenue_impact=body.revenue_impact,
        time_to_execution=body.time_to_execution,
        actual_effort=body.actual_effort,
        metadata=body.metadata,
        timestamp=body.timestamp,
    )

    engine = _engine()
    fb_id, accepted = engine.submit_feedback(feedback)
    if not accepted:
        raise HTTPException(status_code=400, detail="Validation failed")

    return FeedbackSubmitResponseAPI(id=fb_id, accepted=True)


@router.get("/feedback/stats", response_model=FeedbackStatsAPI)
async def get_feedback_stats(
    tenant_id: str = Depends(get_current_tenant_id),
    _token: dict = Depends(verify_token),
):
    engine = _engine()
    stats = engine.get_feedback_stats(tenant_id)
    return FeedbackStatsAPI(
        total=stats.total,
        accepted=stats.accepted,
        rejected=stats.rejected,
        ignored=stats.ignored,
        acceptanceRate=stats.acceptance_rate,
        totalRevenueImpact=stats.total_revenue_impact,
        averageTimeToExecution=stats.average_time_to_execution,
    )


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

@router.get("/rules", response_model=RulesResponseAPI)
async def list_rules(
    category: Optional[str] = Query(None),
    _token: dict = Depends(verify_token),
):
    engine = _engine()
    rules = engine.list_rules(category=category)

    from app.modules.decision.schemas import DecisionRuleAPI
    api_rules = [
        DecisionRuleAPI(
            id=r.id, name=r.name, description=r.description,
            priority=r.priority, category=r.category, version=r.version,
            conditions=r.conditions, action=r.action, weight=r.weight,
        )
        for r in rules
    ]
    return RulesResponseAPI(rules=api_rules)


@router.post("/rules", response_model=DecisionRuleAPI, status_code=201)
async def create_rule(
    body: RuleCreateRequest,
    _token: dict = Depends(verify_token),
):
    import uuid
    rule_id = f"rule-{uuid.uuid4().hex[:12]}"
    rule = DecisionRule(
        id=rule_id,
        name=body.name,
        description=body.description,
        priority=body.priority,
        category=body.category,
        version=body.version,
        conditions=body.conditions,
        action=body.action,
        weight=body.weight,
    )

    engine = _engine()
    try:
        created = engine.create_rule(rule)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    from app.modules.decision.schemas import DecisionRuleAPI
    return DecisionRuleAPI(
        id=created.id, name=created.name, description=created.description,
        priority=created.priority, category=created.category, version=created.version,
        conditions=created.conditions, action=created.action, weight=created.weight,
    )


# ---------------------------------------------------------------------------
# Learning
# ---------------------------------------------------------------------------

@router.get("/learning/quality", response_model=QualityMetricsAPI)
async def get_learning_quality(
    tenant_id: str = Depends(get_current_tenant_id),
    _token: dict = Depends(verify_token),
):
    engine = _engine()
    metrics = engine.get_learning_quality(tenant_id)
    return QualityMetricsAPI(
        averageConfidence=metrics.average_confidence,
        averageAcceptanceRate=metrics.average_acceptance_rate,
        totalRecommendations=metrics.total_recommendations,
        highConfidenceRate=metrics.high_confidence_rate,
        mediumConfidenceRate=metrics.medium_confidence_rate,
        lowConfidenceRate=metrics.low_confidence_rate,
    )


@router.get("/learning/trends", response_model=LearningTrendsResponseAPI)
async def get_learning_trends(
    tenant_id: str = Depends(get_current_tenant_id),
    _token: dict = Depends(verify_token),
):
    engine = _engine()
    trends = engine.get_learning_trends(tenant_id)

    from app.modules.decision.schemas import LearningTrendAPI
    return LearningTrendsResponseAPI(
        trends=[
            LearningTrendAPI(
                metric=t.metric,
                currentValue=t.current_value,
                previousValue=t.previous_value,
                trend=t.trend,
                changePercent=t.change_percent,
            )
            for t in trends
        ]
    )
