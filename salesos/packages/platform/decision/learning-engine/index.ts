import type { LearningEvent } from '../contracts/index'

export interface QualityMetrics {
  averageConfidence: number
  averageAcceptanceRate: number
  totalRecommendations: number
  highConfidenceRate: number
  mediumConfidenceRate: number
  lowConfidenceRate: number
}

export interface RuleEffectiveness {
  ruleId: string
  ruleName: string
  timesApplied: number
  acceptanceRate: number
  averageConfidence: number
}

export interface SignalUsefulness {
  signalType: string
  frequency: number
  correlationWithAcceptance: number
}

export interface LearningTrend {
  metric: string
  currentValue: number
  previousValue: number
  trend: 'up' | 'down' | 'stable'
  changePercent: number
}

const ONE_DAY_MS = 86_400_000

interface StoredEvent {
  tenantId: string
  event: LearningEvent
}

function computeTrend(current: number, previous: number): 'up' | 'down' | 'stable' {
  const delta = current - previous
  const threshold = Math.max(Math.abs(previous) * 0.05, 0.001)
  if (delta > threshold) return 'up'
  if (delta < -threshold) return 'down'
  return 'stable'
}

export class LearningEngine {
  private store: StoredEvent[] = []

  async record(event: LearningEvent): Promise<void> {
    this.store.push({ tenantId: '', event })
  }

  async recordWithTenant(event: LearningEvent, tenantId: string): Promise<void> {
    this.store.push({ tenantId, event })
  }

  private filterByTenant(tenantId: string): LearningEvent[] {
    return this.store
      .filter(s => s.tenantId === tenantId)
      .map(s => s.event)
  }

  async getRecommendationQuality(tenantId: string): Promise<QualityMetrics> {
    const events = this.filterByTenant(tenantId)
    const qualityEvents = events.filter(e => e.type === 'recommendation_quality')

    if (qualityEvents.length === 0) {
      return {
        averageConfidence: 0,
        averageAcceptanceRate: 0,
        totalRecommendations: 0,
        highConfidenceRate: 0,
        mediumConfidenceRate: 0,
        lowConfidenceRate: 0,
      }
    }

    const total = qualityEvents.length
    const averageConfidence =
      qualityEvents.reduce((sum, e) => sum + (e.factors.confidence ?? e.value), 0) / total

    const acceptanceEvents = events.filter(e => e.type === 'acceptance_rate')
    const averageAcceptanceRate = acceptanceEvents.length > 0
      ? acceptanceEvents.reduce((sum, e) => sum + e.value, 0) / acceptanceEvents.length
      : 0

    const highCount = qualityEvents.filter(e => (e.factors.confidence ?? e.value) >= 0.8).length
    const mediumCount = qualityEvents.filter(
      e => (e.factors.confidence ?? e.value) >= 0.5 && (e.factors.confidence ?? e.value) < 0.8,
    ).length
    const lowCount = qualityEvents.filter(e => (e.factors.confidence ?? e.value) < 0.5).length

    return {
      averageConfidence,
      averageAcceptanceRate,
      totalRecommendations: total,
      highConfidenceRate: total > 0 ? highCount / total : 0,
      mediumConfidenceRate: total > 0 ? mediumCount / total : 0,
      lowConfidenceRate: total > 0 ? lowCount / total : 0,
    }
  }

  async getAcceptanceRate(tenantId: string, days: number = 30): Promise<number> {
    const events = this.filterByTenant(tenantId)
    const cutoff = Date.now() - days * ONE_DAY_MS

    const acceptanceEvents = events.filter(
      e =>
        e.type === 'acceptance_rate' &&
        new Date(e.timestamp).getTime() >= cutoff,
    )

    if (acceptanceEvents.length === 0) return 0
    return acceptanceEvents.reduce((sum, e) => sum + e.value, 0) / acceptanceEvents.length
  }

  async getRuleEffectiveness(tenantId: string): Promise<RuleEffectiveness[]> {
    const events = this.filterByTenant(tenantId)
    const ruleEvents = events.filter(e => e.type === 'rule_effectiveness')

    if (ruleEvents.length === 0) return []

    const grouped = new Map<number, LearningEvent[]>()
    for (const event of ruleEvents) {
      const ruleId = event.factors.ruleId ?? 0
      const existing = grouped.get(ruleId) ?? []
      existing.push(event)
      grouped.set(ruleId, existing)
    }

    const results: RuleEffectiveness[] = []
    for (const [ruleId, group] of grouped) {
      const timesApplied = group.length
      const acceptanceCount = group.filter(e => e.value >= 0.7).length
      const acceptanceRate = timesApplied > 0 ? acceptanceCount / timesApplied : 0
      const averageConfidence =
        group.reduce((sum, e) => sum + (e.factors.confidence ?? 0), 0) / timesApplied

      results.push({
        ruleId: String(ruleId),
        ruleName: `Rule ${ruleId}`,
        timesApplied,
        acceptanceRate,
        averageConfidence,
      })
    }

    results.sort((a, b) => b.timesApplied * b.acceptanceRate - a.timesApplied * a.acceptanceRate)
    return results
  }

  async getSignalUsefulness(tenantId: string): Promise<SignalUsefulness[]> {
    const events = this.filterByTenant(tenantId)
    const signalEvents = events.filter(e => e.type === 'signal_usefulness')

    if (signalEvents.length === 0) return []

    const grouped = new Map<number, LearningEvent[]>()
    for (const event of signalEvents) {
      const signalType = event.factors.signalType ?? 0
      const existing = grouped.get(signalType) ?? []
      existing.push(event)
      grouped.set(signalType, existing)
    }

    const results: SignalUsefulness[] = []
    for (const [signalType, group] of grouped) {
      const frequency = group.length
      const positiveCount = group.filter(e => e.value > 0.5).length
      const correlationWithAcceptance = frequency > 0 ? positiveCount / frequency : 0

      results.push({
        signalType: `signal_${signalType}`,
        frequency,
        correlationWithAcceptance,
      })
    }

    results.sort((a, b) => b.correlationWithAcceptance - a.correlationWithAcceptance)
    return results
  }

  async getTrends(tenantId: string): Promise<LearningTrend[]> {
    const events = this.filterByTenant(tenantId)
    const now = Date.now()
    const periodDays = 7
    const currentStart = now - periodDays * ONE_DAY_MS
    const previousStart = currentStart - periodDays * ONE_DAY_MS

    const currentEvents = events.filter(
      e => new Date(e.timestamp).getTime() >= currentStart,
    )
    const previousEvents = events.filter(e => {
      const t = new Date(e.timestamp).getTime()
      return t >= previousStart && t < currentStart
    })

    const avgValue = (evts: LearningEvent[]) =>
      evts.length > 0 ? evts.reduce((s, e) => s + e.value, 0) / evts.length : 0

    const trendDefs = [
      { metric: 'acceptance_rate', type: 'acceptance_rate' as const },
      { metric: 'recommendation_quality', type: 'recommendation_quality' as const },
      { metric: 'rule_effectiveness', type: 'rule_effectiveness' as const },
      { metric: 'signal_usefulness', type: 'signal_usefulness' as const },
    ]

    return trendDefs.map(({ metric, type }) => {
      const curr = avgValue(currentEvents.filter(e => e.type === type))
      const prev = avgValue(previousEvents.filter(e => e.type === type))

      return {
        metric,
        currentValue: curr,
        previousValue: prev,
        trend: computeTrend(curr, prev),
        changePercent: prev !== 0 ? ((curr - prev) / Math.abs(prev)) * 100 : curr > 0 ? 100 : 0,
      }
    })
  }
}
