export interface ForecastData {
  currentQuarter: { target: number; actual: number; projected: number; confidence: number }
  monthlyTrend: { month: string; actual: number; forecast: number }[]
  risks: { label: string; impact: number; probability: number }[]
}
