import type {
  DecisionContext,
  Explainability,
  Recommendation,
  EvidenceItem,
  DecisionRule,
  Score,
  RiskLevel,
} from '../contracts/index'

function isArabic(context: DecisionContext): boolean {
  return context.metadata?.locale === 'ar'
}

function pickTop(scores: Score[], n: number): Score[] {
  return [...scores].sort((a, b) => (b.value * b.confidence) - (a.value * a.confidence)).slice(0, n)
}

function pickTopEvidence(evidence: EvidenceItem[], n: number): EvidenceItem[] {
  return [...evidence].sort((a, b) => b.confidence - a.confidence).slice(0, n)
}

function highestRisk(recommendation: Recommendation): RiskLevel {
  const order: RiskLevel[] = ['critical', 'high', 'medium', 'low']
  if (!recommendation.risks.length) return 'low'
  return recommendation.risks.reduce<RiskLevel>((highest, r) => {
    return order.indexOf(r.level) < order.indexOf(highest) ? r.level : highest
  }, 'low')
}

function formatScoreSummary(score: Score, arabic: boolean): string {
  const label = score.label
  const pct = Math.round(score.value * 100)
  if (arabic) {
    return `${label} بنسبة ${pct}%`
  }
  return `${label} at ${pct}%`
}

function buildWhy(
  context: DecisionContext,
  recommendation: Recommendation,
  scores: Score[],
  evidence: EvidenceItem[],
  arabic: boolean
): string {
  const topScores = pickTop(scores, 3)
  const topEvidence = pickTopEvidence(evidence, 2)
  const scorePart = topScores.map(s => formatScoreSummary(s, arabic)).join(arabic ? ' و' : ' and ')
  const evidencePart = topEvidence.map(e => e.description).join(arabic ? ' و' : ' and ')

  if (arabic) {
    let text = `توصية بـ ${recommendation.actionLabel} بسبب ${recommendation.reason}.`
    if (scorePart) text += ` ${scorePart}.`
    if (evidencePart) text += ` الدليل الرئيسي: ${evidencePart}.`
    return text
  }

  let text = `Recommendation to ${recommendation.actionLabel} due to ${recommendation.reason}.`
  if (scorePart) text += ` Key scores: ${scorePart}.`
  if (evidencePart) text += ` Primary evidence: ${evidencePart}.`
  return text
}

function buildWhyNow(
  context: DecisionContext,
  recommendation: Recommendation,
  rulesApplied: DecisionRule[],
  evidence: EvidenceItem[],
  arabic: boolean
): string {
  const recentEvidence = evidence
    .filter(e => {
      const ts = new Date(e.timestamp).getTime()
      const daysAgo = (Date.now() - ts) / (1000 * 60 * 60 * 24)
      return daysAgo <= 30
    })
    .slice(0, 3)

  const recentSignals = recentEvidence
    .filter(e => e.type === 'signal' || e.type === 'timeline')
    .map(e => e.description)

  const triggeredRules = rulesApplied
    .sort((a, b) => b.priority - a.priority)
    .slice(0, 2)
    .map(r => r.name)

  if (arabic) {
    const parts: string[] = []
    if (recentSignals.length) {
      parts.push(`إشارة حديثة: ${recentSignals.join(' و')}`)
    }
    if (triggeredRules.length) {
      parts.push(`قواعد مفعّلة: ${triggeredRules.join(' و')}`)
    }
    if (!parts.length) {
      return 'الآن لأن البيانات الحالية تدعم هذا التوصية.'
    }
    return `الآن لأن ${parts.join(' و')}.`
  }

  const parts: string[] = []
  if (recentSignals.length) {
    parts.push(`recent signal: ${recentSignals.join(', ')}`)
  }
  if (triggeredRules.length) {
    parts.push(`triggered rules: ${triggeredRules.join(', ')}`)
  }
  if (!parts.length) {
    return 'Right now because current data supports this recommendation.'
  }
  return `Right now due to ${parts.join(' and ')}.`
}

function buildWhyThisAction(
  context: DecisionContext,
  recommendation: Recommendation,
  scores: Score[],
  arabic: boolean
): string {
  const topScore = pickTop(scores, 1)[0]
  const altCount = recommendation.alternatives.length
  const scoreRef = topScore ? formatScoreSummary(topScore, arabic) : ''

  if (arabic) {
    let text = `هذا الإجراء هو الأفضل لأنه ${recommendation.reason}.`
    if (scoreRef) text += ` التقييم الأعلى: ${scoreRef}.`
    if (altCount > 0) text += ` تمت مقارنته مع ${altCount} ${altCount > 1 ? 'بدائل' : 'بديل'} واختيار هذا بناءً على الأعلى ثقةً وتأثيراً.`
    if (recommendation.expectedRevenue) {
      text += ` الإيراد المتوقع: ${recommendation.expectedRevenue.toLocaleString('ar-SA')} ريال.`
    }
    return text
  }

  let text = `This action is optimal because ${recommendation.reason}.`
  if (scoreRef) text += ` Highest score: ${scoreRef}.`
  if (altCount > 0) text += ` Compared against ${altCount} alternative${altCount !== 1 ? 's' : ''} and selected for highest confidence and impact.`
  if (recommendation.expectedRevenue) {
    text += ` Expected revenue: ${recommendation.expectedRevenue.toLocaleString('en-US')}.`
  }
  return text
}

function buildWhyNotAlternatives(
  recommendation: Recommendation,
  arabic: boolean
): string[] {
  return recommendation.alternatives.map(alt => {
    if (arabic) {
      return `${alt.actionLabel} لم يتم اختياره لأن ${alt.reason}. ثقته ${Math.round(alt.confidence * 100)}% مقابل ${Math.round(recommendation.confidence * 100)}% للخيار الحالي.`
    }
    return `${alt.actionLabel} was not chosen because ${alt.reason}. Confidence: ${Math.round(alt.confidence * 100)}% vs ${Math.round(recommendation.confidence * 100)}% for the selected action.`
  })
}

export class ExplainabilityEngine {
  async explain(
    context: DecisionContext,
    recommendation: Recommendation,
    scores: Score[],
    rulesApplied: DecisionRule[],
    evidence: EvidenceItem[]
  ): Promise<Explainability> {
    const arabic = isArabic(context)
    const topEvidence = pickTopEvidence(evidence, 5)

    return {
      why: buildWhy(context, recommendation, scores, evidence, arabic),
      whyNow: buildWhyNow(context, recommendation, rulesApplied, evidence, arabic),
      whyThisAction: buildWhyThisAction(context, recommendation, scores, arabic),
      whyNotAlternative: buildWhyNotAlternatives(recommendation, arabic),
      evidence: topEvidence,
      rulesApplied: [...rulesApplied],
      aiReasoning: null,
      confidence: recommendation.confidence,
      risk: highestRisk(recommendation),
      expectedImpact: {
        revenue: recommendation.expectedRevenue ?? 0,
        timeframe: recommendation.expectedTime ?? 'unknown',
      },
    }
  }
}
