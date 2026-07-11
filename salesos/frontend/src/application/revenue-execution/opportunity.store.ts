import api from '@/lib/api'
import type { RevenueOpportunity, OpportunityStage } from './opportunity.dto'

export async function loadOpportunities(): Promise<RevenueOpportunity[]> {
  try {
    const response = await api.get('/api/v1/revenue-execution/opportunities')
    return response.data.items ?? response.data ?? []
  } catch {
    return []
  }
}

export async function saveOpportunities(opps: RevenueOpportunity[]): Promise<void> {
  try {
    await api.put('/api/v1/revenue-execution/opportunities', opps)
  } catch { /* ignore */ }
}

export async function createOpportunity(input: {
  companyId: string
  companyName: string
  title: string
  estimatedValue: number
  confidence: number
  buyingIntent: number
  relationshipStrength: number
  sourceActionId?: string
}): Promise<RevenueOpportunity> {
  const response = await api.post('/api/v1/revenue-execution/opportunities', input)
  return response.data
}

export async function updateOpportunityStage(id: string, stage: OpportunityStage): Promise<RevenueOpportunity[]> {
  const response = await api.patch(`/api/v1/revenue-execution/opportunities/${id}/stage`, { stage })
  return response.data.items ?? [response.data]
}

export async function addOpportunityNote(id: string, text: string, author: string): Promise<RevenueOpportunity[]> {
  const response = await api.post(`/api/v1/revenue-execution/opportunities/${id}/notes`, { text, author })
  return response.data.items ?? [response.data]
}

export function getOpportunitiesByStage(opps: RevenueOpportunity[], stage?: OpportunityStage): RevenueOpportunity[] {
  if (!stage) return opps
  return opps.filter((o) => o.stage === stage)
}

export async function getOpportunity(id: string): Promise<RevenueOpportunity | undefined> {
  const opps = await loadOpportunities()
  return opps.find((o) => o.id === id)
}
