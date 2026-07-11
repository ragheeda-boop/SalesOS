export interface ExpansionData {
  opportunities: { companyName: string; product: string; value: number; confidence: number; reason: string }[]
  totalValue: number; avgConfidence: number
}
