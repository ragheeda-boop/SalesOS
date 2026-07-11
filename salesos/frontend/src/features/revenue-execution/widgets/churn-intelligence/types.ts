export interface ChurnData {
  atRiskAccounts: { companyName: string; riskScore: number; revenue: number; reason: string; daysSinceActivity: number }[]
  totalAtRisk: number; totalRevenue: number; avgRiskScore: number
}
