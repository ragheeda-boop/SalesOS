export interface CompanyFirmographic {
  nameAr: string
  nameEn: string
  crNumber: string
  city: string
  region: string
  status: string
  industry: string
  employees: number
  foundedYear: number
  businessModel: 'b2b' | 'b2c' | 'b2g' | 'hybrid'
}

export interface CompanyDNA {
  industry: string
  businessModel: string
  size: { employees: number; revenue: string; label: 'small' | 'medium' | 'large' | 'enterprise' }
  growthPattern: 'declining' | 'stable' | 'growing' | 'accelerating'
  buyingBehaviour: { score: number; intent: 'low' | 'medium' | 'high' }
  technologyProfile: { erp?: string; crm?: string; cloud?: string; custom?: string[] }
  financialHealth: { score: number; revenue: number; growth: number; trend: 'up' | 'stable' | 'down' }
  governmentExposure: { level: 'none' | 'low' | 'medium' | 'high'; contracts: number }
  expansionPotential: { score: number; markets: string[] }
  digitalPresence: { score: number; website: 'none' | 'basic' | 'active'; social: 'none' | 'basic' | 'active' }
  hiringTrend: { trend: 'declining' | 'stable' | 'growing'; openings: number }
  procurementMaturity: { score: number; level: 'initial' | 'managed' | 'defined' | 'optimized' }
  relationshipStrength: { score: number; connections: number }
  buyingIntent: { score: number; confidence: number }
  riskLevel: { score: number; level: 'low' | 'medium' | 'high' }
  confidenceScore: number
  dataFreshness: { score: number; updatedAt: string }
  goldenRecordStatus: { status: 'clean' | 'needs_review' | 'conflict'; sources: number }
}

export interface AIRecommendation {
  action: string
  actionLabel: string
  reasoning: string
  confidence: number
  expectedRevenue: number
  expectedImpact: 'low' | 'medium' | 'high'
  estimatedTime: string
  alternatives: { action: string; actionLabel: string; confidence: number }[]
  risks: string[]
}

export interface DecisionMaker {
  id: string
  name: string
  role: string
  department: string
  influence: 'low' | 'medium' | 'high'
  connected: boolean
  email?: string
  phone?: string
  lastInteraction?: string
}

export interface RelationshipNode {
  id: string
  type: 'person' | 'company' | 'department'
  label: string
  strength: number
}

export interface RelationshipEdge {
  source: string
  target: string
  type: string
  label: string
  direction: 'inbound' | 'outbound' | 'bidirectional'
}

export interface TimelineEvent {
  id: string
  type: 'signal' | 'news' | 'government' | 'email' | 'meeting' | 'crm' | 'document' | 'license' | 'hiring' | 'funding' | 'ai'
  summary: string
  detail?: string
  date: string
  source: string
  confidence?: number
  aiHighlighted?: boolean
}

export interface SignalItem {
  id: string
  type: 'hiring' | 'expansion' | 'partnership' | 'contract' | 'regulation' | 'market' | 'financial' | 'news'
  title: string
  description: string
  source: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  timestamp: string
  aiConfidence: number
}

export interface GovernmentRecord {
  id: string
  type: 'cr' | 'municipality' | 'zakat' | 'misa' | 'tender' | 'license' | 'violation'
  title: string
  status: 'active' | 'expired' | 'pending' | 'violation'
  issueDate?: string
  expiryDate?: string
  confidence: number
  source: string
  freshness: string
}

export interface DocumentItem {
  id: string
  title: string
  type: 'contract' | 'pdf' | 'government' | 'report' | 'legal'
  date: string
  aiSummary?: string
  confidence: number
}

export interface BuyingJourney {
  currentStage: 'awareness' | 'interest' | 'evaluation' | 'decision' | 'expansion'
  progress: number
  timeInStage: string
  recommendedAction: string
  stageDescription: string
}

export interface GoldenRecordEntry {
  id: string
  entityName: string
  source: string
  confidence: number
  conflicts: string[]
  freshness: string
  status: 'matched' | 'potential_duplicate' | 'conflict'
}

export interface CompanyIntelligenceDTO {
  companyId: string
  generatedAt: string
  dna: CompanyDNA | null
  aiRecommendation: AIRecommendation | null
  decisionMakers: DecisionMaker[]
  relationships: { nodes: RelationshipNode[]; edges: RelationshipEdge[] }
  timeline: TimelineEvent[]
  signals: SignalItem[]
  government: GovernmentRecord[]
  documents: DocumentItem[]
  buyingJourney: BuyingJourney | null
  goldenRecord: GoldenRecordEntry[]
  firmographic: CompanyFirmographic | null
}
