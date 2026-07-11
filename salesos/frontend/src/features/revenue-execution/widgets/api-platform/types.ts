export interface APIData {
  endpoints: { method: string; path: string; description: string; calls: number; avgLatency: number }[]
  totalEndpoints: number; totalCalls: number; avgLatency: number; errorRate: number
}
