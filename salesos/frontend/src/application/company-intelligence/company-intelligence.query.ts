export interface CompanyIntelligenceQuery {
  companyId: string
  period?: '7d' | '30d' | '90d'
  includeSignals?: boolean
  includeFinancial?: boolean
  includeAI?: boolean
}
