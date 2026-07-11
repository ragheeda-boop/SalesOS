import type { CompanyDNA, AIRecommendation, TimelineEvent, SignalItem, DecisionMaker } from '@/application/company-intelligence/company-intelligence.dto'
import type { NextBestAction } from './nba.dto'

const PLAYBOOKS: Record<string, string> = {
  energy: 'playbook-energy',
  technology: 'playbook-tech',
  healthcare: 'playbook-health',
  finance: 'playbook-finance',
  manufacturing: 'playbook-manufacturing',
  government: 'playbook-government',
}

function computePriority(intent: number, relationship: number, financial: number): NextBestAction['priority'] {
  const s = intent * 0.4 + relationship * 0.3 + financial * 0.3
  if (s >= 70) return 'critical'
  if (s >= 50) return 'high'
  if (s >= 30) return 'medium'
  return 'low'
}

function computeScore(intent: number, relationship: number, confidence: number): number {
  return Math.round((intent * 0.4 + relationship * 0.35 + confidence * 0.25) * 100) / 100
}

export function deriveNextBestAction(
  dna: CompanyDNA | null,
  recommendation: AIRecommendation | null,
  _timeline: TimelineEvent[],
  _signals: SignalItem[],
  _makers: DecisionMaker[],
): NextBestAction | null {
  if (!dna) return null

  const intent = dna.buyingIntent?.score ?? 0
  const relationship = dna.relationshipStrength?.score ?? 0
  const financial = dna.financialHealth?.score ?? 0
  const confidence = dna.confidenceScore ?? 0
  const industry = dna.industry ?? ''

  const priority = computePriority(intent, relationship, financial)
  const score = computeScore(intent, relationship, confidence)

  return {
    actionId: crypto.randomUUID?.() ?? `${Date.now()}-${Math.random()}`,
    actionLabel: recommendation?.actionLabel ?? 'متابعة',
    actionType: recommendation?.action === 'meeting' ? 'meeting' : 'follow_up',
    reasoning: recommendation?.reasoning ?? `${dna.industry} - متابعة محتملة`,
    confidence: recommendation?.confidence ?? 0.5,
    priority,
    score,
    expectedRevenue: recommendation?.expectedRevenue ?? 50000,
    expectedImpact: (recommendation?.expectedImpact as NextBestAction['expectedImpact']) ?? 'medium',
    estimatedTime: recommendation?.estimatedTime ?? '',
    contextSummary: '',
    risks: recommendation?.risks ?? [],
    alternatives: recommendation?.alternatives?.map(a => ({ actionLabel: a.actionLabel, confidence: a.confidence })) ?? [],
    createsOpportunity: score >= 0.5,
    playbookId: PLAYBOOKS[industry] ?? 'playbook-default',
    scoreBreakdown: {
      buyingIntent: intent / 100,
      relationshipStrength: relationship / 100,
      signalRecency: 0,
      aiConfidence: confidence,
      decisionMakerAccess: 0,
      revenuePotential: 0,
    },
  }
}
