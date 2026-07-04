import { useState } from 'react'
import { cn } from '@salesos/ui'
import { Clock, Building2, Users, DollarSign, FileText, Activity, RefreshCw, UserPlus, Edit3, Plus, AlertCircle } from 'lucide-react'

export type ActivityType = 'created' | 'updated' | 'deleted' | 'merged' | 'imported' | 'enriched' | 'ai-analyzed' | 'note-added' | 'meeting-logged' | 'email-received'

export type ActivityEntity = 'company' | 'deal' | 'contact' | 'opportunity' | 'document' | 'workspace'

export interface ActivityEvent {
  id: string
  type: ActivityType
  entityType: ActivityEntity
  entityId: string
  entityName: string
  summary: string
  detail?: string
  user: { name: string; avatar?: string }
  timestamp: number
  aiGenerated?: boolean
  confidence?: number
}

const activityIcons: Record<ActivityEntity, React.ReactNode> = {
  company: <Building2 className="h-4 w-4" />,
  deal: <DollarSign className="h-4 w-4" />,
  contact: <Users className="h-4 w-4" />,
  opportunity: <DollarSign className="h-4 w-4" />,
  document: <FileText className="h-4 w-4" />,
  workspace: <Activity className="h-4 w-4" />,
}

const typeIcons: Record<ActivityType, React.ReactNode> = {
  created: <Plus className="h-3.5 w-3.5 text-green-600" />,
  updated: <Edit3 className="h-3.5 w-3.5 text-blue-600" />,
  deleted: <AlertCircle className="h-3.5 w-3.5 text-red-600" />,
  merged: <RefreshCw className="h-3.5 w-3.5 text-purple-600" />,
  imported: <UserPlus className="h-3.5 w-3.5 text-blue-600" />,
  enriched: <RefreshCw className="h-3.5 w-3.5 text-emerald-600" />,
  'ai-analyzed': <Activity className="h-3.5 w-3.5 text-purple-600" />,
  'note-added': <FileText className="h-3.5 w-3.5 text-gray-600" />,
  'meeting-logged': <Clock className="h-3.5 w-3.5 text-amber-600" />,
  'email-received': <Activity className="h-3.5 w-3.5 text-blue-600" />,
}

interface GlobalActivityFeedProps {
  events: ActivityEvent[]
  className?: string
  global?: boolean
}

export function GlobalActivityFeed({ events, className, global }: GlobalActivityFeedProps) {
  const [filter, setFilter] = useState<ActivityEntity | 'all'>('all')
  const [showAI, setShowAI] = useState(true)

  const filtered = events.filter((e) => {
    if (filter !== 'all' && e.entityType !== filter) return false
    if (!showAI && e.aiGenerated) return false
    return true
  })

  const entityTypes = Array.from(new Set(events.map((e) => e.entityType)))

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          {global ? 'النشاطات العالمية' : 'النشاطات الأخيرة'}
        </h2>
        <label className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
          <input type="checkbox" checked={showAI} onChange={() => setShowAI(!showAI)} className="rounded" />
          AI
        </label>
      </div>
      <div className="flex flex-wrap gap-1">
        <button
          onClick={() => setFilter('all')}
          className={cn('rounded-lg px-2.5 py-1 text-xs transition', filter === 'all' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' : 'text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800')}
        >
          الكل
        </button>
        {entityTypes.map((type) => (
          <button
            key={type}
            onClick={() => setFilter(type)}
            className={cn('rounded-lg px-2.5 py-1 text-xs transition', filter === type ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' : 'text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800')}
          >
            {type === 'company' ? 'شركات' : type === 'deal' ? 'صفقات' : type === 'contact' ? 'جهات اتصال' : type}
          </button>
        ))}
      </div>
      <div className="space-y-1">
        {filtered.length === 0 && (
          <p className="py-8 text-center text-sm text-gray-500 dark:text-gray-400">لا توجد نشاطات</p>
        )}
        {filtered.map((event) => (
          <div
            key={event.id}
            className="flex items-start gap-3 rounded-lg px-3 py-2.5 transition hover:bg-gray-50 dark:hover:bg-gray-900"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-800">
              {activityIcons[event.entityType]}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5 text-sm">
                <span className="inline-flex items-center gap-1 rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500 dark:bg-gray-800 dark:text-gray-400">
                  {typeIcons[event.type]}
                  {event.type === 'created' ? 'جديد' : event.type === 'updated' ? 'تحديث' : event.type === 'ai-analyzed' ? 'AI' : event.type}
                </span>
                <span className="truncate font-medium text-gray-900 dark:text-gray-100">
                  {event.summary}
                </span>
              </div>
              <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                {event.entityName} · منذ {Math.floor((Date.now() - event.timestamp) / 60000)} دقيقة
              </p>
            </div>
            {event.aiGenerated && (
              <SparklesIcon className="h-3.5 w-3.5 text-purple-500" />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function SparklesIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 3l1.5 6.5L20 11l-6.5 1.5L12 19l-1.5-6.5L4 11l6.5-1.5z" />
    </svg>
  )
}
