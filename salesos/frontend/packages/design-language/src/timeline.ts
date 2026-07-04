export type TimelineEventType =
  | 'company.created'
  | 'company.updated'
  | 'company.merged'
  | 'company.enriched'
  | 'deal.created'
  | 'deal.stage_changed'
  | 'deal.won'
  | 'deal.lost'
  | 'contact.added'
  | 'contact.updated'
  | 'activity.logged'
  | 'meeting.scheduled'
  | 'meeting.completed'
  | 'email.sent'
  | 'email.opened'
  | 'call.made'
  | 'task.completed'
  | 'task.assigned'
  | 'document.uploaded'
  | 'signal.detected'
  | 'ai.decision'
  | 'ai.recommendation'
  | 'ai.analysis'
  | 'integration.synced'
  | 'user.action'
  | 'system.alert'
  | 'permission.changed'

export interface TimelineEvent {
  id: string
  type: TimelineEventType
  title: string
  description?: string
  timestamp: number
  actor: {
    id: string
    name: string
    type: 'user' | 'ai' | 'system' | 'integration'
  }
  entity?: {
    type: string
    id: string
    name: string
  }
  metadata?: Record<string, unknown>
  importance: 'low' | 'normal' | 'high' | 'critical'
  actionable?: boolean
}

export const TIMELINE_GROUPS = {
  today: 'اليوم',
  yesterday: 'أمس',
  thisWeek: 'هذا الأسبوع',
  lastWeek: 'الأسبوع الماضي',
  thisMonth: 'هذا الشهر',
  older: 'أقدم',
} as const

export const GLOBAL_TIMELINE_FILTERS = {
  all: 'الكل',
  signals: 'الإشارات',
  activities: 'النشاطات',
  deals: 'الصفقات',
  ai: 'AI',
  system: 'النظام',
  alerts: 'التنبيهات',
} as const
