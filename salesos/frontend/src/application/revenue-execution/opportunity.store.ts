import type { RevenueOpportunity, OpportunityStage } from './opportunity.dto'

const STORAGE_KEY = 'salesos_opportunities'

export function loadOpportunities(): RevenueOpportunity[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  } catch { return [] }
}

export function saveOpportunities(opps: RevenueOpportunity[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(opps))
  } catch { /* ignore */ }
}

export function createOpportunity(input: {
  companyId: string
  companyName: string
  title: string
  estimatedValue: number
  confidence: number
  buyingIntent: number
  relationshipStrength: number
  sourceActionId?: string
}): RevenueOpportunity {
  const opp: RevenueOpportunity = {
    id: `opp_${Date.now()}`,
    companyId: input.companyId,
    companyName: input.companyName,
    title: input.title,
    source: 'nba',
    sourceActionId: input.sourceActionId,
    estimatedValue: input.estimatedValue,
    confidence: input.confidence,
    winProbability: 0.10,
    stage: 'identified',
    createdAt: new Date().toISOString(),
    buyingIntent: input.buyingIntent,
    relationshipStrength: input.relationshipStrength,
    riskLevel: input.confidence >= 0.8 ? 'low' : input.confidence >= 0.5 ? 'medium' : 'high',
    tags: [],
    notes: [],
    lastActivityAt: new Date().toISOString(),
  }
  saveOpportunities([opp, ...loadOpportunities()])
  return opp
}

export function updateOpportunityStage(id: string, stage: OpportunityStage): RevenueOpportunity[] {
  const opps = loadOpportunities()
  const updated = opps.map((o) =>
    o.id === id
      ? { ...o, stage, stageChangedAt: new Date().toISOString(), lastActivityAt: new Date().toISOString() }
      : o
  )
  saveOpportunities(updated)
  return updated
}

export function addOpportunityNote(id: string, text: string, author: string): RevenueOpportunity[] {
  const opps = loadOpportunities()
  const updated = opps.map((o) =>
    o.id === id
      ? { ...o, notes: [...o.notes, { id: `note_${Date.now()}`, text, createdAt: new Date().toISOString(), author }], lastActivityAt: new Date().toISOString() }
      : o
  )
  saveOpportunities(updated)
  return updated
}

export function getOpportunitiesByStage(opps: RevenueOpportunity[], stage?: OpportunityStage): RevenueOpportunity[] {
  if (!stage) return opps
  return opps.filter((o) => o.stage === stage)
}

export function getOpportunity(id: string): RevenueOpportunity | undefined {
  return loadOpportunities().find((o) => o.id === id)
}
