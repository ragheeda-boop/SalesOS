export interface AnalyticsData {
  users: { total: number; active: number; new: number }
  usage: { totalSessions: number; avgSessionDuration: number; dailyActiveUsers: number }
  pipeline: { totalValue: number; weightedValue: number; dealCount: number; winRate: number }
  widgets: { mostUsed: string; usageCount: number; widgets: { id: string; name: string; count: number }[] }
  search: { totalQueries: number; avgResults: number; topQueries: string[] }
  nba: { shown: number; executed: number; acceptanceRate: number }
}
