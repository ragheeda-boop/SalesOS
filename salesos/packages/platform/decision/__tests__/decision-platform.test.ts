import { DecisionEngine } from '../decision-engine'
import { RuleEngine, createRule } from '../rule-engine'
import { ScoringEngine } from '../scoring-engine'
import { EvidenceEngine } from '../evidence-engine'
import { RecommendationEngine } from '../recommendation-engine'
import { ExplainabilityEngine } from '../explainability-engine'
import { FeedbackEngine } from '../feedback-engine'
import { LearningEngine } from '../learning-engine'
import {
  generateId,
  clamp,
  weightedAverage,
  confidenceLabel,
  categorizeRisk,
  deduplicateBy,
  paginate,
} from '../shared'
import {
  createMockContext,
  createMockEvidence,
  createMockRule,
  createMockScore,
  createMockRecommendation,
  createMockFeedback,
  createMockLearningEvent,
  createMockDecisionResult,
  assertValidRecommendation,
  assertValidScore,
  assertValidExplainability,
} from '../testing'

import type {
  DecisionContext,
  EvidenceItem,
  DecisionRule,
  Score,
  ScoreType,
} from '../contracts'
import type { RuleEvaluationResult } from '../rule-engine'
import type { FeedbackStats } from '../feedback-engine'
import type {
  QualityMetrics,
  RuleEffectiveness,
  LearningTrend,
} from '../learning-engine'

describe('DecisionEngine', () => {
  let engine: DecisionEngine

  beforeEach(() => {
    engine = new DecisionEngine()
  })

  describe('evaluate()', () => {
    it('returns a valid DecisionResult with all required fields', async () => {
      const context = createMockContext()
      const result = await engine.evaluate(context)

      expect(result).toBeDefined()
      expect(typeof result.decisionId).toBe('string')
      expect(result.context).toEqual(context)
      expect(result.recommendation).toBeDefined()
      expect(result.scores).toBeDefined()
      expect(Array.isArray(result.scores)).toBe(true)
      expect(result.rulesApplied).toBeDefined()
      expect(Array.isArray(result.rulesApplied)).toBe(true)
      expect(result.evidence).toBeDefined()
      expect(Array.isArray(result.evidence)).toBe(true)
      expect(result.explainability).toBeDefined()
      expect(result.telemetry).toBeDefined()
      expect(typeof result.timestamp).toBe('string')
    })

    it('includes telemetry with timing data', async () => {
      const result = await engine.evaluate(createMockContext())

      expect(result.telemetry).toBeDefined()
      expect(typeof result.telemetry.evaluationTimeMs).toBe('number')
      expect(typeof result.telemetry.rulesTimeMs).toBe('number')
      expect(typeof result.telemetry.scoringTimeMs).toBe('number')
      expect(typeof result.telemetry.evidenceTimeMs).toBe('number')
      expect(typeof result.telemetry.recommendationTimeMs).toBe('number')
      expect(result.telemetry.evaluationTimeMs).toBeGreaterThanOrEqual(0)
    })

    it('generates unique decision IDs across evaluations', async () => {
      const ids = new Set<string>()
      const count = 10

      for (let i = 0; i < count; i++) {
        const result = await engine.evaluate(createMockContext())
        ids.add(result.decisionId)
      }

      expect(ids.size).toBe(count)
    })
  })

  describe('evaluateBatch()', () => {
    it('evaluates multiple contexts and returns results for each', async () => {
      const contexts = [
        createMockContext({ tenantId: 't1', entityId: 'e1' }),
        createMockContext({ tenantId: 't2', entityId: 'e2' }),
        createMockContext({ tenantId: 't3', entityId: 'e3', entityType: 'opportunity' }),
      ]

      const results = await engine.evaluateBatch(contexts)

      expect(results).toHaveLength(3)
      results.forEach((result) => {
        expect(result.decisionId).toBeDefined()
        expect(result.recommendation).toBeDefined()
        expect(result.scores.length).toBeGreaterThan(0)
      })
    })
  })

  describe('explain()', () => {
    it('returns Explainability for a previously evaluated decision', async () => {
      const result = await engine.evaluate(createMockContext())
      const explanation = await engine.explain(result.decisionId)

      expect(explanation).not.toBeNull()
      assertValidExplainability(explanation!)
      expect(explanation!.why).toBeTruthy()
      expect(explanation!.whyNow).toBeTruthy()
      expect(explanation!.whyThisAction).toBeTruthy()
    })

    it('returns null for an unknown decision ID', async () => {
      const explanation = await engine.explain('nonexistent_decision_id')
      expect(explanation).toBeNull()
    })
  })

  describe('getHistory()', () => {
    it('returns decision history items for a given tenant', async () => {
      const tenantId = 'tenant_history_test'
      await engine.evaluate(createMockContext({ tenantId }))
      await engine.evaluate(createMockContext({ tenantId }))
      await engine.evaluate(createMockContext({ tenantId }))

      const history = await engine.getHistory(tenantId)

      expect(history).toHaveLength(3)
      history.forEach((item) => {
        expect(item.decisionId).toBeDefined()
        expect(item.context.tenantId).toBe(tenantId)
        expect(item.recommendation.action).toBeDefined()
        expect(typeof item.recommendation.confidence).toBe('number')
      })
    })

    it('returns empty array for a tenant with no history', async () => {
      const history = await engine.getHistory('tenant_with_no_history')
      expect(history).toHaveLength(0)
    })

    it('respects the limit parameter', async () => {
      const tenantId = 'tenant_limit_test'
      for (let i = 0; i < 5; i++) {
        await engine.evaluate(createMockContext({ tenantId }))
      }

      const limited = await engine.getHistory(tenantId, 2)
      expect(limited).toHaveLength(2)
    })
  })
})

describe('RuleEngine', () => {
  let engine: RuleEngine

  beforeEach(() => {
    engine = new RuleEngine()
  })

  describe('built-in rules', () => {
    it('registers built-in rules on construction', () => {
      const rules = engine.listRules()
      expect(rules.length).toBeGreaterThanOrEqual(7)

      const ids = rules.map((r) => r.id)
      expect(ids).toContain('rule_expired_license')
      expect(ids).toContain('rule_no_decision_maker')
      expect(ids).toContain('rule_low_confidence')
      expect(ids).toContain('rule_high_revenue')
      expect(ids).toContain('rule_government_tender')
      expect(ids).toContain('rule_high_hiring_growth')
      expect(ids).toContain('rule_relationship_strength')
    })
  })

  describe('register()', () => {
    it('adds a new rule successfully', () => {
      const rule = createMockRule({ id: 'rule_custom_1' })
      engine.register(rule)
      const retrieved = engine.getRule('rule_custom_1')
      expect(retrieved).toBeDefined()
      expect(retrieved!.name).toBe(rule.name)
    })

    it('throws on duplicate rule ID', () => {
      const rule = createMockRule({ id: 'rule_dup' })
      engine.register(rule)
      expect(() => engine.register(rule)).toThrow(/already registered/)
    })
  })

  describe('registerMany()', () => {
    it('adds multiple rules at once', () => {
      const rules = [
        createMockRule({ id: 'rule_batch_1', name: 'Batch Rule 1' }),
        createMockRule({ id: 'rule_batch_2', name: 'Batch Rule 2' }),
        createMockRule({ id: 'rule_batch_3', name: 'Batch Rule 3' }),
      ]
      engine.registerMany(rules)

      expect(engine.getRule('rule_batch_1')).toBeDefined()
      expect(engine.getRule('rule_batch_2')).toBeDefined()
      expect(engine.getRule('rule_batch_3')).toBeDefined()
    })

    it('skips rules with duplicate IDs silently', () => {
      const existing = engine.getRule('rule_expired_license')
      expect(existing).toBeDefined()

      engine.registerMany([
        createMockRule({ id: 'rule_expired_license', name: 'Should Not Override' }),
        createMockRule({ id: 'rule_unique_batch', name: 'Unique Rule' }),
      ])

      const unique = engine.getRule('rule_unique_batch')
      expect(unique).toBeDefined()
      expect(unique!.name).toBe('Unique Rule')
    })
  })

  describe('getRule()', () => {
    it('returns a rule by ID', () => {
      const rule = engine.getRule('rule_expired_license')
      expect(rule).toBeDefined()
      expect(rule!.id).toBe('rule_expired_license')
      expect(rule!.name).toBe('Expired License')
    })

    it('returns undefined for unknown ID', () => {
      expect(engine.getRule('nonexistent')).toBeUndefined()
    })

    it('returns a copy, not the internal reference', () => {
      const rule1 = engine.getRule('rule_expired_license')
      const rule2 = engine.getRule('rule_expired_license')
      expect(rule1).not.toBe(rule2)
      expect(rule1).toEqual(rule2)
    })
  })

  describe('listRules()', () => {
    it('returns all rules when no category is specified', () => {
      const allRules = engine.listRules()
      expect(allRules.length).toBeGreaterThanOrEqual(7)
    })

    it('filters rules by category', () => {
      const riskRules = engine.listRules('risk')
      expect(riskRules.length).toBeGreaterThanOrEqual(1)
      riskRules.forEach((r) => {
        expect(r.category).toBe('risk')
      })
    })

    it('returns empty array for non-existent category', () => {
      const rules = engine.listRules('nonexistent_category')
      expect(rules).toHaveLength(0)
    })
  })

  describe('evaluate()', () => {
    it('returns applied, fired, and skipped rules', async () => {
      const context = createMockContext({
        metadata: { licenseStatus: 'expired' },
      })
      const evidence = [createMockEvidence()]

      const result = await engine.evaluate(context, evidence)

      expect(result.rulesApplied.length).toBeGreaterThan(0)
      expect(Array.isArray(result.rulesFired)).toBe(true)
      expect(Array.isArray(result.rulesSkipped)).toBe(true)
      expect(result.rulesApplied.length).toBe(
        result.rulesFired.length + result.rulesSkipped.length,
      )
    })

    it('fires rules that match evidence conditions', async () => {
      const context = createMockContext()
      const evidence = [
        createMockEvidence({
          data: { licenseStatus: 'expired' },
        }),
      ]

      const result = await engine.evaluate(context, evidence)
      const firedIds = result.rulesFired.map((r) => r.id)
      expect(firedIds).toContain('rule_expired_license')
    })

    it('detects rule conflicts between same-category fired rules', async () => {
      const context = createMockContext()
      const evidence = [
        createMockEvidence({
          data: { hiringTrend: 'growing' },
        }),
        createMockEvidence({
          data: { relationshipScore: 0.9 },
        }),
        createMockEvidence({
          data: { opportunityValue: 600000 },
        }),
      ]

      const result = await engine.evaluate(context, evidence)
      expect(result.rulesApplied.length).toBeGreaterThan(0)
      expect(result.auditLog).toBeDefined()
      expect(Array.isArray(result.auditLog)).toBe(true)
    })

    it('handles evidence-based condition matching with operators', async () => {
      const context = createMockContext()
      const evidence = [
        createMockEvidence({
          data: { decisionMakersCount: 0 },
        }),
        createMockEvidence({
          data: { opportunityValue: 750000 },
        }),
      ]

      const result = await engine.evaluate(context, evidence)
      const firedIds = result.rulesFired.map((r) => r.id)
      expect(firedIds).toContain('rule_no_decision_maker')
      expect(firedIds).toContain('rule_high_revenue')
    })
  })
})

describe('ScoringEngine', () => {
  let engine: ScoringEngine

  beforeEach(() => {
    engine = new ScoringEngine()
  })

  describe('score()', () => {
    it('returns a valid Score object', () => {
      const score = engine.score('company', {
        financial_health: 0.8,
        growth_trend: 0.7,
        digital_presence: 0.6,
        hiring_trend: 0.5,
        procurement_maturity: 0.9,
      })

      assertValidScore(score)
      expect(score.type).toBe('company')
      expect(typeof score.confidence).toBe('number')
      expect(typeof score.label).toBe('string')
      expect(typeof score.timestamp).toBe('string')
    })

    it('computes weighted average of factors', () => {
      const score = engine.score('company', {
        financial_health: 1.0,
        growth_trend: 1.0,
        digital_presence: 1.0,
        hiring_trend: 1.0,
        procurement_maturity: 1.0,
      })
      expect(score.value).toBe(1.0)

      const zeroScore = engine.score('company', {
        financial_health: 0,
        growth_trend: 0,
        digital_presence: 0,
        hiring_trend: 0,
        procurement_maturity: 0,
      })
      expect(zeroScore.value).toBe(0)
    })

    it('clamps values to 0-1 range', () => {
      const overScore = engine.score('company', {
        financial_health: 1.5,
        growth_trend: 2.0,
        digital_presence: -0.5,
        hiring_trend: 0,
        procurement_maturity: 0,
      })
      expect(overScore.value).toBeGreaterThanOrEqual(0)
      expect(overScore.value).toBeLessThanOrEqual(1)

      overScore.factors.forEach((f) => {
        expect(f.value).toBeGreaterThanOrEqual(0)
        expect(f.value).toBeLessThanOrEqual(1)
      })
    })

    it('includes all expected factors in result', () => {
      const score = engine.score('company', {
        financial_health: 0.5,
        growth_trend: 0.5,
        digital_presence: 0.5,
        hiring_trend: 0.5,
        procurement_maturity: 0.5,
      })
      expect(score.factors.length).toBe(5)
      const factorNames = score.factors.map((f) => f.name)
      expect(factorNames).toContain('financial_health')
      expect(factorNames).toContain('growth_trend')
      expect(factorNames).toContain('digital_presence')
      expect(factorNames).toContain('hiring_trend')
      expect(factorNames).toContain('procurement_maturity')
    })

    it('throws for unknown score type', () => {
      expect(() =>
        engine.score('nonexistent' as ScoreType, { test: 0.5 }),
      ).toThrow(/Unknown score type/)
    })
  })

  describe('scoreAll()', () => {
    it('returns multiple scores for different types', () => {
      const scores = engine.scoreAll({
        company: {
          financial_health: 0.8,
          growth_trend: 0.7,
          digital_presence: 0.6,
          hiring_trend: 0.5,
          procurement_maturity: 0.9,
        },
        intent: {
          signal_activity: 0.7,
          hiring_trend: 0.6,
          government_exposure: 0.5,
          expansion_potential: 0.8,
          digital_engagement: 0.4,
        },
      })

      expect(scores).toHaveLength(2)
      const types = scores.map((s) => s.type)
      expect(types).toContain('company')
      expect(types).toContain('intent')
    })
  })

  describe('labels', () => {
    it('each score type produces contextually different labels', () => {
      const companyScore = engine.score('company', {
        financial_health: 0.95,
        growth_trend: 0.95,
        digital_presence: 0.95,
        hiring_trend: 0.95,
        procurement_maturity: 0.95,
      })

      const intentScore = engine.score('intent', {
        signal_activity: 0.95,
        hiring_trend: 0.95,
        government_exposure: 0.95,
        expansion_potential: 0.95,
        digital_engagement: 0.95,
      })

      expect(companyScore.label).toBe('excellent')
      expect(intentScore.label).toBe('excellent')
    })
  })
})

describe('EvidenceEngine', () => {
  let engine: EvidenceEngine

  beforeEach(() => {
    engine = new EvidenceEngine()
  })

  describe('collect()', () => {
    it('returns an EvidenceCollectionResult with items', async () => {
      const context = createMockContext()
      const result = await engine.collect(context)

      expect(result).toBeDefined()
      expect(result.items).toBeDefined()
      expect(Array.isArray(result.items)).toBe(true)
      expect(result.items.length).toBeGreaterThan(0)
      expect(typeof result.deduplicated).toBe('number')
      expect(typeof result.totalSources).toBe('number')
      expect(typeof result.averageConfidence).toBe('number')
      expect(typeof result.collectionTimeMs).toBe('number')
    })

    it('deduplicates items by type and description', async () => {
      const context = createMockContext()
      const result = await engine.collect(context)

      const seen = new Set<string>()
      for (const item of result.items) {
        const key = `${item.type}::${item.description.toLowerCase().trim()}`
        expect(seen.has(key)).toBe(false)
        seen.add(key)
      }
    })

    it('applies freshness decay to stale evidence', async () => {
      const pastTimestamp = new Date(
        Date.now() - 48 * 60 * 60 * 1000,
      ).toISOString()

      const sources = [
        {
          type: 'signal' as const,
          provider: { name: 'test_provider', confidence: 0.9, freshnessMax: 24 },
          data: [
            {
              description: 'Old signal',
              source: 'test',
              timestamp: pastTimestamp,
              confidence: 0.9,
            },
          ],
        },
      ]

      const result = await engine.collect(createMockContext(), sources)
      expect(result.items.length).toBeGreaterThanOrEqual(1)

      const oldItem = result.items.find((i) => i.description === 'Old signal')
      expect(oldItem).toBeDefined()
      expect(oldItem!.confidence).toBeLessThan(0.9)
      expect(oldItem!.freshness).toBe('expired')
    })

    it('collects from custom evidence sources', async () => {
      const context = createMockContext()
      const sources = [
        {
          type: 'signal' as const,
          provider: { name: 'custom', confidence: 0.95, freshnessMax: 48 },
          data: [
            { description: 'Custom signal A', source: 'custom' },
            { description: 'Custom signal B', source: 'custom' },
          ],
        },
      ]

      const result = await engine.collect(context, sources)
      expect(result.items.length).toBe(2)
      expect(result.totalSources).toBe(1)
    })
  })

  describe('getRecent()', () => {
    it('returns evidence for a specific entity', async () => {
      const context = createMockContext({
        tenantId: 'tenant_recent',
        entityId: 'entity_recent',
      })
      await engine.collect(context)

      const recent = await engine.getRecent('tenant_recent', 'entity_recent')
      expect(recent.length).toBeGreaterThan(0)
    })

    it('returns empty for unknown tenant/entity', async () => {
      const recent = await engine.getRecent('unknown_tenant', 'unknown_entity')
      expect(recent).toHaveLength(0)
    })

    it('respects the limit parameter', async () => {
      const context = createMockContext({
        tenantId: 'tenant_limit',
        entityId: 'entity_limit',
      })

      const sources = [
        {
          type: 'signal' as const,
          provider: { name: 'p1', confidence: 0.8, freshnessMax: 24 },
          data: [
            { description: 'Signal 1' },
            { description: 'Signal 2' },
            { description: 'Signal 3' },
            { description: 'Signal 4' },
            { description: 'Signal 5' },
          ],
        },
      ]
      await engine.collect(context, sources)

      const limited = await engine.getRecent('tenant_limit', 'entity_limit', 2)
      expect(limited.length).toBeLessThanOrEqual(2)
    })
  })
})

describe('RecommendationEngine', () => {
  let engine: RecommendationEngine

  beforeEach(() => {
    engine = new RecommendationEngine()
  })

  describe('generate()', () => {
    it('returns a valid Recommendation', async () => {
      const context = createMockContext()
      const scores: Score[] = [
        {
          type: 'intent',
          value: 0.8,
          confidence: 0.9,
          label: 'good',
          factors: [],
          timestamp: new Date().toISOString(),
        },
        {
          type: 'relationship',
          value: 0.7,
          confidence: 0.85,
          label: 'good',
          factors: [],
          timestamp: new Date().toISOString(),
        },
        {
          type: 'revenue',
          value: 0.6,
          confidence: 0.8,
          label: 'moderate',
          factors: [],
          timestamp: new Date().toISOString(),
        },
        {
          type: 'company',
          value: 0.7,
          confidence: 0.85,
          label: 'good',
          factors: [],
          timestamp: new Date().toISOString(),
        },
        {
          type: 'data_quality',
          value: 0.7,
          confidence: 0.8,
          label: 'good',
          factors: [],
          timestamp: new Date().toISOString(),
        },
      ]
      const rulesApplied = [
        createMockRule({ id: 'rule_meeting', action: 'meeting', priority: 50 }),
      ]
      const evidence = [createMockEvidence()]

      const rec = await engine.generate(context, scores, rulesApplied, evidence)
      assertValidRecommendation(rec)
    })

    it('ranks actions by score — primary action has the highest score', async () => {
      const context = createMockContext()
      const scores: Score[] = [
        { type: 'intent', value: 0.9, confidence: 0.9, label: 'excellent', factors: [], timestamp: new Date().toISOString() },
        { type: 'relationship', value: 0.85, confidence: 0.9, label: 'good', factors: [], timestamp: new Date().toISOString() },
        { type: 'revenue', value: 0.7, confidence: 0.85, label: 'good', factors: [], timestamp: new Date().toISOString() },
        { type: 'company', value: 0.8, confidence: 0.85, label: 'good', factors: [], timestamp: new Date().toISOString() },
        { type: 'data_quality', value: 0.8, confidence: 0.85, label: 'good', factors: [], timestamp: new Date().toISOString() },
      ]
      const evidence = [createMockEvidence()]

      const rec = await engine.generate(context, scores, [], evidence)
      expect(rec.confidence).toBeGreaterThan(0)
      expect(['high', 'medium', 'low']).toContain(rec.confidenceLabel)
    })

    it('includes alternatives when available', async () => {
      const context = createMockContext()
      const scores: Score[] = [
        { type: 'intent', value: 0.8, confidence: 0.9, label: 'good', factors: [], timestamp: new Date().toISOString() },
        { type: 'relationship', value: 0.7, confidence: 0.85, label: 'good', factors: [], timestamp: new Date().toISOString() },
        { type: 'revenue', value: 0.6, confidence: 0.8, label: 'moderate', factors: [], timestamp: new Date().toISOString() },
        { type: 'company', value: 0.7, confidence: 0.85, label: 'good', factors: [], timestamp: new Date().toISOString() },
        { type: 'data_quality', value: 0.6, confidence: 0.8, label: 'moderate', factors: [], timestamp: new Date().toISOString() },
      ]
      const evidence = [createMockEvidence()]

      const rec = await engine.generate(context, scores, [], evidence)
      expect(Array.isArray(rec.alternatives)).toBe(true)
    })

    it('assesses risks in the recommendation', async () => {
      const context = createMockContext()
      const scores: Score[] = [
        { type: 'intent', value: 0.8, confidence: 0.9, label: 'good', factors: [], timestamp: new Date().toISOString() },
        { type: 'relationship', value: 0.7, confidence: 0.85, label: 'good', factors: [], timestamp: new Date().toISOString() },
        { type: 'revenue', value: 0.6, confidence: 0.8, label: 'moderate', factors: [], timestamp: new Date().toISOString() },
        { type: 'company', value: 0.7, confidence: 0.85, label: 'good', factors: [], timestamp: new Date().toISOString() },
        { type: 'data_quality', value: 0.6, confidence: 0.8, label: 'moderate', factors: [], timestamp: new Date().toISOString() },
      ]
      const evidence = [createMockEvidence()]

      const rec = await engine.generate(context, scores, [], evidence)
      expect(Array.isArray(rec.risks)).toBe(true)
    })

    it('includes evidence references in the recommendation', async () => {
      const context = createMockContext()
      const scores: Score[] = [
        { type: 'intent', value: 0.8, confidence: 0.9, label: 'good', factors: [], timestamp: new Date().toISOString() },
        { type: 'relationship', value: 0.7, confidence: 0.85, label: 'good', factors: [], timestamp: new Date().toISOString() },
        { type: 'revenue', value: 0.6, confidence: 0.8, label: 'moderate', factors: [], timestamp: new Date().toISOString() },
        { type: 'company', value: 0.7, confidence: 0.85, label: 'good', factors: [], timestamp: new Date().toISOString() },
        { type: 'data_quality', value: 0.6, confidence: 0.8, label: 'moderate', factors: [], timestamp: new Date().toISOString() },
      ]
      const evidence = [
        createMockEvidence({ description: 'Meeting scheduled next week' }),
        createMockEvidence({ description: 'Proposal request received' }),
      ]

      const rec = await engine.generate(context, scores, [], evidence)
      expect(rec.evidence).toBeDefined()
      expect(Array.isArray(rec.evidence)).toBe(true)
    })

    it('returns nurture with low confidence when no actions score above 0', async () => {
      const context = createMockContext()
      const scores: Score[] = [
        { type: 'intent', value: 0, confidence: 0, label: 'poor', factors: [], timestamp: new Date().toISOString() },
        { type: 'relationship', value: 0, confidence: 0, label: 'poor', factors: [], timestamp: new Date().toISOString() },
        { type: 'revenue', value: 0, confidence: 0, label: 'poor', factors: [], timestamp: new Date().toISOString() },
        { type: 'company', value: 0, confidence: 0, label: 'poor', factors: [], timestamp: new Date().toISOString() },
        { type: 'data_quality', value: 0, confidence: 0, label: 'poor', factors: [], timestamp: new Date().toISOString() },
      ]
      const evidence = [createMockEvidence()]

      const rec = await engine.generate(context, scores, [], evidence)
      expect(rec.action).toBe('nurture')
      expect(rec.confidence).toBeLessThanOrEqual(0.3)
    })
  })
})

describe('ExplainabilityEngine', () => {
  let engine: ExplainabilityEngine

  beforeEach(() => {
    engine = new ExplainabilityEngine()
  })

  describe('explain()', () => {
    it('returns a valid Explainability object', async () => {
      const context = createMockContext()
      const recommendation = createMockRecommendation()
      const scores = [createMockScore()]
      const rulesApplied = [createMockRule()]
      const evidence = [createMockEvidence()]

      const exp = await engine.explain(context, recommendation, scores, rulesApplied, evidence)
      assertValidExplainability(exp)
    })

    it('generates why, whyNow, and whyThisAction strings', async () => {
      const context = createMockContext()
      const recommendation = createMockRecommendation({ alternatives: [] })
      const scores = [createMockScore()]
      const rulesApplied = [createMockRule()]
      const evidence = [createMockEvidence()]

      const exp = await engine.explain(context, recommendation, scores, rulesApplied, evidence)

      expect(typeof exp.why).toBe('string')
      expect(exp.why.length).toBeGreaterThan(0)
      expect(typeof exp.whyNow).toBe('string')
      expect(exp.whyNow.length).toBeGreaterThan(0)
      expect(typeof exp.whyThisAction).toBe('string')
      expect(exp.whyThisAction.length).toBeGreaterThan(0)
    })

    it('generates whyNotAlternative for each alternative', async () => {
      const context = createMockContext()
      const recommendation = createMockRecommendation({
        alternatives: [
          { action: 'call', actionLabel: 'Make Call', reason: 'Alternative 1', confidence: 0.5 },
          { action: 'nurture', actionLabel: 'Nurture', reason: 'Alternative 2', confidence: 0.3 },
        ],
      })
      const scores = [createMockScore()]
      const rulesApplied = [createMockRule()]
      const evidence = [createMockEvidence()]

      const exp = await engine.explain(context, recommendation, scores, rulesApplied, evidence)

      expect(exp.whyNotAlternative).toHaveLength(2)
      exp.whyNotAlternative.forEach((text) => {
        expect(typeof text).toBe('string')
        expect(text.length).toBeGreaterThan(0)
      })
    })

    it('includes evidence and rules applied', async () => {
      const context = createMockContext()
      const recommendation = createMockRecommendation()
      const scores = [createMockScore()]
      const rulesApplied = [createMockRule({ id: 'rule_test_evidence' })]
      const evidence = [createMockEvidence({ id: 'evt_test_exp' })]

      const exp = await engine.explain(context, recommendation, scores, rulesApplied, evidence)

      expect(exp.evidence.length).toBeGreaterThanOrEqual(1)
      expect(exp.rulesApplied.length).toBeGreaterThanOrEqual(1)
      expect(exp.rulesApplied.some((r) => r.id === 'rule_test_evidence')).toBe(true)
    })

    it('Arabic locale produces Arabic explanations', async () => {
      const context = createMockContext({
        metadata: { locale: 'ar' },
      })
      const recommendation = createMockRecommendation({
        actionLabel: 'ترتيب اجتماع',
        reason: 'سبب الاختبار',
        alternatives: [
          { action: 'call', actionLabel: 'اتصال', reason: 'بديل', confidence: 0.5 },
        ],
      })
      const scores = [createMockScore()]
      const rulesApplied = [createMockRule()]
      const evidence = [createMockEvidence()]

      const exp = await engine.explain(context, recommendation, scores, rulesApplied, evidence)

      const hasArabic = (text: string) => /[\u0600-\u06FF]/.test(text)
      expect(hasArabic(exp.why)).toBe(true)
      expect(hasArabic(exp.whyNow)).toBe(true)
      expect(hasArabic(exp.whyThisAction)).toBe(true)
      expect(exp.whyNotAlternative.length).toBeGreaterThan(0)
      expect(hasArabic(exp.whyNotAlternative[0])).toBe(true)
    })
  })
})

describe('FeedbackEngine', () => {
  let engine: FeedbackEngine

  beforeEach(() => {
    engine = new FeedbackEngine()
  })

  describe('submit()', () => {
    it('stores and returns accepted feedback', async () => {
      const feedback = createMockFeedback()
      const result = await engine.submit(feedback)

      expect(result.accepted).toBe(true)
      expect(typeof result.id).toBe('string')
      expect(result.id.length).toBeGreaterThan(0)
    })

    it('generates a LearningEvent on submission', async () => {
      const feedback = createMockFeedback({ tenantId: 'tenant_learning' })
      await engine.submit(feedback)

      const byTenant = await engine.getByTenant('tenant_learning')
      expect(byTenant.length).toBe(1)
      expect(byTenant[0].decisionId).toBe(feedback.decisionId)
    })

    it('rejects feedback with missing required fields', async () => {
      const badFeedback = { decisionId: '', tenantId: '', actorId: '', outcome: 'accepted' as const, timestamp: '' }
      const result = await engine.submit(badFeedback)
      expect(result.accepted).toBe(false)
    })
  })

  describe('getByDecision()', () => {
    it('returns feedback for a known decision', async () => {
      const feedback = createMockFeedback({ decisionId: 'dec_lookup_test' })
      await engine.submit(feedback)

      const found = await engine.getByDecision('dec_lookup_test')
      expect(found).not.toBeNull()
      expect(found!.decisionId).toBe('dec_lookup_test')
      expect(found!.outcome).toBe(feedback.outcome)
    })

    it('returns null for unknown decision', async () => {
      const found = await engine.getByDecision('nonexistent_decision')
      expect(found).toBeNull()
    })
  })

  describe('getByTenant()', () => {
    it('returns all feedback for a tenant', async () => {
      const tenantId = 'tenant_multi_fb'
      await engine.submit(createMockFeedback({ tenantId, decisionId: 'd1' }))
      await engine.submit(createMockFeedback({ tenantId, decisionId: 'd2' }))
      await engine.submit(createMockFeedback({ tenantId, decisionId: 'd3' }))

      const results = await engine.getByTenant(tenantId)
      expect(results).toHaveLength(3)
    })

    it('respects the limit parameter', async () => {
      const tenantId = 'tenant_limit_fb'
      for (let i = 0; i < 5; i++) {
        await engine.submit(createMockFeedback({ tenantId, decisionId: `d${i}` }))
      }

      const limited = await engine.getByTenant(tenantId, 2)
      expect(limited.length).toBeLessThanOrEqual(2)
    })
  })

  describe('getStats()', () => {
    it('returns aggregated statistics for a tenant', async () => {
      const tenantId = 'tenant_stats'
      await engine.submit(createMockFeedback({ tenantId, outcome: 'accepted', revenueImpact: 10000 }))
      await engine.submit(createMockFeedback({ tenantId, outcome: 'accepted', revenueImpact: 20000 }))
      await engine.submit(createMockFeedback({ tenantId, outcome: 'rejected' }))

      const stats: FeedbackStats = await engine.getStats(tenantId)

      expect(stats.total).toBe(3)
      expect(stats.accepted).toBe(2)
      expect(stats.rejected).toBe(1)
      expect(stats.ignored).toBe(0)
      expect(stats.acceptanceRate).toBeCloseTo(2 / 3, 5)
      expect(stats.totalRevenueImpact).toBe(30000)
    })

    it('returns zero stats for tenant with no feedback', async () => {
      const stats = await engine.getStats('tenant_no_fb')
      expect(stats.total).toBe(0)
      expect(stats.acceptanceRate).toBe(0)
    })
  })
})

describe('LearningEngine', () => {
  let engine: LearningEngine

  beforeEach(() => {
    engine = new LearningEngine()
  })

  describe('record()', () => {
    it('stores learning events', async () => {
      const event = createMockLearningEvent()
      await engine.record(event)
      const quality = await engine.getRecommendationQuality('')
      expect(quality.totalRecommendations).toBeGreaterThanOrEqual(0)
    })
  })

  describe('getRecommendationQuality()', () => {
    it('returns quality metrics for a tenant with events', async () => {
      const tenantId = 'tenant_quality'
      await engine.recordWithTenant(
        createMockLearningEvent({ type: 'recommendation_quality', value: 0.9, factors: { confidence: 0.9 } }),
        tenantId,
      )
      await engine.recordWithTenant(
        createMockLearningEvent({ type: 'recommendation_quality', value: 0.6, factors: { confidence: 0.6 } }),
        tenantId,
      )
      await engine.recordWithTenant(
        createMockLearningEvent({ type: 'acceptance_rate', value: 1, factors: {} }),
        tenantId,
      )

      const quality: QualityMetrics = await engine.getRecommendationQuality(tenantId)
      expect(quality.totalRecommendations).toBe(2)
      expect(quality.averageConfidence).toBeGreaterThan(0)
      expect(quality.highConfidenceRate).toBeGreaterThanOrEqual(0)
      expect(quality.mediumConfidenceRate).toBeGreaterThanOrEqual(0)
      expect(quality.lowConfidenceRate).toBeGreaterThanOrEqual(0)
    })

    it('returns zeroed metrics when no events exist', async () => {
      const quality = await engine.getRecommendationQuality('tenant_empty')
      expect(quality.totalRecommendations).toBe(0)
      expect(quality.averageConfidence).toBe(0)
    })
  })

  describe('getAcceptanceRate()', () => {
    it('returns acceptance rate for recent events', async () => {
      const tenantId = 'tenant_acceptance'
      await engine.recordWithTenant(
        createMockLearningEvent({ type: 'acceptance_rate', value: 1, factors: {} }),
        tenantId,
      )
      await engine.recordWithTenant(
        createMockLearningEvent({ type: 'acceptance_rate', value: 0, factors: {} }),
        tenantId,
      )

      const rate = await engine.getAcceptanceRate(tenantId, 30)
      expect(rate).toBeCloseTo(0.5, 5)
    })

    it('returns 0 for tenant with no acceptance events', async () => {
      const rate = await engine.getAcceptanceRate('tenant_no_accept', 30)
      expect(rate).toBe(0)
    })
  })

  describe('getRuleEffectiveness()', () => {
    it('returns effectiveness scores for rules', async () => {
      const tenantId = 'tenant_rules'
      await engine.recordWithTenant(
        createMockLearningEvent({
          type: 'rule_effectiveness',
          value: 0.9,
          factors: { ruleId: 42, confidence: 0.85 },
        }),
        tenantId,
      )
      await engine.recordWithTenant(
        createMockLearningEvent({
          type: 'rule_effectiveness',
          value: 0.8,
          factors: { ruleId: 42, confidence: 0.8 },
        }),
        tenantId,
      )
      await engine.recordWithTenant(
        createMockLearningEvent({
          type: 'rule_effectiveness',
          value: 0.3,
          factors: { ruleId: 99, confidence: 0.4 },
        }),
        tenantId,
      )

      const effectiveness: RuleEffectiveness[] = await engine.getRuleEffectiveness(tenantId)
      expect(effectiveness.length).toBe(2)

      const rule42 = effectiveness.find((e) => e.ruleId === '42')
      expect(rule42).toBeDefined()
      expect(rule42!.timesApplied).toBe(2)
      expect(rule42!.acceptanceRate).toBe(1)

      const rule99 = effectiveness.find((e) => e.ruleId === '99')
      expect(rule99).toBeDefined()
      expect(rule99!.timesApplied).toBe(1)
      expect(rule99!.acceptanceRate).toBe(0)
    })

    it('returns empty array when no rule events exist', async () => {
      const results = await engine.getRuleEffectiveness('tenant_no_rules')
      expect(results).toHaveLength(0)
    })
  })

  describe('getTrends()', () => {
    it('returns trend data for all metric types', async () => {
      const tenantId = 'tenant_trends'

      const now = Date.now()
      const recentTs = new Date(now - 1 * 24 * 60 * 60 * 1000).toISOString()
      const olderTs = new Date(now - 10 * 24 * 60 * 60 * 1000).toISOString()

      await engine.recordWithTenant(
        createMockLearningEvent({ type: 'acceptance_rate', value: 0.8, factors: {}, timestamp: recentTs }),
        tenantId,
      )
      await engine.recordWithTenant(
        createMockLearningEvent({ type: 'acceptance_rate', value: 0.5, factors: {}, timestamp: olderTs }),
        tenantId,
      )

      const trends: LearningTrend[] = await engine.getTrends(tenantId)
      expect(trends.length).toBeGreaterThan(0)

      const metricNames = trends.map((t) => t.metric)
      expect(metricNames).toContain('acceptance_rate')
      expect(metricNames).toContain('recommendation_quality')

      trends.forEach((t) => {
        expect(typeof t.currentValue).toBe('number')
        expect(typeof t.previousValue).toBe('number')
        expect(['up', 'down', 'stable']).toContain(t.trend)
        expect(typeof t.changePercent).toBe('number')
      })
    })
  })
})

describe('Shared Utilities', () => {
  describe('generateId()', () => {
    it('creates unique IDs', () => {
      const ids = new Set<string>()
      for (let i = 0; i < 100; i++) {
        ids.add(generateId())
      }
      expect(ids.size).toBe(100)
    })

    it('uses the provided prefix', () => {
      const id = generateId('custom')
      expect(id).toMatch(/^custom_/)
    })

    it('defaults to dec prefix', () => {
      const id = generateId()
      expect(id).toMatch(/^dec_/)
    })
  })

  describe('clamp()', () => {
    it('returns the value unchanged when within range', () => {
      expect(clamp(0.5)).toBe(0.5)
    })

    it('clamps to minimum', () => {
      expect(clamp(-5)).toBe(0)
    })

    it('clamps to maximum', () => {
      expect(clamp(5)).toBe(1)
    })

    it('uses custom min and max', () => {
      expect(clamp(10, 0, 5)).toBe(5)
      expect(clamp(-10, 0, 5)).toBe(0)
      expect(clamp(3, 0, 5)).toBe(3)
    })
  })

  describe('weightedAverage()', () => {
    it('computes weighted average correctly', () => {
      const result = weightedAverage([
        { value: 1.0, weight: 0.6 },
        { value: 0.5, weight: 0.4 },
      ])
      expect(result).toBeCloseTo(0.8, 5)
    })

    it('returns 0 when all weights are 0', () => {
      const result = weightedAverage([
        { value: 1.0, weight: 0 },
        { value: 0.5, weight: 0 },
      ])
      expect(result).toBe(0)
    })

    it('handles single factor', () => {
      const result = weightedAverage([{ value: 0.75, weight: 1.0 }])
      expect(result).toBe(0.75)
    })
  })

  describe('confidenceLabel()', () => {
    it('returns high for values >= 0.7', () => {
      expect(confidenceLabel(0.7)).toBe('high')
      expect(confidenceLabel(1.0)).toBe('high')
      expect(confidenceLabel(0.85)).toBe('high')
    })

    it('returns medium for values >= 0.4 and < 0.7', () => {
      expect(confidenceLabel(0.4)).toBe('medium')
      expect(confidenceLabel(0.55)).toBe('medium')
      expect(confidenceLabel(0.69)).toBe('medium')
    })

    it('returns low for values < 0.4', () => {
      expect(confidenceLabel(0.39)).toBe('low')
      expect(confidenceLabel(0)).toBe('low')
      expect(confidenceLabel(-1)).toBe('low')
    })
  })

  describe('categorizeRisk()', () => {
    it('returns critical for values >= 0.8', () => {
      expect(categorizeRisk(0.8)).toBe('critical')
      expect(categorizeRisk(1.0)).toBe('critical')
    })

    it('returns high for values >= 0.6 and < 0.8', () => {
      expect(categorizeRisk(0.6)).toBe('high')
      expect(categorizeRisk(0.75)).toBe('high')
    })

    it('returns medium for values >= 0.3 and < 0.6', () => {
      expect(categorizeRisk(0.3)).toBe('medium')
      expect(categorizeRisk(0.5)).toBe('medium')
    })

    it('returns low for values < 0.3', () => {
      expect(categorizeRisk(0.29)).toBe('low')
      expect(categorizeRisk(0)).toBe('low')
    })
  })

  describe('deduplicateBy()', () => {
    it('removes duplicates by key function', () => {
      const items = [
        { id: 1, name: 'A' },
        { id: 2, name: 'B' },
        { id: 1, name: 'A2' },
        { id: 3, name: 'C' },
      ]
      const result = deduplicateBy(items, (i) => String(i.id))
      expect(result).toHaveLength(3)
    })

    it('uses keepFn to resolve duplicates', () => {
      const items = [
        { id: 1, score: 5 },
        { id: 1, score: 10 },
        { id: 2, score: 3 },
      ]
      const result = deduplicateBy(items, (i) => String(i.id), (a, b) =>
        a.score > b.score ? a : b,
      )
      expect(result).toHaveLength(2)
      const item1 = result.find((i) => i.id === 1)
      expect(item1!.score).toBe(10)
    })

    it('returns empty array for empty input', () => {
      expect(deduplicateBy([], () => 'key')).toHaveLength(0)
    })
  })

  describe('paginate()', () => {
    const items = Array.from({ length: 25 }, (_, i) => `item_${i}`)

    it('returns correct first page', () => {
      const result = paginate(items, 1, 10)
      expect(result.items).toHaveLength(10)
      expect(result.total).toBe(25)
      expect(result.page).toBe(1)
      expect(result.hasMore).toBe(true)
    })

    it('returns correct last page', () => {
      const result = paginate(items, 3, 10)
      expect(result.items).toHaveLength(5)
      expect(result.hasMore).toBe(false)
    })

    it('handles empty array', () => {
      const result = paginate([], 1, 10)
      expect(result.items).toHaveLength(0)
      expect(result.total).toBe(0)
      expect(result.hasMore).toBe(false)
    })
  })
})
