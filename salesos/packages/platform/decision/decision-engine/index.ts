import type {
  DecisionContext,
  DecisionResult,
  DecisionHistoryItem,
  EvidenceItem,
  DecisionRule,
  Score,
  Recommendation,
  Explainability,
  DecisionStatus,
  ConfidenceLabel,
} from '../contracts'

function generateId(): string {
  return crypto.randomUUID()
}

function now(): string {
  return new Date().toISOString()
}

const BASE_RULES: DecisionRule[] = [
  {
    id: 'rule-high-intent',
    name: 'High Intent Signal',
    description: 'Trigger when entity shows strong buying intent',
    priority: 1,
    category: 'intent',
    version: '1.0.0',
    conditions: { signalStrength: 'high' },
    action: 'accelerate',
    weight: 0.9,
  },
  {
    id: 'rule-risk-check',
    name: 'Risk Assessment',
    description: 'Evaluate risk level for the entity',
    priority: 2,
    category: 'risk',
    version: '1.0.0',
    conditions: { entityType: ['company', 'opportunity'] },
    action: 'assess_risk',
    weight: 0.7,
  },
  {
    id: 'rule-engagement',
    name: 'Engagement Recency',
    description: 'Check how recently the entity was engaged',
    priority: 3,
    category: 'engagement',
    version: '1.0.0',
    conditions: { maxDaysSinceContact: 30 },
    action: 're_engage',
    weight: 0.5,
  },
  {
    id: 'rule-data-quality',
    name: 'Data Quality Gate',
    description: 'Ensure minimum data quality before action',
    priority: 0,
    category: 'quality',
    version: '1.0.0',
    conditions: { minConfidence: 0.3 },
    action: 'validate',
    weight: 1.0,
  },
]

function collectEvidence(context: DecisionContext): EvidenceItem[] {
  const evidence: EvidenceItem[] = []
  const ts = now()

  if (context.metadata) {
    for (const [key, value] of Object.entries(context.metadata)) {
      if (value !== null && value !== undefined) {
        evidence.push({
          id: generateId(),
          type: 'signal',
          description: `${key}: ${JSON.stringify(value)}`,
          source: 'context.metadata',
          confidence: 0.7,
          freshness: 'current',
          timestamp: ts,
          data: { key, rawValue: value },
        })
      }
    }
  }

  if (context.entityType) {
    evidence.push({
      id: generateId(),
      type: 'document',
      description: `Entity type identified: ${context.entityType}`,
      source: 'context.entityType',
      confidence: 1.0,
      freshness: 'current',
      timestamp: ts,
      data: { entityType: context.entityType },
    })
  }

  if (context.companyId) {
    evidence.push({
      id: generateId(),
      type: 'company',
      description: `Company context provided: ${context.companyId}`,
      source: 'context.companyId',
      confidence: 1.0,
      freshness: 'current',
      timestamp: ts,
      data: { companyId: context.companyId },
    })
  }

  if (context.opportunityId) {
    evidence.push({
      id: generateId(),
      type: 'timeline',
      description: `Opportunity context provided: ${context.opportunityId}`,
      source: 'context.opportunityId',
      confidence: 1.0,
      freshness: 'current',
      timestamp: ts,
      data: { opportunityId: context.opportunityId },
    })
  }

  if (evidence.length === 0) {
    evidence.push({
      id: generateId(),
      type: 'search',
      description: 'No contextual evidence available — default evaluation',
      source: 'decision-engine.default',
      confidence: 0.3,
      freshness: 'stale',
      timestamp: ts,
    })
  }

  return evidence
}

function applyRules(context: DecisionContext, evidence: EvidenceItem[]): DecisionRule[] {
  const applied: DecisionRule[] = []

  for (const rule of BASE_RULES) {
    if (rule.category === 'quality') {
      applied.push(rule)
      continue
    }

    if (rule.category === 'intent') {
      const hasHighIntent = evidence.some(
        (e) =>
          e.data &&
          typeof e.data === 'object' &&
          'strength' in (e.data as Record<string, unknown>) &&
          (e.data as Record<string, unknown>).strength === 'high'
      )
      if (hasHighIntent || evidence.length > 3) {
        applied.push(rule)
      }
      continue
    }

    if (rule.category === 'risk') {
      if (context.entityType === 'company' || context.entityType === 'opportunity') {
        applied.push(rule)
      }
      continue
    }

    if (rule.category === 'engagement') {
      applied.push(rule)
      continue
    }
  }

  return applied.sort((a, b) => b.priority - a.priority || b.weight - a.weight)
}

function computeScores(
  context: DecisionContext,
  evidence: EvidenceItem[],
  rulesApplied: DecisionRule[]
): Score[] {
  const ts = now()
  const scores: Score[] = []

  const evidenceConfidence =
    evidence.length > 0
      ? evidence.reduce((sum, e) => sum + e.confidence, 0) / evidence.length
      : 0

  const ruleWeight =
    rulesApplied.length > 0
      ? rulesApplied.reduce((sum, r) => sum + r.weight, 0) / rulesApplied.length
      : 0

  const combinedScore = Math.round((evidenceConfidence * 0.6 + ruleWeight * 0.4) * 100) / 100

  scores.push({
    type: 'confidence',
    value: combinedScore,
    confidence: evidenceConfidence,
    label: combinedScore >= 0.7 ? 'High' : combinedScore >= 0.4 ? 'Medium' : 'Low',
    factors: [
      {
        name: 'evidence_strength',
        value: evidenceConfidence,
        weight: 0.6,
        description: 'Average confidence of collected evidence items',
        source: 'decision-engine.evidence',
      },
      {
        name: 'rule_alignment',
        value: ruleWeight,
        weight: 0.4,
        description: 'Average weight of applicable rules',
        source: 'decision-engine.rules',
      },
    ],
    timestamp: ts,
  })

  if (context.entityType === 'company' || !context.entityType) {
    scores.push({
      type: 'company',
      value: combinedScore,
      confidence: evidenceConfidence,
      label: combinedScore >= 0.7 ? 'Strong' : combinedScore >= 0.4 ? 'Moderate' : 'Weak',
      factors: [
        {
          name: 'context_completeness',
          value: evidence.length > 2 ? 0.8 : evidence.length > 0 ? 0.5 : 0.2,
          weight: 0.5,
          description: 'Completeness of available context',
          source: 'decision-engine.context',
        },
        {
          name: 'entity_type_match',
          value: context.entityType ? 1.0 : 0.3,
          weight: 0.5,
          description: 'Whether entity type is specified',
          source: 'decision-engine.context',
        },
      ],
      timestamp: ts,
    })
  }

  if (context.entityType === 'opportunity') {
    scores.push({
      type: 'revenue',
      value: Math.min(combinedScore * 1.1, 1.0),
      confidence: evidenceConfidence * 0.9,
      label: combinedScore >= 0.7 ? 'High potential' : 'Moderate potential',
      factors: [
        {
          name: 'opportunity_signals',
          value: combinedScore,
          weight: 0.7,
          description: 'Signals indicating revenue potential',
          source: 'decision-engine.scoring',
        },
        {
          name: 'risk_adjustment',
          value: 1 - ruleWeight * 0.3,
          weight: 0.3,
          description: 'Risk-adjusted revenue factor',
          source: 'decision-engine.risk',
        },
      ],
      timestamp: ts,
    })
  }

  if (context.entityType === 'person') {
    scores.push({
      type: 'relationship',
      value: combinedScore,
      confidence: evidenceConfidence,
      label: combinedScore >= 0.7 ? 'Strong' : combinedScore >= 0.4 ? 'Developing' : 'Weak',
      factors: [
        {
          name: 'engagement_level',
          value: evidenceConfidence,
          weight: 0.6,
          description: 'Level of engagement signals',
          source: 'decision-engine.evidence',
        },
        {
          name: 'recency',
          value: 0.7,
          weight: 0.4,
          description: 'Recency of interactions',
          source: 'decision-engine.timeline',
        },
      ],
      timestamp: ts,
    })
  }

  return scores
}

function generateRecommendation(
  context: DecisionContext,
  evidence: EvidenceItem[],
  scores: Score[],
  rulesApplied: DecisionRule[],
  decisionId: string
): Recommendation {
  const ts = now()
  const confidenceScore = scores.find((s) => s.type === 'confidence')
  const value = confidenceScore?.value ?? 0.5
  const confidenceLabel: ConfidenceLabel = value >= 0.7 ? 'high' : value >= 0.4 ? 'medium' : 'low'

  let action: string
  let actionLabel: string

  if (value >= 0.7) {
    action = 'pursue'
    actionLabel = 'Pursue Immediately'
  } else if (value >= 0.4) {
    action = 'nurture'
    actionLabel = 'Nurture & Monitor'
  } else {
    action = 'deprioritize'
    actionLabel = 'Deprioritize'
  }

  if (context.entityType === 'opportunity' && value >= 0.6) {
    action = 'accelerate'
    actionLabel = 'Accelerate Deal'
  }

  const risks: { type: string; level: 'critical' | 'high' | 'medium' | 'low'; description: string; mitigation?: string }[] = []
  if (value < 0.4) {
    risks.push({
      type: 'low_confidence',
      level: 'high',
      description: 'Low overall confidence in the decision',
      mitigation: 'Gather more evidence before proceeding',
    })
  }
  if (evidence.length < 2) {
    risks.push({
      type: 'insufficient_data',
      level: 'medium',
      description: 'Limited evidence available for this decision',
      mitigation: 'Collect additional data points',
    })
  }
  if (rulesApplied.length === 0) {
    risks.push({
      type: 'no_rules_matched',
      level: 'medium',
      description: 'No business rules matched this context',
      mitigation: 'Review rule configuration',
    })
  }

  const alternatives: { action: string; actionLabel: string; reason: string; confidence: number }[] = []
  if (action !== 'pursue' && action !== 'accelerate') {
    alternatives.push({
      action: 'pursue',
      actionLabel: 'Pursue',
      reason: 'If additional evidence is gathered, pursuing may become viable',
      confidence: Math.min(value + 0.2, 1.0),
    })
  }
  if (action !== 'deprioritize') {
    alternatives.push({
      action: 'deprioritize',
      actionLabel: 'Deprioritize',
      reason: 'Conservative approach to focus resources elsewhere',
      confidence: 1.0 - value,
    })
  }
  alternatives.push({
    action: 'gather_evidence',
    actionLabel: 'Gather More Evidence',
    reason: 'Delay decision until more data is available',
    confidence: 0.6,
  })

  return {
    id: decisionId,
    action,
    actionLabel,
    reason: `Based on ${evidence.length} evidence items and ${rulesApplied.length} rules, the combined score is ${Math.round(value * 100)}%.`,
    confidence: value,
    confidenceLabel,
    source: rulesApplied.length > 0 ? 'hybrid' : 'rule',
    priority: value >= 0.7 ? 1 : value >= 0.4 ? 2 : 3,
    businessImpact: `Impact level: ${value >= 0.7 ? 'High' : value >= 0.4 ? 'Medium' : 'Low'}`,
    alternatives,
    evidence,
    risks,
    status: 'pending' as DecisionStatus,
    createdAt: ts,
    updatedAt: ts,
  }
}

function buildExplainability(
  context: DecisionContext,
  evidence: EvidenceItem[],
  rulesApplied: DecisionRule[],
  recommendation: Recommendation,
  scores: Score[]
): Explainability {
  const confidenceScore = scores.find((s) => s.type === 'confidence')
  const value = confidenceScore?.value ?? 0.5
  const riskLevel: 'critical' | 'high' | 'medium' | 'low' =
    value >= 0.7 ? 'low' : value >= 0.4 ? 'medium' : 'high'

  const whyParts: string[] = []
  if (evidence.length > 0) {
    whyParts.push(`${evidence.length} evidence items were collected from context`)
  }
  if (rulesApplied.length > 0) {
    whyParts.push(`${rulesApplied.length} business rules matched`)
  }

  return {
    why: whyParts.length > 0 ? whyParts.join('; ') : 'Limited context available — default evaluation applied',
    whyNow: `Decision requested at ${now()} for entity ${context.entityId ?? context.entityType ?? 'unknown'}`,
    whyThisAction: `The '${recommendation.action}' action was recommended with ${Math.round(recommendation.confidence * 100)}% confidence based on combined scoring`,
    whyNotAlternative: recommendation.alternatives.map((a) => `${a.actionLabel}: confidence ${Math.round(a.confidence * 100)}% — ${a.reason}`),
    evidence,
    rulesApplied,
    aiReasoning: null,
    confidence: value,
    risk: riskLevel,
    expectedImpact: {
      revenue: Math.round(value * 100000),
      timeframe: value >= 0.7 ? '30 days' : value >= 0.4 ? '90 days' : '180+ days',
    },
  }
}

export class DecisionEngine {
  private history: Map<string, DecisionResult> = new Map()
  private historyByTenant: Map<string, string[]> = new Map()

  async evaluate(context: DecisionContext): Promise<DecisionResult> {
    const decisionId = generateId()
    const evaluationStart = performance.now()

    const evidenceStart = performance.now()
    const evidence = collectEvidence(context)
    const evidenceTimeMs = Math.round(performance.now() - evidenceStart)

    const rulesStart = performance.now()
    const rulesApplied = applyRules(context, evidence)
    const rulesTimeMs = Math.round(performance.now() - rulesStart)

    const scoringStart = performance.now()
    const scores = computeScores(context, evidence, rulesApplied)
    const scoringTimeMs = Math.round(performance.now() - scoringStart)

    const recommendationStart = performance.now()
    const recommendation = generateRecommendation(context, evidence, scores, rulesApplied, decisionId)
    const recommendationTimeMs = Math.round(performance.now() - recommendationStart)

    const explainability = buildExplainability(context, evidence, rulesApplied, recommendation, scores)

    const result: DecisionResult = {
      decisionId,
      context,
      recommendation,
      scores,
      rulesApplied,
      evidence,
      explainability,
      telemetry: {
        evaluationTimeMs: Math.round(performance.now() - evaluationStart),
        rulesTimeMs,
        scoringTimeMs,
        evidenceTimeMs,
        recommendationTimeMs,
      },
      timestamp: now(),
    }

    this.history.set(decisionId, result)
    const tenantDecisions = this.historyByTenant.get(context.tenantId) ?? []
    tenantDecisions.push(decisionId)
    this.historyByTenant.set(context.tenantId, tenantDecisions)

    return result
  }

  async evaluateBatch(contexts: DecisionContext[]): Promise<DecisionResult[]> {
    const results: DecisionResult[] = []
    for (const context of contexts) {
      results.push(await this.evaluate(context))
    }
    return results
  }

  async explain(decisionId: string): Promise<Explainability | null> {
    const result = this.history.get(decisionId)
    return result?.explainability ?? null
  }

  async getHistory(tenantId: string, limit?: number): Promise<DecisionHistoryItem[]> {
    const ids = this.historyByTenant.get(tenantId) ?? []
    const sliced = limit ? ids.slice(-limit) : ids

    return sliced
      .map((id) => this.history.get(id))
      .filter((r): r is DecisionResult => r !== undefined)
      .map((r) => ({
        decisionId: r.decisionId,
        context: r.context,
        recommendation: {
          action: r.recommendation.action,
          actionLabel: r.recommendation.actionLabel,
          confidence: r.recommendation.confidence,
        },
        outcome: null,
        revenueImpact: null,
        createdAt: r.timestamp,
        updatedAt: r.timestamp,
      }))
  }
}

export const decisionEngine = new DecisionEngine()
