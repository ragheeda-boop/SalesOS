import type {
  DecisionContext,
  Recommendation,
  AlternativeRecommendation,
  Risk,
  EvidenceItem,
  DecisionRule,
  Score,
  ScoreType,
  RiskLevel,
  ConfidenceLabel,
  DecisionSource,
} from '../contracts/index'

interface ActionDefinition {
  action: string
  actionLabel: string
  evaluate: (args: ActionArgs) => number
  risks: (args: ActionArgs) => Risk[]
  impact: (args: ActionArgs) => { revenue?: number; effort: string; time: string; business: string }
}

interface ActionArgs {
  context: DecisionContext
  scores: Score[]
  rulesApplied: DecisionRule[]
  evidence: EvidenceItem[]
}

function generateId(): string {
  return 'rec_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 9)
}

function getScore(scores: Score[], type: ScoreType): Score | undefined {
  return scores.find(s => s.type === type)
}

function getScoreValue(scores: Score[], type: ScoreType): number {
  return getScore(scores, type)?.value ?? 0
}

function getScoreConfidence(scores: Score[], type: ScoreType): number {
  return getScore(scores, type)?.confidence ?? 0
}

function relevantEvidence(evidence: EvidenceItem[], keywords: string[]): EvidenceItem[] {
  return evidence.filter(e => {
    const text = `${e.description} ${e.type} ${e.source}`.toLowerCase()
    return keywords.some(k => text.includes(k.toLowerCase()))
  })
}

function confidenceLabel(score: number): ConfidenceLabel {
  if (score >= 0.75) return 'high'
  if (score >= 0.45) return 'medium'
  return 'low'
}

const ACTION_DEFINITIONS: ActionDefinition[] = [
  {
    action: 'meeting',
    actionLabel: 'Arrange Meeting',
    evaluate({ scores, rulesApplied }) {
      const intent = getScoreValue(scores, 'intent')
      const relationship = getScoreValue(scores, 'relationship')
      const revenue = getScoreValue(scores, 'revenue')
      if (intent < 0.6 || relationship < 0.5) return 0

      let score = intent * 0.4 + relationship * 0.35 + revenue * 0.25
      const meetingRule = rulesApplied.find(r => r.action === 'meeting')
      if (meetingRule) score += meetingRule.weight * 0.15
      return Math.min(score, 0.95)
    },
    risks({ scores }) {
      const dataQuality = getScoreValue(scores, 'data_quality')
      const risks: Risk[] = []
      if (dataQuality < 0.4) {
        risks.push({
          type: 'insufficient_data',
          level: 'medium',
          description: 'Low data quality may lead to poorly targeted meeting',
          mitigation: 'Enrich contact data before scheduling',
        })
      }
      return risks
    },
    impact({ scores, context }) {
      const revenue = getScoreValue(scores, 'revenue')
      const opportunityValue = context.metadata?.opportunityValue as number | undefined
      const expectedRevenue = opportunityValue ? opportunityValue * 0.2 : revenue * 50000
      return {
        revenue: expectedRevenue,
        effort: 'low',
        time: '1-2 days',
        business: 'Advances deal stage, builds rapport with decision makers',
      }
    },
  },
  {
    action: 'send_proposal',
    actionLabel: 'Send Proposal',
    evaluate({ scores, rulesApplied }) {
      const relationship = getScoreValue(scores, 'relationship')
      const intent = getScoreValue(scores, 'intent')
      const revenue = getScoreValue(scores, 'revenue')
      if (relationship < 0.6 || intent < 0.5) return 0

      let score = relationship * 0.45 + intent * 0.3 + revenue * 0.25
      const proposalRule = rulesApplied.find(r => r.action === 'send_proposal')
      if (proposalRule) score += proposalRule.weight * 0.12
      return Math.min(score, 0.95)
    },
    risks({ scores }) {
      const company = getScoreValue(scores, 'company')
      const risks: Risk[] = []
      if (company < 0.4) {
        risks.push({
          type: 'poor_fit',
          level: 'high',
          description: 'Company profile suggests low fit for proposed solution',
          mitigation: 'Validate company requirements before sending proposal',
        })
      }
      if (getScoreValue(scores, 'risk') > 0.6) {
        risks.push({
          type: 'financial_risk',
          level: 'medium',
          description: 'Elevated risk score indicates potential payment or contract issues',
          mitigation: 'Request upfront commitment or shorter contract term',
        })
      }
      return risks
    },
    impact({ scores, context }) {
      const revenue = getScoreValue(scores, 'revenue')
      const opportunityValue = context.metadata?.opportunityValue as number | undefined
      const expectedRevenue = opportunityValue ? opportunityValue * 0.5 : revenue * 80000
      return {
        revenue: expectedRevenue,
        effort: 'medium',
        time: '3-5 days',
        business: 'Formalizes value proposition, moves deal to negotiation',
      }
    },
  },
  {
    action: 'call',
    actionLabel: 'Make Call',
    evaluate({ scores, rulesApplied }) {
      const intent = getScoreValue(scores, 'intent')
      const relationship = getScoreValue(scores, 'relationship')
      if (intent < 0.3 || intent > 0.75) return 0

      let score = intent * 0.4 + relationship * 0.35
      const callRule = rulesApplied.find(r => r.action === 'call')
      if (callRule) score += callRule.weight * 0.15
      const hasMeetingRule = rulesApplied.some(r => r.action === 'meeting')
      if (hasMeetingRule) score *= 0.7
      return Math.min(score, 0.85)
    },
    risks() {
      return [{
        type: 'timing',
        level: 'low',
        description: 'Call may interrupt the prospect at an inconvenient time',
        mitigation: 'Schedule call through calendar or email confirmation',
      }]
    },
    impact({ scores }) {
      const revenue = getScoreValue(scores, 'revenue')
      return {
        revenue: revenue * 20000,
        effort: 'low',
        time: '30 minutes',
        business: 'Re-engages prospect, gathers updated requirements',
      }
    },
  },
  {
    action: 'follow_up',
    actionLabel: 'Follow Up',
    evaluate({ scores, rulesApplied }) {
      const intent = getScoreValue(scores, 'intent')
      const dataQuality = getScoreValue(scores, 'data_quality')
      if (intent < 0.2) return 0

      let score = intent * 0.3 + dataQuality * 0.2 + 0.25
      const followUpRule = rulesApplied.find(r => r.action === 'follow_up')
      if (followUpRule) score += followUpRule.weight * 0.15
      return Math.min(score, 0.8)
    },
    risks() {
      return [{
        type: 'fatigue',
        level: 'low',
        description: 'Too many follow-ups may annoy the prospect',
        mitigation: 'Space follow-ups at least 5 business days apart',
      }]
    },
    impact({ scores }) {
      const revenue = getScoreValue(scores, 'revenue')
      return {
        revenue: revenue * 15000,
        effort: 'low',
        time: '1 day',
        business: 'Maintains engagement, prevents deal from going cold',
      }
    },
  },
  {
    action: 'demo',
    actionLabel: 'Product Demo',
    evaluate({ scores, rulesApplied }) {
      const intent = getScoreValue(scores, 'intent')
      const company = getScoreValue(scores, 'company')
      const relationship = getScoreValue(scores, 'relationship')
      if (intent < 0.4 || company < 0.4) return 0

      let score = intent * 0.35 + company * 0.35 + relationship * 0.2
      const demoRule = rulesApplied.find(r => r.action === 'demo')
      if (demoRule) score += demoRule.weight * 0.1
      if (getScoreValue(scores, 'revenue') > 0.6) score += 0.05
      return Math.min(score, 0.9)
    },
    risks({ scores }) {
      const risks: Risk[] = []
      if (getScoreValue(scores, 'data_quality') < 0.3) {
        risks.push({
          type: 'mismatched_expectations',
          level: 'medium',
          description: 'Insufficient data may lead to demo that does not address specific needs',
          mitigation: 'Conduct pre-demo discovery call',
        })
      }
      return risks
    },
    impact({ scores, context }) {
      const revenue = getScoreValue(scores, 'revenue')
      const opportunityValue = context.metadata?.opportunityValue as number | undefined
      const expectedRevenue = opportunityValue ? opportunityValue * 0.35 : revenue * 65000
      return {
        revenue: expectedRevenue,
        effort: 'medium',
        time: '2-3 days',
        business: 'Showcases value, qualifies technical fit',
      }
    },
  },
  {
    action: 'nurture',
    actionLabel: 'Nurture',
    evaluate({ scores }) {
      const intent = getScoreValue(scores, 'intent')
      const relationship = getScoreValue(scores, 'relationship')
      if (intent > 0.5 || relationship > 0.6) return 0

      const score = (1 - intent) * 0.4 + (1 - relationship) * 0.3 + 0.15
      return Math.min(score, 0.7)
    },
    risks() {
      return [{
        type: 'stagnation',
        level: 'medium',
        description: 'Long nurture cycles may result in lost opportunity',
        mitigation: 'Set quarterly review checkpoints with engagement triggers',
      }]
    },
    impact() {
      return {
        effort: 'low',
        time: 'ongoing',
        business: 'Builds long-term awareness, positions for future opportunities',
      }
    },
  },
  {
    action: 'escalate',
    actionLabel: 'Escalate',
    evaluate({ scores, rulesApplied }) {
      const revenue = getScoreValue(scores, 'revenue')
      const risk = getScoreValue(scores, 'risk')
      const intent = getScoreValue(scores, 'intent')
      if (revenue < 0.6 || risk < 0.4) return 0

      let score = revenue * 0.45 + risk * 0.35 + intent * 0.2
      const escalateRule = rulesApplied.find(r => r.action === 'escalate')
      if (escalateRule) score += escalateRule.weight * 0.2
      return Math.min(score, 0.9)
    },
    risks() {
      return [{
        type: 'process_disruption',
        level: 'medium',
        description: 'Escalation may disrupt normal workflow and stakeholder relationships',
        mitigation: 'Notify affected parties before escalation',
      }]
    },
    impact({ scores, context }) {
      const revenue = getScoreValue(scores, 'revenue')
      const opportunityValue = context.metadata?.opportunityValue as number | undefined
      const expectedRevenue = opportunityValue ?? revenue * 120000
      return {
        revenue: expectedRevenue,
        effort: 'high',
        time: '1 week',
        business: 'Resolves critical blockers, protects high-value opportunity',
      }
    },
  },
  {
    action: 'research',
    actionLabel: 'Research',
    evaluate({ scores }) {
      const dataQuality = getScoreValue(scores, 'data_quality')
      if (dataQuality > 0.6) return 0

      const score = (1 - dataQuality) * 0.6 + 0.2
      return Math.min(score, 0.75)
    },
    risks() {
      return [{
        type: 'delay',
        level: 'low',
        description: 'Research phase delays direct engagement with prospect',
        mitigation: 'Limit research to 48 hours, proceed with available data',
      }]
    },
    impact({ scores }) {
      return {
        effort: 'medium',
        time: '2 days',
        business: 'Improves data foundation, reduces risk of misinformed decisions',
      }
    },
  },
]

function assessRisks(
  context: DecisionContext,
  scores: Score[],
  rulesApplied: DecisionRule[],
  evidence: EvidenceItem[],
): Risk[] {
  const risks: Risk[] = []

  const riskScore = getScoreValue(scores, 'risk')
  if (riskScore > 0.7) {
    risks.push({
      type: 'overall_risk',
      level: 'critical',
      description: 'Overall risk score exceeds threshold — proceed with extreme caution',
      mitigation: 'Perform additional due diligence before any action',
    })
  } else if (riskScore > 0.5) {
    risks.push({
      type: 'overall_risk',
      level: 'medium',
      description: 'Moderate risk signals detected across multiple dimensions',
      mitigation: 'Monitor risk indicators closely during execution',
    })
  }

  const conflictingSignals = evidence.filter(
    e => e.severity === 'critical' || e.severity === 'high',
  )
  if (conflictingSignals.length > 2) {
    risks.push({
      type: 'conflicting_signals',
      level: 'high',
      description: `${conflictingSignals.length} high-severity signals may indicate conflicting data`,
      mitigation: 'Validate critical signals with primary source before acting',
    })
  }

  const dataQuality = getScoreValue(scores, 'data_quality')
  if (dataQuality < 0.3) {
    risks.push({
      type: 'data_quality',
      level: 'high',
      description: 'Very low data quality — recommendations may be unreliable',
      mitigation: 'Invest in data enrichment before making high-stakes decisions',
    })
  }

  const intent = getScoreValue(scores, 'intent')
  const relationship = getScoreValue(scores, 'relationship')
  if (intent > 0.7 && relationship < 0.3) {
    risks.push({
      type: 'readiness_mismatch',
      level: 'medium',
      description: 'High intent with low relationship readiness — risk of premature push',
      mitigation: 'Invest in relationship building before advancing the deal',
    })
  }

  if (rulesApplied.length === 0) {
    risks.push({
      type: 'no_rules',
      level: 'low',
      description: 'No decision rules were triggered — recommendation is purely score-based',
      mitigation: 'Review rule configuration for completeness',
    })
  }

  return risks
}

function buildSource(
  rulesApplied: DecisionRule[],
  action: string,
  score: number,
): DecisionSource {
  const hasRule = rulesApplied.some(r => r.action === action)
  if (hasRule && score >= 0.6) return 'hybrid'
  if (hasRule) return 'rule'
  return 'ai'
}

function estimateRevenue(scores: Score[], context: DecisionContext): number | undefined {
  const revenueScore = getScoreValue(scores, 'revenue')
  const opportunityValue = context.metadata?.opportunityValue as number | undefined
  if (opportunityValue) return opportunityValue
  if (revenueScore > 0) return revenueScore * 100000
  return undefined
}

function selectEvidence(
  evidence: EvidenceItem[],
  action: string,
  limit: number = 5,
): EvidenceItem[] {
  const keywordsByAction: Record<string, string[]> = {
    meeting: ['meeting', 'call', 'decision', 'stakeholder', 'contact'],
    send_proposal: ['proposal', 'pricing', 'requirement', 'budget', 'timeline'],
    call: ['call', 'phone', 'connect', 'reconnect', 'outreach'],
    follow_up: ['follow', 'pending', 'email', 'response', 'stale'],
    demo: ['demo', 'evaluation', 'trial', 'technical', 'product'],
    nurture: ['awareness', 'content', 'early', 'education', 'interest'],
    escalate: ['escalate', 'blocker', 'critical', 'risk', 'executive'],
    research: ['research', 'data', 'company', 'industry', 'profile'],
  }

  const keywords = keywordsByAction[action] ?? []
  const matched = relevantEvidence(evidence, keywords)
  if (matched.length >= limit) return matched.slice(0, limit)

  const remaining = evidence.filter(e => !matched.includes(e))
  return [...matched, ...remaining].slice(0, limit)
}

function prioritizeRules(rulesApplied: DecisionRule[], action: string): DecisionRule[] {
  return rulesApplied
    .filter(r => r.action === action)
    .sort((a, b) => b.priority - a.priority)
}

function determinePriority(
  score: number,
  intent: number,
  revenue: number,
): number {
  if (score >= 0.8 && intent >= 0.7) return 1
  if (score >= 0.65 && revenue >= 0.5) return 2
  if (score >= 0.5) return 3
  return 4
}

export class RecommendationEngine {
  async generate(
    context: DecisionContext,
    scores: Score[],
    rulesApplied: DecisionRule[],
    evidence: EvidenceItem[],
  ): Promise<Recommendation> {
    const intent = getScoreValue(scores, 'intent')
    const revenue = getScoreValue(scores, 'revenue')

    const scoredActions = ACTION_DEFINITIONS
      .map(def => {
        const score = def.evaluate({ context, scores, rulesApplied, evidence })
        const risks = def.risks({ context, scores, rulesApplied, evidence })
        const impact = def.impact({ context, scores, rulesApplied, evidence })
        const source = buildSource(rulesApplied, def.action, score)
        const matchedEvidence = selectEvidence(evidence, def.action)

        return {
          def,
          score,
          risks,
          impact,
          source,
          matchedEvidence,
        }
      })
      .filter(a => a.score > 0)
      .sort((a, b) => b.score - a.score)

    if (scoredActions.length === 0) {
      const now = new Date().toISOString()
      return {
        id: generateId(),
        action: 'nurture',
        actionLabel: 'Nurture',
        reason: 'No strong signals detected — defaulting to nurture strategy',
        confidence: 0.3,
        confidenceLabel: 'low',
        source: 'rule',
        priority: 4,
        alternatives: [],
        evidence: evidence.slice(0, 3),
        risks: [{
          type: 'no_signal',
          level: 'medium',
          description: 'No actionable signals were detected from available data',
          mitigation: 'Collect more data points before making a recommendation',
        }],
        status: 'pending',
        createdAt: now,
        updatedAt: now,
      }
    }

    const primary = scoredActions[0]
    const alternatives: AlternativeRecommendation[] = scoredActions.slice(1, 4).map(a => ({
      action: a.def.action,
      actionLabel: a.def.actionLabel,
      reason: `Alternative to ${primary.def.actionLabel}: ${a.def.actionLabel} addresses a related need with lower confidence`,
      confidence: Math.round(a.score * 100) / 100,
      expectedRevenue: a.impact.revenue,
    }))

    const allRisks = [
      ...assessRisks(context, scores, rulesApplied, evidence),
      ...primary.risks,
    ]

    const now = new Date().toISOString()

    const recommendation: Recommendation = {
      id: generateId(),
      action: primary.def.action,
      actionLabel: primary.def.actionLabel,
      reason: buildReason(primary.def.action, scores, rulesApplied, intent),
      confidence: Math.round(primary.score * 100) / 100,
      confidenceLabel: confidenceLabel(primary.score),
      source: primary.source,
      priority: determinePriority(primary.score, intent, revenue),
      expectedRevenue: primary.impact.revenue,
      expectedEffort: primary.impact.effort,
      expectedTime: primary.impact.time,
      businessImpact: primary.impact.business,
      alternatives,
      evidence: primary.matchedEvidence,
      risks: allRisks,
      status: 'pending',
      createdAt: now,
      updatedAt: now,
    }

    return recommendation
  }
}

function buildReason(
  action: string,
  scores: Score[],
  rulesApplied: DecisionRule[],
  intent: number,
): string {
  const reasonsByAction: Record<string, string> = {
    meeting: `High intent score (${(intent * 100).toFixed(0)}%) and strong relationship indicate readiness for a direct meeting with decision makers`,
    send_proposal: 'Relationship and intent scores suggest the prospect is ready to receive a formal proposal with pricing and terms',
    call: 'Medium intent level indicates the prospect needs re-engagement — a direct call will gauge current interest and next steps',
    follow_up: 'Pending activity detected — a timely follow-up will keep momentum and prevent the opportunity from going cold',
    demo: 'Prospect shows sufficient interest and company fit for a product demonstration to validate technical requirements',
    nurture: 'Early-stage signals with low urgency — best served through content-based nurturing until intent develops',
    escalate: 'High-value opportunity with elevated risk requires immediate executive attention to prevent loss',
    research: 'Low data quality score indicates insufficient information — research will improve decision confidence',
  }

  const baseReason = reasonsByAction[action] ?? `Recommended action based on score analysis`

  const rule = rulesApplied.find(r => r.action === action)
  if (rule) {
    return `${baseReason}. Triggered by rule: "${rule.name}" (${rule.description})`
  }

  return baseReason
}
