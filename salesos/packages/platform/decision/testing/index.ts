import type {
  DecisionContext, EvidenceItem, DecisionRule, Score, Recommendation,
  Feedback, LearningEvent, Explainability, DecisionResult,
} from '../contracts'

export function createMockContext(overrides: Partial<DecisionContext> = {}): DecisionContext {
  return {
    tenantId: 'tenant_test',
    actorId: 'actor_test',
    entityId: 'entity_test',
    entityType: 'company',
    ...overrides,
  }
}

export function createMockEvidence(overrides: Partial<EvidenceItem> = {}): EvidenceItem {
  return {
    id: `evt_test_${Date.now()}`,
    type: 'signal',
    description: 'Test evidence item',
    source: 'test',
    confidence: 0.85,
    freshness: '2h ago',
    timestamp: new Date().toISOString(),
    ...overrides,
  }
}

export function createMockRule(overrides: Partial<DecisionRule> = {}): DecisionRule {
  return {
    id: `rule_test_${Date.now()}`,
    name: 'Test Rule',
    description: 'A test rule for unit testing',
    priority: 50,
    category: 'test',
    version: '1.0.0',
    conditions: { type: 'test' },
    action: 'flag',
    weight: 1.0,
    ...overrides,
  }
}

export function createMockScore(overrides: Partial<Score> = {}): Score {
  return {
    type: 'company',
    value: 0.75,
    confidence: 0.85,
    label: 'good',
    factors: [{ name: 'test_factor', value: 0.75, weight: 1.0, description: 'Test factor', source: 'test' }],
    timestamp: new Date().toISOString(),
    ...overrides,
  }
}

export function createMockRecommendation(overrides: Partial<Recommendation> = {}): Recommendation {
  return {
    id: `rec_test_${Date.now()}`,
    action: 'meeting',
    actionLabel: 'ترتيب اجتماع',
    reason: 'Test recommendation reason',
    confidence: 0.85,
    confidenceLabel: 'high',
    source: 'rule',
    priority: 1,
    expectedRevenue: 500000,
    evidence: [createMockEvidence()],
    risks: [{ type: 'test', level: 'low', description: 'Test risk' }],
    alternatives: [{ action: 'call', actionLabel: 'اتصال', reason: 'Alternative', confidence: 0.6 }],
    status: 'pending',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    ...overrides,
  }
}

export function createMockFeedback(overrides: Partial<Feedback> = {}): Feedback {
  return {
    decisionId: 'dec_test',
    tenantId: 'tenant_test',
    actorId: 'actor_test',
    outcome: 'accepted',
    timestamp: new Date().toISOString(),
    ...overrides,
  }
}

export function createMockLearningEvent(overrides: Partial<LearningEvent> = {}): LearningEvent {
  return {
    id: `learn_test_${Date.now()}`,
    type: 'recommendation_quality',
    decisionId: 'dec_test',
    metric: 'confidence',
    value: 0.85,
    factors: {},
    timestamp: new Date().toISOString(),
    ...overrides,
  }
}

export function createMockDecisionResult(overrides: Partial<DecisionResult> = {}): DecisionResult {
  const now = new Date().toISOString()
  const ctx = createMockContext()
  const rec = createMockRecommendation()
  return {
    decisionId: `dec_test_${Date.now()}`,
    context: ctx,
    recommendation: rec,
    scores: [createMockScore()],
    rulesApplied: [createMockRule()],
    evidence: [createMockEvidence()],
    explainability: {
      why: 'Test explanation',
      whyNow: 'Test why now',
      whyThisAction: 'Test why this action',
      whyNotAlternative: ['Test why not'],
      evidence: [createMockEvidence()],
      rulesApplied: [createMockRule()],
      aiReasoning: null,
      confidence: 0.85,
      risk: 'low',
      expectedImpact: { revenue: 500000, timeframe: '2 weeks' },
    },
    telemetry: {
      evaluationTimeMs: 10,
      rulesTimeMs: 2,
      scoringTimeMs: 3,
      evidenceTimeMs: 4,
      recommendationTimeMs: 1,
    },
    timestamp: now,
    ...overrides,
  }
}

export function assertValidRecommendation(rec: Recommendation): void {
  expect(rec).toBeDefined()
  expect(typeof rec.id).toBe('string')
  expect(typeof rec.action).toBe('string')
  expect(typeof rec.confidence).toBe('number')
  expect(rec.confidence).toBeGreaterThanOrEqual(0)
  expect(rec.confidence).toBeLessThanOrEqual(1)
  expect(['high', 'medium', 'low']).toContain(rec.confidenceLabel)
  expect(typeof rec.reason).toBe('string')
  expect(Array.isArray(rec.alternatives)).toBe(true)
  expect(Array.isArray(rec.evidence)).toBe(true)
  expect(Array.isArray(rec.risks)).toBe(true)
}

export function assertValidScore(score: Score): void {
  expect(score).toBeDefined()
  expect(typeof score.value).toBe('number')
  expect(score.value).toBeGreaterThanOrEqual(0)
  expect(score.value).toBeLessThanOrEqual(1)
  expect(Array.isArray(score.factors)).toBe(true)
  expect(score.factors.length).toBeGreaterThan(0)
}

export function assertValidExplainability(exp: Explainability): void {
  expect(exp).toBeDefined()
  expect(typeof exp.why).toBe('string')
  expect(typeof exp.whyNow).toBe('string')
  expect(typeof exp.whyThisAction).toBe('string')
  expect(Array.isArray(exp.whyNotAlternative)).toBe(true)
  expect(Array.isArray(exp.evidence)).toBe(true)
  expect(Array.isArray(exp.rulesApplied)).toBe(true)
  expect(typeof exp.confidence).toBe('number')
}
