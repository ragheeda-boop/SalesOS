import { useState } from 'react'
import { cn } from '@salesos/ui'
import { CheckCircle2, AlertCircle, Bell, Bot, MessageSquare, ThumbsUp, Clock, ArrowRight, Sparkles, ListTodo, UserPlus } from 'lucide-react'
import { EMPTY_STATES } from '@salesos/design-language'

export type InboxItemType = 'task' | 'approval' | 'recommendation' | 'ai-insight' | 'mention' | 'notification' | 'alert'

export interface InboxItem {
  id: string
  type: InboxItemType
  title: string
  description?: string
  entityType?: string
  entityId?: string
  entityName?: string
  priority: 'low' | 'medium' | 'high' | 'critical'
  timestamp: number
  read: boolean
  actionable: boolean
  actionLabel?: string
  actionHandler?: string
  source?: string
}

const typeConfig: Record<InboxItemType, { icon: React.ReactNode; label: string; color: string }> = {
  task: { icon: <ListTodo className="h-4 w-4" />, label: 'مهمة', color: 'text-blue-600' },
  approval: { icon: <ThumbsUp className="h-4 w-4" />, label: 'اعتماد', color: 'text-amber-600' },
  recommendation: { icon: <Sparkles className="h-4 w-4" />, label: 'توصية', color: 'text-purple-600' },
  'ai-insight': { icon: <Bot className="h-4 w-4" />, label: 'AI', color: 'text-purple-600' },
  mention: { icon: <MessageSquare className="h-4 w-4" />, label: 'ذكر', color: 'text-green-600' },
  notification: { icon: <Bell className="h-4 w-4" />, label: 'إشعار', color: 'text-blue-600' },
  alert: { icon: <AlertCircle className="h-4 w-4" />, label: 'تنبيه', color: 'text-red-600' },
}

const priorityConfig = {
  low: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  medium: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
  high: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300',
  critical: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
}

interface UniversalInboxProps {
  items: InboxItem[]
  className?: string
  onItemClick?: (item: InboxItem) => void
  onAction?: (item: InboxItem) => void
}

export function UniversalInbox({ items, className, onItemClick, onAction }: UniversalInboxProps) {
  const [filter, setFilter] = useState<InboxItemType | 'all'>('all')
  const [showUnread, setShowUnread] = useState(false)

  const filtered = items.filter((item) => {
    if (filter !== 'all' && item.type !== filter) return false
    if (showUnread && item.read) return false
    return true
  })

  const unreadCount = items.filter((i) => !i.read).length
  const typeCounts = items.reduce((acc, item) => {
    acc[item.type] = (acc[item.type] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return (
    <div className={cn('flex h-full flex-col', className)}>
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">صندوق الوارد</h2>
          {unreadCount > 0 && (
            <span className="rounded-full bg-blue-600 px-2 py-0.5 text-[10px] font-medium text-white">
              {unreadCount}
            </span>
          )}
        </div>
        <button
          onClick={() => setShowUnread(!showUnread)}
          className={cn('rounded-lg px-2.5 py-1 text-xs transition', showUnread ? 'bg-blue-100 text-blue-700' : 'text-gray-500 hover:bg-gray-100')}
        >
          غير مقروء
        </button>
      </div>
      <div className="flex gap-1 overflow-x-auto border-b border-gray-200 px-4 py-2 dark:border-gray-700">
        <button
          onClick={() => setFilter('all')}
          className={cn('shrink-0 rounded-lg px-2.5 py-1 text-xs transition', filter === 'all' ? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100' : 'text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800')}
        >
          الكل ({items.length})
        </button>
        {(Object.entries(typeConfig) as [InboxItemType, typeof typeConfig[InboxItemType]][]).map(([type, config]) => (
          <button
            key={type}
            onClick={() => setFilter(type)}
            className={cn('flex shrink-0 items-center gap-1 rounded-lg px-2.5 py-1 text-xs transition', filter === type ? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100' : 'text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800')}
          >
            {config.icon}
            {config.label}
            {typeCounts[type] && <span className="text-[10px] opacity-60">({typeCounts[type]})</span>}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-gray-500 dark:text-gray-400">
            <Bell className="mb-3 h-8 w-8 opacity-50" />
            <p className="text-sm">{EMPTY_STATES.noNotifications.title}</p>
            <p className="text-xs">{EMPTY_STATES.noNotifications.description}</p>
          </div>
        )}
        {filtered.map((item) => {
          const config = typeConfig[item.type]
          return (
            <div
              key={item.id}
              onClick={() => onItemClick?.(item)}
              className={cn(
                'flex items-start gap-3 border-b border-gray-100 px-4 py-3 transition hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-900',
                !item.read && 'bg-blue-50/30 dark:bg-blue-900/10'
              )}
            >
              <div className={cn('mt-0.5 shrink-0', config.color)}>{config.icon}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className={cn('rounded px-1.5 py-0.5 text-[10px] font-medium', priorityConfig[item.priority])}>
                    {item.priority === 'critical' ? 'حرج' : item.priority === 'high' ? 'عالي' : item.priority === 'medium' ? 'متوسط' : 'منخفض'}
                  </span>
                  <span className="text-[10px] text-gray-400">{config.label}</span>
                </div>
                <p className={cn('mt-0.5 text-sm', item.read ? 'text-gray-600 dark:text-gray-400' : 'font-medium text-gray-900 dark:text-gray-100')}>
                  {item.title}
                </p>
                {item.description && (
                  <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400 line-clamp-2">{item.description}</p>
                )}
                <div className="mt-1 flex items-center gap-2 text-[10px] text-gray-400">
                  <span>منذ {Math.floor((Date.now() - item.timestamp) / 60000)} دقيقة</span>
                  {item.entityName && <span>· {item.entityName}</span>}
                </div>
              </div>
              {item.actionable && (
                <button
                  onClick={(e) => { e.stopPropagation(); onAction?.(item) }}
                  className="shrink-0 rounded-lg px-2.5 py-1 text-xs text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/50"
                >
                  {item.actionLabel || 'فتح'}
                </button>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
