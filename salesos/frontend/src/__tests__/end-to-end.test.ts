/**
 * End-to-end integration test — complete product flow.
 * Tests that all modules work together: Search → Company Intelligence → NBA → Opportunity → Pipeline → Task
 */

import { SearchQueryBuilder, queryToKey } from '@salesos/search'
import { deriveStatus } from '@salesos/workspace'
import { deriveNextBestAction } from '@/application/revenue-execution/nba.engine'
import { createOpportunity, loadOpportunities, updateOpportunityStage } from '@/application/revenue-execution/opportunity.store'
import { calculateWinProbability, STAGE_LABEL } from '@/application/revenue-execution/opportunity.dto'
import { addTask, completeTask, loadTasks } from '@/application/revenue-execution/task.store'
import type { CompanyDNA, AIRecommendation, TimelineEvent, SignalItem, DecisionMaker } from '@/application/company-intelligence/company-intelligence.dto'
import type { NextBestAction } from '@/application/revenue-execution/nba.dto'

// ─── Mock Data ──────────────────────────────────────────────

const dna: CompanyDNA = {
  industry: 'energy', businessModel: 'b2b', size: { employees: 15000, revenue: '1.2B', label: 'enterprise' },
  growthPattern: 'accelerating', buyingBehaviour: { score: 78, intent: 'high' },
  technologyProfile: {}, financialHealth: { score: 82, revenue: 1_200_000_000, growth: 12.5, trend: 'up' },
  governmentExposure: { level: 'high', contracts: 45 },
  expansionPotential: { score: 72, markets: [] }, digitalPresence: { score: 68, website: 'active', social: 'active' },
  hiringTrend: { trend: 'growing', openings: 120 }, procurementMaturity: { score: 65, level: 'managed' },
  relationshipStrength: { score: 70, connections: 15 }, buyingIntent: { score: 82, confidence: 0.88 },
  riskLevel: { score: 25, level: 'low' }, confidenceScore: 0.92,
  dataFreshness: { score: 90, updatedAt: '2026-07-10' }, goldenRecordStatus: { status: 'clean', sources: 5 },
}

const recommendation: AIRecommendation = {
  action: 'meeting', actionLabel: 'ترتيب اجتماع', reasoning: 'ارتفاع نية الشراء', confidence: 0.85,
  expectedRevenue: 500000, expectedImpact: 'high', estimatedTime: 'أسبوعين',
  alternatives: [{ action: 'send_proposal', actionLabel: 'إرسال عرض', confidence: 0.7 }],
  risks: ['مورد بديل قيد التقييم'],
}

const signals: SignalItem[] = [
  { id: 's1', type: 'hiring', title: 'توظيف 500 مهندس', description: '', source: 'LinkedIn', severity: 'high', timestamp: '2026-07-10T08:00:00Z', aiConfidence: 0.9 },
]

const timeline: TimelineEvent[] = [
  { id: 't1', type: 'signal', summary: 'إعلان توسع', date: '2026-07-10', source: 'News', aiHighlighted: true },
]

const makers: DecisionMaker[] = [
  { id: 'dm1', name: 'أحمد', role: 'CEO', department: '', influence: 'high', connected: true },
]

// ─── Flow 1: Search → Query Building ───────────────────────

describe('Flow 1: Search — Query Building', () => {
  it('builds a search query from natural language', () => {
    const q = SearchQueryBuilder.create('hospitals opening new branches')
      .withTypes(['company'])
      .withNaturalLanguage(true)
      .withPage(1)
      .build()

    expect(q.text).toBe('hospitals opening new branches')
    expect(q.types).toEqual(['company'])
    expect(q.naturalLanguage).toBe(true)
  })

  it('generates a unique cache key from query', () => {
    const key1 = queryToKey({ text: 'energy companies', types: ['company'] })
    const key2 = queryToKey({ text: 'energy companies' })
    expect(key1).not.toBe(key2) // types differentiate
  })

  it('derives correct widget status', () => {
    expect(deriveStatus({}, false, false)).toBe('ready')
    expect(deriveStatus(null, true, false)).toBe('loading')
    expect(deriveStatus({}, true, false)).toBe('degraded')
    expect(deriveStatus(null, false, true)).toBe('error')
  })
})

// ─── Flow 2: Company Intelligence → NBA Engine ─────────────

describe('Flow 2: Company Intelligence → NBA Engine', () => {
  let action: NextBestAction | null

  it('derives NBA from Company DNA + AI Recommendation', () => {
    action = deriveNextBestAction(dna, recommendation, timeline, signals, makers)
    expect(action).not.toBeNull()
    expect(action!.actionLabel).toBeDefined()
    expect(action!.score).toBeGreaterThan(0)
  })

  it('calculates priority correctly for high-intent company', () => {
    expect(['critical', 'high']).toContain(action!.priority)
  })

  it('includes revenue impact', () => {
    expect(action!.expectedRevenue).toBeGreaterThan(0)
  })

  it('includes risks from AI Recommendation', () => {
    expect(action!.risks).toContain('مورد بديل قيد التقييم')
  })

  it('includes score breakdown', () => {
    expect(action!.scoreBreakdown.buyingIntent).toBeGreaterThan(0)
    expect(action!.scoreBreakdown.relationshipStrength).toBeGreaterThan(0)
    expect(action!.scoreBreakdown.signalRecency).toBeGreaterThan(0)
  })

  it('sets createsOpportunity flag for high scores', () => {
    expect(action!.createsOpportunity).toBe(true)
  })

  it('assigns industry-specific playbook', () => {
    expect(action!.playbookId).toBe('playbook-energy')
  })

  it('identifies trigger event from timeline', () => {
    expect(action!.triggerEvent).toBe('توظيف 500 مهندس')
  })
})

// ─── Flow 3: NBA → Opportunity Creation ────────────────────

describe('Flow 3: NBA → Opportunity', () => {
  let nba: NextBestAction
  let opportunityId: string

  beforeAll(() => {
    nba = deriveNextBestAction(dna, recommendation, timeline, signals, makers)!
  })

  it('creates opportunity from NBA action', () => {
    const opp = createOpportunity({
      companyId: 'comp_energy',
      companyName: 'شركة الطاقة',
      title: nba.actionLabel,
      estimatedValue: nba.expectedRevenue,
      confidence: nba.confidence,
      buyingIntent: nba.scoreBreakdown.buyingIntent,
      relationshipStrength: nba.scoreBreakdown.relationshipStrength,
      sourceActionId: nba.actionId,
    })

    expect(opp.title).toBe(nba.actionLabel)
    expect(opp.estimatedValue).toBe(500000)
    expect(opp.stage).toBe('identified')
    expect(opp.source).toBe('nba')
    expect(opp.sourceActionId).toBe(nba.actionId)
    opportunityId = opp.id
  })

  it('calculates win probability for the opportunity', () => {
    const prob = calculateWinProbability({
      stage: 'developing',
      buyingIntent: 0.82,
      relationshipStrength: 0.70,
      nbaConfidence: 0.85,
      signalActivity: 0.60,
    })
    expect(prob).toBeGreaterThan(0.3)
    expect(prob).toBeLessThanOrEqual(1)
  })

  it('updates opportunity stage through pipeline', () => {
    const updated = updateOpportunityStage(opportunityId, 'qualifying')
    const opp = updated.find((o) => o.id === opportunityId)
    expect(opp?.stage).toBe('qualifying')
  })

  it('advances stage to developing', () => {
    const updated = updateOpportunityStage(opportunityId, 'developing')
    const opp = updated.find((o) => o.id === opportunityId)
    expect(opp?.stage).toBe('developing')
  })

  it('has correct stage labels', () => {
    expect(STAGE_LABEL.identified).toBe('تم التحديد')
    expect(STAGE_LABEL.developing).toBe('قيد التطوير')
    expect(STAGE_LABEL.closing).toBe('قيد الإغلاق')
    expect(STAGE_LABEL.won).toBe('فوز')
  })
})

// ─── Flow 4: Opportunity → Task ────────────────────────────

describe('Flow 4: Opportunity → Task', () => {
  it('creates task from NBA recommendation', () => {
    const tasks = addTask({
      title: 'متابعة شركة الطاقة',
      priority: 'high',
      source: 'nba',
      companyId: 'comp_energy',
      companyName: 'شركة الطاقة',
      dueDate: '2026-07-20',
      completed: false,
    })

    const task = tasks.find((t) => t.title === 'متابعة شركة الطاقة')
    expect(task).toBeDefined()
    expect(task!.priority).toBe('high')
    expect(task!.companyName).toBe('شركة الطاقة')
  })

  it('completes task', () => {
    const tasks = loadTasks()
    const task = tasks.find((t) => t.title === 'متابعة شركة الطاقة')!
    const updated = completeTask(task.id)
    const completed = updated.find((t) => t.id === task.id)
    expect(completed!.completed).toBe(true)
  })
})

// ─── Flow 5: End-to-End Integration ─────────────────────────

describe('Flow 5: Full Product Flow', () => {
  it('completes the full cycle: Search → NBA → Opportunity → Pipeline → Task', () => {
    // 1. Search (via query builder)
    const query = SearchQueryBuilder.create('energy companies with high buying intent').withTypes(['company']).build()
    expect(query.text).toContain('energy')

    // 2. NBA Engine
    const action = deriveNextBestAction(dna, recommendation, timeline, signals, makers)
    expect(action).not.toBeNull()
    expect(action!.createsOpportunity).toBe(true)

    // 3. Create Opportunity
    const opp = createOpportunity({
      companyId: 'comp_energy',
      companyName: 'شركة الطاقة',
      title: action!.actionLabel,
      estimatedValue: action!.expectedRevenue,
      confidence: action!.confidence,
      buyingIntent: action!.scoreBreakdown.buyingIntent,
      relationshipStrength: action!.scoreBreakdown.relationshipStrength,
    })
    expect(opp.stage).toBe('identified')

    // 4. Advance through pipeline
    const stages = ['qualifying', 'developing', 'proposing'] as const
    stages.forEach((stage) => {
      const updated = updateOpportunityStage(opp.id, stage)
      const o = updated.find((x) => x.id === opp.id)
      expect(o?.stage).toBe(stage)
    })

    // 5. Calculate win probability
    const prob = calculateWinProbability({
      stage: 'proposing',
      buyingIntent: 0.82,
      relationshipStrength: 0.70,
      nbaConfidence: 0.85,
      signalActivity: 0.60,
    })
    expect(prob).toBeGreaterThan(0.5)

    // 6. Create Task
    const tasks = addTask({
      title: `متابعة ${opp.companyName}`,
      priority: 'high',
      source: 'nba',
      companyId: opp.companyId,
      companyName: opp.companyName,
    })
    expect(tasks.some((t) => t.title === `متابعة ${opp.companyName}`)).toBe(true)
  })
})
