import type { AIBriefData } from '@/application/dashboard/dashboard.dto'

export interface AIBriefViewProps {
  summary: string
  highlights: string[]
  generatedAt: string
  onRefresh?: () => void
}
