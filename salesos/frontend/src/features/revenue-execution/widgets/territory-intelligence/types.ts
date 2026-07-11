export interface TerritoryData {
  territories: { id: string; name: string; deals: number; value: number; quota: number; attainment: number }[]
  coverage: { region: string; covered: boolean; salesReps: number; opportunityValue: number }[]
  gaps: { region: string; potentialValue: number; reason: string }[]
}
