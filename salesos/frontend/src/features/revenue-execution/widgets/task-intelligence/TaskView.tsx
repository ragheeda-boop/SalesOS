'use client'

import { useState } from 'react'
import { cn } from '@salesos/ui'
import { CheckCircle2, Circle, AlertTriangle, Clock, Target, Sparkles } from 'lucide-react'
import type { TaskViewProps } from './types'

const PRIORITY_CFG = { critical: { color: 'text-red-500', label: 'حرج' }, high: { color: 'text-orange-500', label: 'عالي' }, medium: { color: 'text-amber-500', label: 'متوسط' }, low: { color: 'text-neutral-400', label: 'منخفض' } }
const SOURCE_ICON = { nba: <Sparkles className="h-3 w-3" />, meeting: <Clock className="h-3 w-3" />, email: <Target className="h-3 w-3" />, manual: <Circle className="h-3 w-3" />, signal: <AlertTriangle className="h-3 w-3" /> }

export function TaskView({ tasks, onComplete }: TaskViewProps) {
  const [filter, setFilter] = useState<'all' | 'active' | 'completed'>('active')
  const filtered = tasks.filter((t) => filter === 'all' ? true : filter === 'completed' ? t.completed : !t.completed)
  const activeCount = tasks.filter((t) => !t.completed).length

  if (tasks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <CheckCircle2 className="mb-2 h-8 w-8 text-[var(--text-muted)] opacity-30" />
        <p className="text-sm text-[var(--text-muted)]">لا توجد مهام</p>
      </div>
    )
  }

  return (
    <div role="region" aria-label="المهام" className="space-y-2 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      <div className="flex items-center justify-between">
        <div className="flex gap-1">
          {(['active', 'all', 'completed'] as const).map((f) => (
            <button key={f} onClick={() => setFilter(f)} className={cn('rounded-lg px-2 py-0.5 text-[9px] font-medium transition', filter === f ? 'bg-primary-500 text-white' : 'bg-[var(--bg-tertiary)] text-[var(--text-muted)]')}>
              {f === 'active' ? 'نشطة' : f === 'all' ? 'الكل' : 'مكتملة'}
            </button>
          ))}
        </div>
        <span className="text-[9px] text-[var(--text-muted)]">{activeCount} نشطة</span>
      </div>
      <div className="space-y-0.5">
        {filtered.map((task) => {
          const priority = PRIORITY_CFG[task.priority]
          return (
            <div key={task.id} className={cn('flex items-start gap-2.5 rounded-lg px-3 py-2 transition', task.completed ? 'opacity-50' : 'hover:bg-[var(--bg-tertiary)]')}>
              <button onClick={() => onComplete?.(task.id)} className="mt-0.5 shrink-0">
                {task.completed ? <CheckCircle2 className="h-4 w-4 text-green-500" /> : <Circle className="h-4 w-4 text-[var(--text-muted)] hover:text-primary-500" />}
              </button>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className={cn('truncate text-xs font-medium', task.completed ? 'line-through text-[var(--text-muted)]' : 'text-[var(--text-primary)]')}>{task.title}</span>
                  <span className={cn('mr-auto text-[9px] font-medium', priority.color)}>{priority.label}</span>
                </div>
                <div className="mt-0.5 flex items-center gap-1.5 text-[9px] text-[var(--text-muted)]">
                  {task.companyName && <span>{task.companyName} · </span>}
                  {SOURCE_ICON[task.source]}
                  <span>{task.source === 'nba' ? 'AI' : task.source}</span>
                  {task.dueDate && <span>· {new Date(task.dueDate).toLocaleDateString('ar-SA')}</span>}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
