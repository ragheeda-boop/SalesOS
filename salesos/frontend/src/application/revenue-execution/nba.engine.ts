import type { NextBestAction, NBActionType, NBAPriority } from './nba.dto'
import type { CompanyDNA, AIRecommendation, TimelineEvent, SignalItem, DecisionMaker } from '@/application/company-intelligence/company-intelligence.dto'

const WEIGHTS = {
  buyingIntent: 0.35,
  relationshipStrength: 0.20,
  signalRecency: 0.15,
  aiConfidence: 0.15,
  decisionMakerAccess: 0.10,
  revenuePotential: 0.05,
}

function scoreBuyingIntent(dna: CompanyDNA): number {
  return dna.buyingIntent.score / 100
}

function scoreRelationshipStrength(dna: CompanyDNA): number {
  return dna.relationshipStrength.score / 100
}

function scoreSignalRecency(signals: SignalItem[]): number {
  if (signals.length === 0) return 0
  const now = Date.now()
  const maxScore = Math.min(1, signals.filter((s) => {
    const age = now - new Date(s.timestamp).getTime()
    return age < 7 * 24 * 60 * 60 * 1000 && (s.severity === 'high' || s.severity === 'critical')
  }).length / 5)
  return maxScore
}

function scoreDecisionMakerAccess(makers: DecisionMaker[]): number {
  if (makers.length === 0) return 0
  const connected = makers.filter((m) => m.connected).length
  const highInfluence = makers.filter((m) => m.influence === 'high').length
  return Math.min(1, (connected * 0.4 + highInfluence * 0.6) / makers.length)
}

function scoreRevenuePotential(dna: CompanyDNA): number {
  return Math.min(1, dna.financialHealth.revenue / 10_000_000_000)
}

function pickPriority(score: number): NBAPriority {
  if (score >= 0.80) return 'critical'
  if (score >= 0.60) return 'high'
  if (score >= 0.40) return 'medium'
  return 'low'
}

function pickActionType(dna: CompanyDNA, recommendation: AIRecommendation | null): NBActionType {
  if (!recommendation) return 'review'
  if (dna.buyingIntent.intent === 'high') return 'meeting'
  if (dna.buyingIntent.intent === 'medium') return 'demo'
  return 'review'
}

function findTriggerEvent(timeline: TimelineEvent[], signals: SignalItem[]): string | undefined {
  const recent = [...timeline, ...signals.map((s) => ({ id: s.id, type: 'signal' as const, summary: s.title, date: s.timestamp, source: s.source, aiHighlighted: false }))]
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
  return recent[0]?.summary
}

const ACTION_LABELS: Record<NBActionType, string> = {
  call: 'اتصال هاتفي',
  meeting: 'ترتيب اجتماع',
  demo: 'تقديم عرض توضيحي',
  proposal: 'إرسال عرض',
  follow_up: 'متابعة',
  event: 'دعوة لفعالية',
  review: 'مراجعة الحساب',
  custom: 'إجراء مخصص',
}

export function deriveNextBestAction(
  dna: CompanyDNA | null,
  recommendation: AIRecommendation | null,
  timeline: TimelineEvent[],
  signals: SignalItem[],
  makers: DecisionMaker[],
): NextBestAction | null {
  if (!dna) return null

  const bi = scoreBuyingIntent(dna)
  const rs = scoreRelationshipStrength(dna)
  const sr = scoreSignalRecency(signals)
  const ac = recommendation?.confidence ?? 0.5
  const dm = scoreDecisionMakerAccess(makers)
  const rp = scoreRevenuePotential(dna)

  const score = Math.min(1,
    WEIGHTS.buyingIntent * bi +
    WEIGHTS.relationshipStrength * rs +
    WEIGHTS.signalRecency * sr +
    WEIGHTS.aiConfidence * ac +
    WEIGHTS.decisionMakerAccess * dm +
    WEIGHTS.revenuePotential * rp
  )

  const actionType = recommendation
    ? (recommendation.action as NBActionType)
    : pickActionType(dna, recommendation)

  return {
    actionId: `nba_${Date.now()}`,
    actionLabel: recommendation?.actionLabel ?? ACTION_LABELS[actionType],
    actionType,
    reasoning: recommendation?.reasoning ?? `فرصة في ${dna.industry} مع نية شراء ${dna.buyingIntent.intent === 'high' ? 'عالية' : dna.buyingIntent.intent}`,
    confidence: Math.round(score * 100) / 100,
    priority: pickPriority(score),
    score: Math.round(score * 100) / 100,
    expectedRevenue: recommendation?.expectedRevenue ?? Math.round(dna.financialHealth.revenue * 0.01),
    expectedImpact: recommendation?.expectedImpact ?? 'medium',
    estimatedTime: recommendation?.estimatedTime ?? 'شهر',
    contextSummary: dna.growthPattern === 'accelerating'
      ? `الشركة في حالة نمو ${dna.growthPattern === 'accelerating' ? 'متسارع' : 'مستقر'} مع ${dna.size.employees.toLocaleString()} موظف`
      : `شركة في قطاع ${dna.industry} بحجم ${dna.size.label}`,
    triggerEvent: findTriggerEvent(timeline, signals),
    risks: recommendation?.risks ?? ['مخاطر غير معروفة — يوصى بمراجعة الحساب'],
    alternatives: recommendation?.alternatives ?? [],
    playbookId: dna.industry === 'healthcare' ? 'playbook-healthcare' : dna.industry === 'energy' ? 'playbook-energy' : 'playbook-general',
    createsOpportunity: score >= 0.40,
    scoreBreakdown: {
      buyingIntent: bi,
      relationshipStrength: rs,
      signalRecency: sr,
      aiConfidence: ac,
      decisionMakerAccess: dm,
      revenuePotential: rp,
    },
  }
}
