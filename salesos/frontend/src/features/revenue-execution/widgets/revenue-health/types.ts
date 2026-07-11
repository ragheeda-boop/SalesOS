export interface RevenueHealthData {
  totalPortfolio: number; activeAccounts: number; atRisk: number; growthAccounts: number
  healthDistribution: { label: string; count: number; value: number; color: string }[]
}
