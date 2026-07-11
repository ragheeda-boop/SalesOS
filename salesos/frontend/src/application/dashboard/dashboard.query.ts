export interface DashboardQuery {
  period?: 'today' | 'week' | 'month' | 'quarter'
  fields?: string[]
}
