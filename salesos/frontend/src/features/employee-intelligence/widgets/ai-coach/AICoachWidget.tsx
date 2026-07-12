'use client'

import { useCallback } from 'react'
import { createWorkspaceWidget } from '@salesos/workspace'
import { useWorkspaceContext } from '../../workspace/EmployeeWorkspace'
import { useDecision } from '../../../revenue-execution/_providers/DecisionProvider'
import type { AICoachAction } from '@/lib/api'
import { Lightbulb, AlertTriangle, CheckCircle, ArrowRight, Sparkles, Target, TrendingUp } from 'lucide-react'
import { cn } from '@salesos/ui'

const PRIORITY_CONFIG: Record<string, { label: string; color: string; bg: string; icon: React.ReactNode }> = {
  high: { label: 'عالي', color: 'text-danger-600', bg: 'bg-danger-50', icon: <AlertTriangle className="h-3.5 w-3.5" /> },
  medium: { label: 'متوسط', color: 'text-warning-600', bg: 'bg-warning-50', icon: <Lightbulb className="h-3.5 w-3.5" /> },
  low: { label: 'منخفض', color: 'text-success-600', bg: 'bg-success-50', icon: <CheckCircle className="h-3.5 w-3.5" /> },
}

const TYPE_ICONS: Record<string, React.ReactNode> = {
  pipeline_empty: <Target className="h-4 w-4" />,
  win_rate_low: <TrendingUp className="h-4 w-4" />,
  on_track: <CheckCircle className="h-4 w-4" />,
}

export function AICoachView({ actions }: { actions: AICoachAction[] }) {
  const decision = useDecision()

  const handleAction = useCallback(async (action: AICoachAction) => {
    try {
      await decision.evaluate({
        tenantId: '',
        actorId: '',
        entityType: 'opportunity',
        metadata: { coachAction: action.type, title: action.title },
      })
    } catch {
      // silently ignore decision platform errors
    }
  }, [decision])

  if (actions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <Sparkles className="h-8 w-8 text-[var(--text-muted)] opacity-30 mb-2" />
        <p className="text-sm text-[var(--text-muted)]">لا توجد إجراءات حالياً</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {actions.map((action, i) => {
        const priority = PRIORITY_CONFIG[action.priority] || PRIORITY_CONFIG.low
        return (
          <button
            key={i}
            onClick={() => handleAction(action)}
            className={cn(
              'w-full text-right rounded-xl border p-3 transition-all',
              'hover:border-[var(--muhide-orange)] hover:bg-[var(--muhide-orange)]/5',
              'border-[var(--border-default)] bg-[var(--bg-primary)]',
            )}
          >
            <div className="flex items-start gap-2">
              <span className={cn('flex items-center justify-center w-8 h-8 rounded-lg shrink-0', priority.bg, priority.color)}>
                {TYPE_ICONS[action.type] || <Lightbulb className="h-4 w-4" />}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <p className="text-sm font-medium text-[var(--text-primary)]">{action.title}</p>
                  <span className={cn('mr-auto text-[9px] px-1.5 py-0.5 rounded-full font-medium', priority.bg, priority.color)}>
                    {priority.label}
                  </span>
                </div>
                <p className="text-xs text-[var(--text-secondary)] mt-0.5">{action.description}</p>
                <div className="flex items-center gap-1 mt-1.5 text-[9px] text-[var(--muhide-orange)]">
                  <span>عرض التفاصيل</span>
                  <ArrowRight className="h-2.5 w-2.5" />
                </div>
              </div>
            </div>
          </button>
        )
      })}
    </div>
  )
}

export const AICoachWidget = createWorkspaceWidget(
  { id: 'aiCoach', minHeight: '320px' },
  useWorkspaceContext,
  (widgets) => widgets.aiCoach,
  {
    metadata: { title: 'المدرب الذكي', category: 'decisions', priority: 'high' },
    render: ({ data }) => <AICoachView actions={data} />,
  },
)
