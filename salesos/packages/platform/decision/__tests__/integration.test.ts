jest.mock('../../agents/memory', () => ({
  store: jest.fn(),
  recall: jest.fn(),
  forget: jest.fn(),
  clear: jest.fn(),
  getContext: jest.fn(),
}))

import { DecisionEngine } from '../decision-engine'
import { RuleEngine } from '../rule-engine'
import { ScoringEngine } from '../scoring-engine'
import { EvidenceEngine } from '../evidence-engine'
import { FeedbackEngine } from '../feedback-engine'
import type { FeedbackStats } from '../feedback-engine'
import * as registry from '../../agents/registry'
import * as orchestrator from '../../agents/orchestrator'
import type { DecisionContext, DecisionResult, EvidenceItem, Score } from '../contracts'
import type { AgentDefinition } from '../../agents/contracts'
import type { RuleEvaluationResult } from '../rule-engine'

let decisionEngine: DecisionEngine
let ruleEngine: RuleEngine
let scoringEngine: ScoringEngine
let evidenceEngine: EvidenceEngine
let feedbackEngine: FeedbackEngine

beforeEach(() => {
  decisionEngine = new DecisionEngine()
  ruleEngine = new RuleEngine()
  scoringEngine = new ScoringEngine()
  evidenceEngine = new EvidenceEngine()
  feedbackEngine = new FeedbackEngine()
})

afterEach(() => {
  registry.unregister('test-integration-agent')
  registry.unregister('orchestrator-test-agent')
  registry.unregister('multi-agent-1')
  registry.unregister('multi-agent-2')
})

describe('Flow 1: Decision Platform → NBA Recommendation', () => {
  it('evaluates a high-intent company and returns full DecisionResult', async () => {
    const context: DecisionContext = {
      tenantId: 'acme-corp',
      actorId: 'sales-rep-1',
      entityId: 'comp_energy_01',
      entityType: 'company',
      companyId: 'comp_energy_01',
      metadata: {
        strength: 'high',
        buyingIntent: 0.92,
        opportunityValue: 750000,
        hasGovernmentContracts: true,
        hiringTrend: 'growing',
        relationshipScore: 0.85,
      },
    }

    const result: DecisionResult = await decisionEngine.evaluate(context)

    expect(result.decisionId).toBeDefined()
    expect(typeof result.decisionId).toBe('string')

    expect(result.recommendation).toBeDefined()
    expect(result.recommendation.action).toBe('pursue')
    expect(result.recommendation.actionLabel).toBe('Pursue Immediately')
    expect(result.recommendation.confidence).toBeGreaterThanOrEqual(0.7)
    expect(result.recommendation.confidenceLabel).toBe('high')
    expect(result.recommendation.alternatives.length).toBeGreaterThanOrEqual(2)
    expect(result.recommendation.risks).toBeDefined()

    const scoreTypes = result.scores.map(s => s.type)
    expect(scoreTypes).toContain('confidence')
    expect(scoreTypes).toContain('company')

    const confidenceScore = result.scores.find(s => s.type === 'confidence')!
    expect(confidenceScore.value).toBeGreaterThanOrEqual(0)
    expect(confidenceScore.value).toBeLessThanOrEqual(1)
    expect(confidenceScore.factors.length).toBeGreaterThan(0)

    expect(result.evidence.length).toBeGreaterThan(0)
    const metadataEvidence = result.evidence.filter(e => e.source === 'context.metadata')
    expect(metadataEvidence.length).toBeGreaterThanOrEqual(5)

    expect(result.explainability).toBeDefined()
    expect(typeof result.explainability.why).toBe('string')
    expect(result.explainability.why.length).toBeGreaterThan(0)
    expect(typeof result.explainability.whyNow).toBe('string')
    expect(result.explainability.whyNow.length).toBeGreaterThan(0)
    expect(typeof result.explainability.whyThisAction).toBe('string')
    expect(result.explainability.whyThisAction.length).toBeGreaterThan(0)
    expect(Array.isArray(result.explainability.whyNotAlternative)).toBe(true)
    expect(result.explainability.whyNotAlternative.length).toBeGreaterThan(0)
    expect(result.explainability.evidence.length).toBeGreaterThan(0)
    expect(result.explainability.rulesApplied.length).toBeGreaterThan(0)
    expect(typeof result.explainability.confidence).toBe('number')
    expect(result.explainability.expectedImpact.revenue).toBeGreaterThan(0)
    expect(result.explainability.expectedImpact.timeframe).toBeTruthy()

    const ruleIds = result.rulesApplied.map(r => r.id)
    expect(ruleIds).toContain('rule-data-quality')
    expect(ruleIds).toContain('rule-high-intent')

    expect(result.telemetry.evaluationTimeMs).toBeGreaterThanOrEqual(0)
    expect(result.telemetry.rulesTimeMs).toBeGreaterThanOrEqual(0)
    expect(result.telemetry.scoringTimeMs).toBeGreaterThanOrEqual(0)
    expect(result.telemetry.evidenceTimeMs).toBeGreaterThanOrEqual(0)
    expect(result.telemetry.recommendationTimeMs).toBeGreaterThanOrEqual(0)
  })

  it('includes revenue score for opportunity entity type', async () => {
    const context: DecisionContext = {
      tenantId: 'tenant-opp',
      actorId: 'actor-opp',
      entityId: 'opp_01',
      entityType: 'opportunity',
      opportunityId: 'opp_01',
      metadata: { opportunityValue: 600000, strength: 'high' },
    }

    const result = await decisionEngine.evaluate(context)
    const scoreTypes = result.scores.map(s => s.type)
    expect(scoreTypes).toContain('confidence')
    expect(scoreTypes).toContain('revenue')

    const revenueScore = result.scores.find(s => s.type === 'revenue')!
    expect(revenueScore.value).toBeGreaterThan(0)
    expect(revenueScore.factors.length).toBeGreaterThan(0)

    expect(result.recommendation.action).toBe('accelerate')
    expect(result.recommendation.actionLabel).toBe('Accelerate Deal')
  })

  it('returns moderate confidence for minimal context due to rules', async () => {
    const context: DecisionContext = { tenantId: 'minimal', actorId: 'minimal' }
    const result = await decisionEngine.evaluate(context)

    expect(result.recommendation.confidence).toBeGreaterThanOrEqual(0.4)
    expect(result.recommendation.confidence).toBeLessThanOrEqual(0.5)
    expect(result.recommendation.confidenceLabel).toBe('medium')
    expect(result.recommendation.action).toBe('nurture')
    expect(result.recommendation.actionLabel).toBe('Nurture & Monitor')
    expect(result.evidence.length).toBe(1)
    expect(result.evidence[0].type).toBe('search')
    expect(result.evidence[0].description).toBe('No contextual evidence available — default evaluation')
  })

  it('stores decision history per tenant', async () => {
    const tenantId = 'hist-tenant'
    const c1 = await decisionEngine.evaluate({ tenantId, actorId: 'a1', entityId: 'e1' })
    const c2 = await decisionEngine.evaluate({ tenantId, actorId: 'a2', entityId: 'e2' })

    const history = await decisionEngine.getHistory(tenantId)
    expect(history).toHaveLength(2)
    expect(history.map(h => h.decisionId)).toContain(c1.decisionId)
    expect(history.map(h => h.decisionId)).toContain(c2.decisionId)
  })
})

describe('Flow 2: Rule Engine → Scoring', () => {
  it('fires rules matching high-intent metadata', async () => {
    const context: DecisionContext = {
      tenantId: 'rule-tenant',
      actorId: 'rule-actor',
      entityId: 'rule-entity',
      metadata: {
        hiringTrend: 'growing',
        hasGovernmentContracts: true,
        relationshipScore: 0.9,
        opportunityValue: 600000,
      },
    }

    const evidence: EvidenceItem[] = []
    for (const [key, value] of Object.entries(context.metadata ?? {})) {
      evidence.push({
        id: `evt_${key}`,
        type: 'signal',
        description: `${key}: ${JSON.stringify(value)}`,
        source: 'metadata',
        confidence: 0.85,
        freshness: 'current',
        timestamp: new Date().toISOString(),
        data: { [key]: value },
      })
    }

    const evalResult: RuleEvaluationResult = await ruleEngine.evaluate(context, evidence)

    expect(evalResult.rulesFired.length).toBeGreaterThanOrEqual(4)
    const firedIds = evalResult.rulesFired.map(r => r.id)
    expect(firedIds).toContain('rule_high_hiring_growth')
    expect(firedIds).toContain('rule_government_tender')
    expect(firedIds).toContain('rule_relationship_strength')
    expect(firedIds).toContain('rule_high_revenue')
  })

  it('computes scores within 0-1 range', () => {
    const score = scoringEngine.score('company', {
      financial_health: 0.85,
      growth_trend: 0.75,
      digital_presence: 0.6,
      hiring_trend: 0.9,
      procurement_maturity: 0.7,
    })

    expect(score.value).toBeGreaterThanOrEqual(0)
    expect(score.value).toBeLessThanOrEqual(1)
    expect(score.confidence).toBeGreaterThanOrEqual(0)
    expect(score.confidence).toBeLessThanOrEqual(1)
    expect(score.factors).toHaveLength(5)
    score.factors.forEach(f => {
      expect(f.value).toBeGreaterThanOrEqual(0)
      expect(f.value).toBeLessThanOrEqual(1)
    })
  })

  it('combines rule engine and scoring in a realistic pipeline', async () => {
    const context: DecisionContext = {
      tenantId: 'pipeline',
      actorId: 'pipeline',
      entityId: 'pipeline-co',
      metadata: {
        hiringTrend: 'growing',
        hasGovernmentContracts: true,
        relationshipScore: 0.85,
        opportunityValue: 500000,
        financial_health: 0.8,
      },
    }

    const evidence: EvidenceItem[] = []
    for (const [key, value] of Object.entries(context.metadata ?? {})) {
      evidence.push({
        id: `evt_pipe_${key}`,
        type: 'signal',
        description: `${key}: ${JSON.stringify(value)}`,
        source: 'context.metadata',
        confidence: 0.85,
        freshness: 'current',
        timestamp: new Date().toISOString(),
        data: { [key]: value },
      })
    }

    const ruleResult = await ruleEngine.evaluate(context, evidence)
    expect(ruleResult.rulesFired.length).toBeGreaterThan(0)
    expect(ruleResult.auditLog.length).toBeGreaterThan(0)

    const companyScore = scoringEngine.score('company', {
      financial_health: 0.8,
      growth_trend: 0.75,
      digital_presence: 0.65,
      hiring_trend: 0.9,
      procurement_maturity: 0.7,
    })
    expect(companyScore.value).toBeGreaterThan(0.5)

    const intentScore = scoringEngine.score('intent', {
      signal_activity: 0.85,
      hiring_trend: 0.9,
      government_exposure: 0.8,
      expansion_potential: 0.7,
      digital_engagement: 0.6,
    })
    expect(intentScore.value).toBeGreaterThan(0.5)

    const highIntentFired = ruleResult.rulesFired.some(
      r => r.id === 'rule_high_hiring_growth' && r.category === 'intent',
    )
    expect(highIntentFired).toBe(true)
    expect(intentScore.label).toBe('good')
  })
})

describe('Flow 3: Feedback → Learning', () => {
  it('submits feedback and retrieves it by decision', async () => {
    const result = await feedbackEngine.submit({
      decisionId: 'dec_feedback_1',
      tenantId: 'fb-tenant',
      actorId: 'fb-actor',
      outcome: 'accepted',
      revenueImpact: 150000,
      timeToExecution: 86400,
      reason: 'Good opportunity fit',
      timestamp: new Date().toISOString(),
    })

    expect(result.accepted).toBe(true)
    expect(result.id.length).toBeGreaterThan(0)

    const stored = await feedbackEngine.getByDecision('dec_feedback_1')
    expect(stored).not.toBeNull()
    expect(stored!.outcome).toBe('accepted')
    expect(stored!.revenueImpact).toBe(150000)
  })

  it('tracks stats across multiple feedback submissions', async () => {
    const tenant = 'stats-tenant'
    await feedbackEngine.submit({ decisionId: 'd1', tenantId: tenant, actorId: 'a', outcome: 'accepted', revenueImpact: 50000, timestamp: new Date().toISOString() })
    await feedbackEngine.submit({ decisionId: 'd2', tenantId: tenant, actorId: 'a', outcome: 'accepted', revenueImpact: 100000, timestamp: new Date().toISOString() })
    await feedbackEngine.submit({ decisionId: 'd3', tenantId: tenant, actorId: 'a', outcome: 'rejected', timestamp: new Date().toISOString() })
    await feedbackEngine.submit({ decisionId: 'd4', tenantId: tenant, actorId: 'a', outcome: 'ignored', timestamp: new Date().toISOString() })

    const stats: FeedbackStats = await feedbackEngine.getStats(tenant)
    expect(stats.total).toBe(4)
    expect(stats.accepted).toBe(2)
    expect(stats.rejected).toBe(1)
    expect(stats.ignored).toBe(1)
    expect(stats.acceptanceRate).toBe(0.5)
    expect(stats.totalRevenueImpact).toBe(150000)
  })

  it('rejects invalid feedback', async () => {
    const result = await feedbackEngine.submit({
      decisionId: '',
      tenantId: '',
      actorId: '',
      outcome: 'accepted' as const,
      timestamp: '',
    })
    expect(result.accepted).toBe(false)
    expect(result.id).toBe('')
  })
})

describe('Flow 4: Evidence → Explainability', () => {
  it('collects evidence from context', async () => {
    const context: DecisionContext = {
      tenantId: 'ev-tenant',
      actorId: 'ev-actor',
      entityId: 'ev-entity',
      companyId: 'ev-company',
      metadata: { buyingIntent: 0.95, strength: 'high' },
    }

    const collected = await evidenceEngine.collect(context)
    expect(collected.items.length).toBeGreaterThan(0)
    expect(collected.deduplicated).toBeGreaterThanOrEqual(0)
    expect(collected.totalSources).toBeGreaterThan(0)
    expect(collected.averageConfidence).toBeGreaterThan(0)
    expect(collected.collectionTimeMs).toBeGreaterThanOrEqual(0)
  })

  it('deduplicates evidence by type and description', async () => {
    const context: DecisionContext = { tenantId: 'dedup', actorId: 'dedup', entityId: 'dedup-entity' }

    const sources = [
      {
        type: 'signal' as const,
        provider: { name: 'p1', confidence: 0.9, freshnessMax: 24 },
        data: [
          { description: 'Duplicate signal', source: 'src1', timestamp: new Date().toISOString() },
          { description: 'Duplicate signal', source: 'src2', timestamp: new Date().toISOString() },
          { description: 'Unique signal', source: 'src3', timestamp: new Date().toISOString() },
        ],
      },
    ]

    const result = await evidenceEngine.collect(context, sources)
    expect(result.deduplicated).toBe(1)
    expect(result.items.length).toBe(2)

    const descriptions = result.items.map(i => i.description)
    expect(descriptions.filter(d => d === 'Duplicate signal')).toHaveLength(1)
    expect(descriptions).toContain('Unique signal')
  })

  it('retrieves explainability from decision engine', async () => {
    const context: DecisionContext = {
      tenantId: 'exp-tenant',
      actorId: 'exp-actor',
      entityId: 'exp-entity',
      entityType: 'company',
      metadata: { strength: 'high', buyingIntent: 0.88, opportunityValue: 500000 },
    }

    const result = await decisionEngine.evaluate(context)
    const explanation = await decisionEngine.explain(result.decisionId)

    expect(explanation).not.toBeNull()
    expect(explanation!.why.length).toBeGreaterThan(0)
    expect(explanation!.whyNow.length).toBeGreaterThan(0)
    expect(explanation!.whyThisAction.length).toBeGreaterThan(0)
    expect(explanation!.whyNotAlternative.length).toBeGreaterThan(0)
    expect(explanation!.evidence.length).toBeGreaterThan(0)
    expect(explanation!.rulesApplied.length).toBeGreaterThan(0)
    expect(typeof explanation!.confidence).toBe('number')
    expect(typeof explanation!.risk).toBe('string')
    expect(explanation!.expectedImpact.revenue).toBeGreaterThan(0)
    expect(explanation!.expectedImpact.timeframe).toBeTruthy()
  })

  it('returns null for unknown decision', async () => {
    const explanation = await decisionEngine.explain('nonexistent-decision')
    expect(explanation).toBeNull()
  })
})

describe('Flow 5: Agent Engine', () => {
  it('registers an agent and creates a task', async () => {
    const agent: AgentDefinition = {
      id: 'test-integration-agent',
      name: 'Test Integration Agent',
      description: 'Agent created during integration test',
      capabilities: ['test', 'decision-execution'],
      tools: ['evaluate_decision'],
      memoryConfig: { ttl: 60000, maxEntries: 10, storageType: 'memory' },
      maxConcurrency: 3,
    }

    registry.register(agent)
    const retrieved = registry.get('test-integration-agent')
    expect(retrieved).toBeDefined()
    expect(retrieved!.name).toBe('Test Integration Agent')
    expect(retrieved!.tools).toContain('evaluate_decision')

    const task = await orchestrator.assignTask(
      'test-integration-agent',
      { tenantId: 't1', entityId: 'e1', entityType: 'company' },
      'Test assignment',
    )
    expect(task.agentId).toBe('test-integration-agent')
    expect(task.status).toBe('pending')
  })

  it('executes an agent task through the orchestrator', async () => {
    const agent: AgentDefinition = {
      id: 'orchestrator-test-agent',
      name: 'Orchestrator Test Agent',
      description: 'Agent for orchestrator test',
      capabilities: ['decision-execution'],
      tools: ['evaluate_decision'],
      memoryConfig: { ttl: 60000, maxEntries: 10, storageType: 'memory' },
      maxConcurrency: 5,
    }

    registry.register(agent)

    const task = await orchestrator.assignTask(
      'orchestrator-test-agent',
      {
        tenantId: 'agent-tenant',
        entityId: 'agent-entity',
        entityType: 'company',
        metadata: { buyingIntent: 0.9, strength: 'high' },
      },
      'Evaluate high-intent prospect',
    )

    expect(task.priority).toBe('high')

    const result = await orchestrator.executeTask(task.id)
    expect(result.taskId).toBe(task.id)
    expect(result.agentId).toBe('orchestrator-test-agent')
    expect(result.decision).toBeDefined()
    expect(result.decision.recommendation).toBeDefined()
    expect(result.decision.recommendation.confidence).toBeGreaterThan(0)
    expect(result.decision.scores.length).toBeGreaterThan(0)
    expect(result.actions).toBeDefined()
    expect(Array.isArray(result.actions)).toBe(true)
    expect(result.summary).toBeTruthy()
    expect(result.summary).toContain('Evaluate high-intent prospect')
  })

  it('executes tasks for multiple agents concurrently', async () => {
    const agentDefs = [
      { id: 'multi-agent-1', name: 'Multi Agent 1' },
      { id: 'multi-agent-2', name: 'Multi Agent 2' },
    ]

    for (const a of agentDefs) {
      registry.register({
        id: a.id,
        name: a.name,
        description: `Agent ${a.id}`,
        capabilities: ['decision-execution'],
        tools: ['evaluate_decision'],
        memoryConfig: { ttl: 60000, maxEntries: 10, storageType: 'memory' },
        maxConcurrency: 5,
      })
    }

    const batch = agentDefs.map(a => ({
      agentId: a.id,
      context: { tenantId: 'multi-tenant', entityId: a.id, metadata: { priority: 'critical' } },
      goal: `Process for ${a.id}`,
    }))

    const results = await orchestrator.executeBatch(batch)
    expect(results).toHaveLength(2)
    results.forEach((r, i) => {
      expect(r.agentId).toBe(agentDefs[i].id)
      expect(r.decision.recommendation).toBeDefined()
      expect(r.actions).toBeDefined()
    })

    const finalTask = orchestrator.getTask(results[0].taskId)
    expect(finalTask).toBeDefined()
    expect(finalTask!.status).toBe('completed')
  })
})

describe('Flow 6: Full End-to-End Product Story', () => {
  it('completes the full decision platform lifecycle', async () => {
    const tenantId = 'e2e-tenant'

    const context: DecisionContext = {
      tenantId,
      actorId: 'sales-rep-1',
      entityId: 'e2e-company',
      entityType: 'company',
      companyId: 'e2e-company',
      metadata: {
        name: 'Al Taqnia Advanced Tech',
        industry: 'technology',
        strength: 'high',
        buyingIntent: 0.94,
        hiringTrend: 'growing',
        hasGovernmentContracts: true,
        relationshipScore: 0.88,
        opportunityValue: 850000,
        financial_health: 0.85,
      },
    }

    const decision = await decisionEngine.evaluate(context)
    expect(decision.recommendation.action).toBe('pursue')
    expect(decision.recommendation.confidence).toBeGreaterThanOrEqual(0.7)
    expect(decision.scores.length).toBeGreaterThanOrEqual(2)
    expect(decision.explainability.why).toBeTruthy()
    expect(decision.explainability.whyNow).toBeTruthy()
    expect(decision.explainability.whyThisAction).toBeTruthy()

    const ruleResult = await ruleEngine.evaluate(context, decision.evidence)
    expect(ruleResult.rulesFired.length).toBeGreaterThan(0)
    const firedIds = ruleResult.rulesFired.map(r => r.id)
    expect(firedIds).toContain('rule_high_hiring_growth')
    expect(firedIds).toContain('rule_government_tender')

    const companyScore = scoringEngine.score('company', {
      financial_health: 0.85,
      growth_trend: 0.8,
      digital_presence: 0.7,
      hiring_trend: 0.9,
      procurement_maturity: 0.75,
    })
    expect(companyScore.value).toBeGreaterThan(0.7)
    expect(companyScore.label).toBe('good')

    const intentScore = scoringEngine.score('intent', {
      signal_activity: 0.9,
      hiring_trend: 0.9,
      government_exposure: 0.85,
      expansion_potential: 0.75,
      digital_engagement: 0.7,
    })
    expect(intentScore.value).toBeGreaterThan(0.7)

    const feedback = await feedbackEngine.submit({
      decisionId: decision.decisionId,
      tenantId,
      actorId: 'sales-rep-1',
      outcome: 'accepted',
      revenueImpact: 850000,
      reason: 'High buying intent and government contracts',
      timestamp: new Date().toISOString(),
    })
    expect(feedback.accepted).toBe(true)

    const storedFeedback = await feedbackEngine.getByDecision(decision.decisionId)
    expect(storedFeedback).not.toBeNull()
    expect(storedFeedback!.outcome).toBe('accepted')

    const stats = await feedbackEngine.getStats(tenantId)
    expect(stats.total).toBe(1)
    expect(stats.accepted).toBe(1)
    expect(stats.totalRevenueImpact).toBe(850000)

    const history = await decisionEngine.getHistory(tenantId)
    expect(history.length).toBe(1)
    expect(history[0].decisionId).toBe(decision.decisionId)
  })
})
