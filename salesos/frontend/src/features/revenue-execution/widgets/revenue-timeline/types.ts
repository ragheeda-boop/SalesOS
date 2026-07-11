export interface RevenueTimelineEvent {
  id: string; type: 'signal' | 'meeting' | 'email' | 'task' | 'deal' | 'note'; summary: string; date: string; entityName?: string; value?: number
}
export interface RevenueTimelineViewProps { events: RevenueTimelineEvent[] }
