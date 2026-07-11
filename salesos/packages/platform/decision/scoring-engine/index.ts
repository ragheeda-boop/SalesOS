import type { Score, ScoreFactor, ScoreType } from '../contracts'

interface FactorConfig {
  name: string
  weight: number
  description: string
}

const SCORE_CONFIGS: Record<ScoreType, FactorConfig[]> = {
  company: [
    { name: 'financial_health', weight: 0.3, description: 'Financial stability and health indicators' },
    { name: 'growth_trend', weight: 0.2, description: 'Revenue and employee growth trajectory' },
    { name: 'digital_presence', weight: 0.15, description: 'Online footprint and digital maturity' },
    { name: 'hiring_trend', weight: 0.15, description: 'Recruitment activity and headcount changes' },
    { name: 'procurement_maturity', weight: 0.2, description: 'Procurement process sophistication' },
  ],
  opportunity: [
    { name: 'stage_weight', weight: 0.3, description: 'Current pipeline stage progression' },
    { name: 'estimated_value', weight: 0.15, description: 'Projected deal value' },
    { name: 'buying_intent', weight: 0.25, description: 'Signals indicating purchase readiness' },
    { name: 'relationship_strength', weight: 0.2, description: 'Depth of stakeholder engagement' },
    { name: 'confidence', weight: 0.1, description: 'Overall evaluation confidence' },
  ],
  intent: [
    { name: 'signal_activity', weight: 0.3, description: 'Volume and intensity of buying signals' },
    { name: 'hiring_trend', weight: 0.2, description: 'Related hiring patterns' },
    { name: 'government_exposure', weight: 0.15, description: 'Government contract activity' },
    { name: 'expansion_potential', weight: 0.2, description: 'Market expansion indicators' },
    { name: 'digital_engagement', weight: 0.15, description: 'Digital interaction frequency' },
  ],
  relationship: [
    { name: 'connection_count', weight: 0.3, description: 'Number of established connections' },
    { name: 'decision_maker_access', weight: 0.25, description: 'Access to key decision makers' },
    { name: 'interaction_recency', weight: 0.2, description: 'How recent the last interaction was' },
    { name: 'meeting_frequency', weight: 0.15, description: 'Cadence of scheduled meetings' },
    { name: 'email_engagement', weight: 0.1, description: 'Email open and reply rates' },
  ],
  risk: [
    { name: 'risk_level_raw', weight: 0.3, description: 'Baseline risk assessment' },
    { name: 'financial_volatility', weight: 0.2, description: 'Financial stability variance' },
    { name: 'market_volatility', weight: 0.15, description: 'Market condition fluctuations' },
    { name: 'competitive_threat', weight: 0.15, description: 'Competitive pressure intensity' },
    { name: 'regulatory_exposure', weight: 0.2, description: 'Regulatory compliance risk' },
  ],
  revenue: [
    { name: 'estimated_value', weight: 0.35, description: 'Projected revenue value' },
    { name: 'win_probability', weight: 0.3, description: 'Likelihood of closing the deal' },
    { name: 'expansion_potential', weight: 0.2, description: 'Upsell and cross-sell opportunity' },
    { name: 'cross_sell', weight: 0.15, description: 'Adjacent product fit' },
  ],
  data_quality: [
    { name: 'freshness', weight: 0.3, description: 'How current the underlying data is' },
    { name: 'source_count', weight: 0.2, description: 'Number of corroborating sources' },
    { name: 'conflict_count', weight: 0.25, description: 'Contradictions across data sources' },
    { name: 'completeness', weight: 0.25, description: 'Coverage of required data fields' },
  ],
  confidence: [
    { name: 'data_quality', weight: 0.4, description: 'Quality of underlying data' },
    { name: 'evidence_count', weight: 0.3, description: 'Volume of supporting evidence' },
    { name: 'source_reliability', weight: 0.3, description: 'Trustworthiness of data sources' },
  ],
}

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substring(2)
}

function clamp(value: number): number {
  return Math.max(0, Math.min(1, value))
}

function getLabel(value: number): string {
  if (value >= 0.9) return 'excellent'
  if (value >= 0.7) return 'good'
  if (value >= 0.5) return 'moderate'
  if (value >= 0.3) return 'low'
  return 'poor'
}

function computeConfidence(factors: ScoreFactor[]): number {
  if (factors.length === 0) return 0
  const totalWeight = factors.reduce((sum, f) => sum + f.weight, 0)
  if (totalWeight === 0) return 0
  const coverage = Math.min(factors.length / 3, 1)
  const avgValue = factors.reduce((sum, f) => sum + f.value * f.weight, 0) / totalWeight
  return clamp(coverage * 0.6 + avgValue * 0.4)
}

export class ScoringEngine {
  score(type: ScoreType, factors: Record<string, number>, metadata?: Record<string, unknown>): Score {
    const config = SCORE_CONFIGS[type]
    if (!config) {
      throw new Error(`Unknown score type: ${type}`)
    }

    const source = (metadata?.source as string) ?? type
    const scoredFactors: ScoreFactor[] = []

    for (const cfg of config) {
      const raw = factors[cfg.name] ?? 0
      const normalized = clamp(raw)
      scoredFactors.push({
        name: cfg.name,
        value: normalized,
        weight: cfg.weight,
        description: cfg.description,
        source,
      })
    }

    const totalWeight = scoredFactors.reduce((sum, f) => sum + f.weight, 0)
    const value = totalWeight > 0
      ? clamp(scoredFactors.reduce((sum, f) => sum + f.value * f.weight, 0) / totalWeight)
      : 0

    const confidence = computeConfidence(scoredFactors)

    return {
      type,
      value,
      confidence,
      label: getLabel(value),
      factors: scoredFactors,
      timestamp: new Date().toISOString(),
    }
  }

  scoreAll(factors: Record<string, Record<string, number>>): Score[] {
    const scores: Score[] = []
    for (const type of Object.keys(factors) as ScoreType[]) {
      if (type in SCORE_CONFIGS) {
        scores.push(this.score(type, factors[type]))
      }
    }
    return scores
  }
}

export { SCORE_CONFIGS, generateId }
