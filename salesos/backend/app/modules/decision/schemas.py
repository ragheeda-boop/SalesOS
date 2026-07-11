from pydantic import BaseModel, Field
from typing import Optional, Literal, Any
from datetime import datetime
from decimal import Decimal


DecisionStatus = Literal["pending", "accepted", "dismissed", "completed", "failed"]
ConfidenceLabel = Literal["high", "medium", "low"]
DecisionSource = Literal["rule", "ai", "hybrid"]
SignalSeverity = Literal["critical", "high", "medium", "low"]
RiskLevel = Literal["critical", "high", "medium", "low"]
EvidenceType = Literal["signal", "document", "timeline", "dna", "meeting", "email", "search", "government"]
ScoreType = Literal["company", "opportunity", "intent", "relationship", "risk", "revenue", "data_quality", "confidence"]
OutcomeValue = Literal["accepted", "rejected", "ignored"]
EntityType = Literal["company", "opportunity", "person"]
LearningEventType = Literal["recommendation_quality", "acceptance_rate", "rule_effectiveness", "signal_usefulness", "evidence_quality"]


# --- Request Schemas ---

class DecisionContext(BaseModel):
    tenant_id: str
    actor_id: str
    entity_id: Optional[str] = None
    entity_type: Optional[EntityType] = None
    opportunity_id: Optional[str] = None
    company_id: Optional[str] = None
    signal_id: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class FeedbackRequest(BaseModel):
    decision_id: str
    tenant_id: str
    actor_id: str
    outcome: OutcomeValue
    reason: Optional[str] = None
    revenue_impact: Optional[float] = None
    time_to_execution: Optional[float] = None
    actual_effort: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    timestamp: str


class RuleCreateRequest(BaseModel):
    name: str
    description: str
    priority: int
    category: str
    version: str
    conditions: dict[str, Any]
    action: str
    weight: float = Field(ge=0.0, le=1.0)


# --- Evidence & Rules ---

class EvidenceItem(BaseModel):
    id: str
    type: EvidenceType
    description: str
    source: str
    confidence: float
    freshness: str
    timestamp: str
    severity: Optional[SignalSeverity] = None
    url: Optional[str] = None
    data: Optional[dict[str, Any]] = None


class DecisionRule(BaseModel):
    id: str
    name: str
    description: str
    priority: int
    category: str
    version: str
    conditions: dict[str, Any]
    action: str
    weight: float


# --- Scores ---

class ScoreFactor(BaseModel):
    name: str
    value: float
    weight: float
    description: str
    source: str


class Score(BaseModel):
    type: ScoreType
    value: float
    confidence: float
    label: str
    factors: list[ScoreFactor]
    timestamp: str


# --- Recommendation ---

class AlternativeRecommendation(BaseModel):
    action: str
    action_label: str
    reason: str
    confidence: float
    expected_revenue: Optional[float] = None


class Risk(BaseModel):
    type: str
    level: RiskLevel
    description: str
    mitigation: Optional[str] = None


class Recommendation(BaseModel):
    id: str
    action: str
    action_label: str
    reason: str
    confidence: float
    confidence_label: ConfidenceLabel
    source: DecisionSource
    priority: int
    expected_revenue: Optional[float] = None
    expected_effort: Optional[str] = None
    expected_time: Optional[str] = None
    business_impact: Optional[str] = None
    alternatives: list[AlternativeRecommendation]
    evidence: list[EvidenceItem]
    risks: list[Risk]
    status: DecisionStatus
    created_at: str
    updated_at: str


# --- Explainability ---

class ExpectedImpact(BaseModel):
    revenue: float
    timeframe: str


class Explainability(BaseModel):
    why: str
    why_now: str
    why_this_action: str
    why_not_alternative: list[str]
    evidence: list[EvidenceItem]
    rules_applied: list[DecisionRule]
    ai_reasoning: Optional[str] = None
    confidence: float
    risk: RiskLevel
    expected_impact: ExpectedImpact


# --- Telemetry ---

class Telemetry(BaseModel):
    evaluation_time_ms: float
    rules_time_ms: float
    scoring_time_ms: float
    evidence_time_ms: float
    recommendation_time_ms: float


# --- Decision Result ---

class DecisionResult(BaseModel):
    decision_id: str
    context: DecisionContext
    recommendation: Recommendation
    scores: list[Score]
    rules_applied: list[DecisionRule]
    evidence: list[EvidenceItem]
    explainability: Explainability
    telemetry: Telemetry
    timestamp: str


# --- History ---

class DecisionHistoryRecommendation(BaseModel):
    action: str
    action_label: str
    confidence: float


class DecisionHistoryItem(BaseModel):
    decision_id: str
    context: DecisionContext
    recommendation: DecisionHistoryRecommendation
    outcome: Optional[OutcomeValue] = None
    revenue_impact: Optional[float] = None
    created_at: str
    updated_at: str


# --- Feedback ---

class Feedback(BaseModel):
    decision_id: str
    tenant_id: str
    actor_id: str
    outcome: OutcomeValue
    reason: Optional[str] = None
    revenue_impact: Optional[float] = None
    time_to_execution: Optional[float] = None
    actual_effort: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    timestamp: str


class FeedbackRecord(BaseModel):
    id: str
    decision_id: str
    tenant_id: str
    actor_id: str
    outcome: OutcomeValue
    reason: Optional[str] = None
    revenue_impact: Optional[float] = None
    time_to_execution: Optional[float] = None
    actual_effort: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    timestamp: str
    created_at: str


class FeedbackStats(BaseModel):
    total: int
    accepted: int
    rejected: int
    ignored: int
    acceptance_rate: float
    total_revenue_impact: float
    average_time_to_execution: Optional[float] = None


# --- Learning ---

class LearningEvent(BaseModel):
    id: str
    type: LearningEventType
    decision_id: str
    metric: str
    value: float
    factors: dict[str, float]
    timestamp: str


class QualityMetrics(BaseModel):
    average_confidence: float
    average_acceptance_rate: float
    total_recommendations: int
    high_confidence_rate: float
    medium_confidence_rate: float
    low_confidence_rate: float


class LearningTrend(BaseModel):
    metric: str
    current_value: float
    previous_value: float
    trend: Literal["up", "down", "stable"]
    change_percent: float


# --- Batch ---

class BatchSummary(BaseModel):
    total: int
    succeeded: int
    failed: int
    total_time_ms: float


class BatchResponse(BaseModel):
    results: list[DecisionResult]
    summary: BatchSummary


# --- Response Wrappers ---

class ExplainResponse(BaseModel):
    decision_id: str
    explainability: Explainability


class HistoryResponse(BaseModel):
    items: list[DecisionHistoryItem]
    total: int


class RecommendationsResponse(BaseModel):
    items: list[Recommendation]
    total: int


class ScoresResponse(BaseModel):
    scores: list[Score]


class EvidenceResponse(BaseModel):
    items: list[EvidenceItem]
    total: int


class FeedbackSubmitResponse(BaseModel):
    id: str
    accepted: bool


class RulesResponse(BaseModel):
    rules: list[DecisionRule]


class LearningTrendsResponse(BaseModel):
    trends: list[LearningTrend]


# --- API Mapping Aliases (camelCase responses) ---

class RecommendationAPI(BaseModel):
    id: str
    action: str
    actionLabel: str
    reason: str
    confidence: float
    confidenceLabel: ConfidenceLabel
    source: DecisionSource
    priority: int
    expectedRevenue: Optional[float] = None
    expectedEffort: Optional[str] = None
    expectedTime: Optional[str] = None
    businessImpact: Optional[str] = None
    alternatives: list["AlternativeRecommendationAPI"]
    evidence: list["EvidenceItemAPI"]
    risks: list["RiskAPI"]
    status: DecisionStatus
    createdAt: str
    updatedAt: str


class AlternativeRecommendationAPI(BaseModel):
    action: str
    actionLabel: str
    reason: str
    confidence: float
    expectedRevenue: Optional[float] = None


class RiskAPI(BaseModel):
    type: str
    level: RiskLevel
    description: str
    mitigation: Optional[str] = None


class EvidenceItemAPI(BaseModel):
    id: str
    type: EvidenceType
    description: str
    source: str
    confidence: float
    freshness: str
    timestamp: str
    severity: Optional[SignalSeverity] = None
    url: Optional[str] = None
    data: Optional[dict[str, Any]] = None


class ScoreFactorAPI(BaseModel):
    name: str
    value: float
    weight: float
    description: str
    source: str


class ScoreAPI(BaseModel):
    type: ScoreType
    value: float
    confidence: float
    label: str
    factors: list[ScoreFactorAPI]
    timestamp: str


class DecisionRuleAPI(BaseModel):
    id: str
    name: str
    description: str
    priority: int
    category: str
    version: str
    conditions: dict[str, Any]
    action: str
    weight: float


class ExpectedImpactAPI(BaseModel):
    revenue: float
    timeframe: str


class ExplainabilityAPI(BaseModel):
    why: str
    whyNow: str
    whyThisAction: str
    whyNotAlternative: list[str]
    evidence: list[EvidenceItemAPI]
    rulesApplied: list[DecisionRuleAPI]
    aiReasoning: Optional[str] = None
    confidence: float
    risk: RiskLevel
    expectedImpact: ExpectedImpactAPI


class TelemetryAPI(BaseModel):
    evaluationTimeMs: float
    rulesTimeMs: float
    scoringTimeMs: float
    evidenceTimeMs: float
    recommendationTimeMs: float


class DecisionContextAPI(BaseModel):
    tenantId: str
    actorId: str
    entityId: Optional[str] = None
    entityType: Optional[EntityType] = None
    opportunityId: Optional[str] = None
    companyId: Optional[str] = None
    signalId: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class DecisionResultAPI(BaseModel):
    decisionId: str
    context: DecisionContextAPI
    recommendation: RecommendationAPI
    scores: list[ScoreAPI]
    rulesApplied: list[DecisionRuleAPI]
    evidence: list[EvidenceItemAPI]
    explainability: ExplainabilityAPI
    telemetry: TelemetryAPI
    timestamp: str


class DecisionHistoryRecommendationAPI(BaseModel):
    action: str
    actionLabel: str
    confidence: float


class DecisionHistoryItemAPI(BaseModel):
    decisionId: str
    context: DecisionContextAPI
    recommendation: DecisionHistoryRecommendationAPI
    outcome: Optional[OutcomeValue] = None
    revenueImpact: Optional[float] = None
    createdAt: str
    updatedAt: str


class HistoryResponseAPI(BaseModel):
    items: list[DecisionHistoryItemAPI]
    total: int


class BatchSummaryAPI(BaseModel):
    total: int
    succeeded: int
    failed: int
    totalTimeMs: float


class BatchResponseAPI(BaseModel):
    results: list[DecisionResultAPI]
    summary: BatchSummaryAPI


class ExplainResponseAPI(BaseModel):
    decisionId: str
    explainability: ExplainabilityAPI


class FeedbackSubmitResponseAPI(BaseModel):
    id: str
    accepted: bool


class FeedbackStatsAPI(BaseModel):
    total: int
    accepted: int
    rejected: int
    ignored: int
    acceptanceRate: float
    totalRevenueImpact: float
    averageTimeToExecution: Optional[float] = None


class RulesResponseAPI(BaseModel):
    rules: list[DecisionRuleAPI]


class RecommendationsResponseAPI(BaseModel):
    items: list[RecommendationAPI]
    total: int


class ScoresResponseAPI(BaseModel):
    scores: list[ScoreAPI]


class EvidenceResponseAPI(BaseModel):
    items: list[EvidenceItemAPI]
    total: int


class LearningTrendAPI(BaseModel):
    metric: str
    currentValue: float
    previousValue: float
    trend: Literal["up", "down", "stable"]
    changePercent: float


class LearningTrendsResponseAPI(BaseModel):
    trends: list[LearningTrendAPI]


class QualityMetricsAPI(BaseModel):
    averageConfidence: float
    averageAcceptanceRate: float
    totalRecommendations: int
    highConfidenceRate: float
    mediumConfidenceRate: float
    lowConfidenceRate: float
