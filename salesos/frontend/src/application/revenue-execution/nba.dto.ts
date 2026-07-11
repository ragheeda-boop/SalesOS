export type NBActionType = 'call' | 'meeting' | 'demo' | 'proposal' | 'follow_up' | 'event' | 'review' | 'custom'
export type NBAPriority = 'critical' | 'high' | 'medium' | 'low'

export interface NextBestAction {
  actionId: string
  actionLabel: string
  actionType: NBActionType
  reasoning: string
  confidence: number
  priority: NBAPriority
  score: number
  expectedRevenue: number
  expectedImpact: 'low' | 'medium' | 'high'
  estimatedTime: string
  contextSummary: string
  triggerEvent?: string
  risks: string[]
  alternatives: { actionLabel: string; confidence: number }[]
  playbookId?: string
  createsOpportunity: boolean
  scoreBreakdown: {
    buyingIntent: number
    relationshipStrength: number
    signalRecency: number
    aiConfidence: number
    decisionMakerAccess: number
    revenuePotential: number
  }
}
