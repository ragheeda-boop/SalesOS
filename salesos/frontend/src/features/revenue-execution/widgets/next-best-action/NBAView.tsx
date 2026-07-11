'use client'

import { cn } from '@salesos/ui'
import { Sparkles, TrendingUp, AlertTriangle, Clock, DollarSign, ArrowUpRight, Zap, Target } from 'lucide-react'
import type { NBAViewProps } from './types'

const PRIORITY_CFG = {
  critical: { label: 'حرج — تحرك فوري', color: 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-300 ring-1 ring-red-200 dark:ring-red-800', icon: <Zap className="h-4 w-4" /> },
  high: { label: 'عالي — هذا الأسبوع', color: 'bg-orange-50 text-orange-700 dark:bg-orange-900/20 dark:text-orange-300 ring-1 ring-orange-200 dark:ring-orange-800', icon: <TrendingUp className="h-4 w-4" /> },
  medium: { label: 'متوسط — هذا الشهر', color: 'bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-300 ring-1 ring-amber-200 dark:ring-amber-800', icon: <Target className="h-4 w-4" /> },
  low: { label: 'منخفض — مراقبة', color: 'bg-neutral-50 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400 ring-1 ring-neutral-200 dark:ring-neutral-700', icon: <Clock className="h-4 w-4" /> },
}

export function NBAView({ action, onExecute }: NBAViewProps) {
  if (!action) {
    return (
      <div className="flex flex-col items-center justify-center py-10 text-center">
        <Sparkles className="mb-3 h-10 w-10 text-[var(--text-muted)] opacity-30" />
        <p className="text-sm font-medium text-[var(--text-muted)]">جاري تحليل أفضل إجراء تالي</p>
        <p className="mt-1 text-xs text-[var(--text-muted)]">سيتم اقتراح الإجراء المناسب بناءً على ذكاء الشركة</p>
      </div>
    )
  }

  const priority = PRIORITY_CFG[action.priority]

  return (
    <div role="region" aria-label="أفضل إجراء تالي" className="space-y-3 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      {/* Priority Badge */}
      <div className={cn('flex items-center gap-2 rounded-lg px-3 py-2', priority.color)}>
        {priority.icon}
        <span className="text-xs font-semibold">{priority.label}</span>
        <span className="mr-auto text-[10px] opacity-70">ثقة %{Math.round(action.confidence * 100)}</span>
      </div>

      {/* Action Card */}
      <div className="rounded-lg border border-primary-200 bg-primary-50/50 p-3 dark:border-primary-800 dark:bg-primary-900/10">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary-600" />
          <span className="text-base font-bold text-primary-700 dark:text-primary-300">{action.actionLabel}</span>
        </div>
        <p className="mt-2 text-sm leading-relaxed text-primary-800 dark:text-primary-200">{action.reasoning}</p>

        {/* Metrics */}
        <div className="mt-3 grid grid-cols-3 gap-2">
          <div className="rounded-lg bg-white/60 p-2 dark:bg-neutral-800/60">
            <div className="flex items-center gap-1 text-[10px] text-[var(--text-muted)]">
              <DollarSign className="h-3 w-3" /> الإيرادات
            </div>
            <p className="text-sm font-bold text-[var(--text-primary)]">
              ${action.expectedRevenue >= 1_000_000 ? (action.expectedRevenue / 1_000_000).toFixed(1) + 'M' : (action.expectedRevenue / 1000).toFixed(0) + 'K'}
            </p>
          </div>
          <div className="rounded-lg bg-white/60 p-2 dark:bg-neutral-800/60">
            <div className="flex items-center gap-1 text-[10px] text-[var(--text-muted)]">
              <Clock className="h-3 w-3" /> المدة
            </div>
            <p className="text-sm font-bold text-[var(--text-primary)]">{action.estimatedTime}</p>
          </div>
          <div className="rounded-lg bg-white/60 p-2 dark:bg-neutral-800/60">
            <div className="flex items-center gap-1 text-[10px] text-[var(--text-muted)]">
              <TrendingUp className="h-3 w-3" /> الأثر
            </div>
            <p className="text-sm font-bold capitalize text-[var(--text-primary)]">{action.expectedImpact === 'high' ? 'كبير' : action.expectedImpact === 'medium' ? 'متوسط' : 'صغير'}</p>
          </div>
        </div>

        {/* Execute Button */}
        {action.createsOpportunity && onExecute && (
          <button
            onClick={() => onExecute(action)}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-300"
          >
            <ArrowUpRight className="h-4 w-4" />
            تنفيذ — إنشاء فرصة
          </button>
        )}
      </div>

      {/* Context */}
      <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
        <p className="text-[10px] font-medium text-[var(--text-muted)]">السياق</p>
        <p className="mt-0.5 text-xs text-[var(--text-primary)]">{action.contextSummary}</p>
        {action.triggerEvent && (
          <p className="mt-0.5 flex items-center gap-1 text-[10px] text-purple-500">
            <Zap className="h-3 w-3" /> آخر حدث: {action.triggerEvent}
          </p>
        )}
      </div>

      {/* Risks */}
      {action.risks.length > 0 && (
        <div>
          <p className="mb-1 text-[10px] font-medium text-red-500">المخاطر</p>
          {action.risks.map((r, i) => (
            <div key={i} className="flex items-start gap-1.5 text-[10px] text-[var(--text-muted)]">
              <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0 text-red-400" />
              <span>{r}</span>
            </div>
          ))}
        </div>
      )}

      {/* Alternatives */}
      {action.alternatives.length > 0 && (
        <div className="border-t border-[var(--border-color)] pt-2 dark:border-neutral-700">
          <p className="mb-1 text-[10px] font-medium text-[var(--text-muted)]">بدائل</p>
          {action.alternatives.map((alt, i) => (
            <div key={i} className="flex items-center justify-between py-0.5">
              <span className="text-xs text-[var(--text-muted)]">{alt.actionLabel}</span>
              <span className="text-[10px] text-[var(--text-muted)]">%{Math.round(alt.confidence * 100)}</span>
            </div>
          ))}
        </div>
      )}

      {/* Score Breakdown */}
      <div className="border-t border-[var(--border-color)] pt-1.5 text-[9px] text-[var(--text-muted)] dark:border-neutral-700">
        <div className="grid grid-cols-3 gap-x-2 gap-y-0.5">
          <span>النية: %{Math.round(action.scoreBreakdown.buyingIntent * 100)}</span>
          <span>العلاقات: %{Math.round(action.scoreBreakdown.relationshipStrength * 100)}</span>
          <span>الإشارات: %{Math.round(action.scoreBreakdown.signalRecency * 100)}</span>
          <span>AI: %{Math.round(action.scoreBreakdown.aiConfidence * 100)}</span>
          <span>القرار: %{Math.round(action.scoreBreakdown.decisionMakerAccess * 100)}</span>
          <span>الإيرادات: %{Math.round(action.scoreBreakdown.revenuePotential * 100)}</span>
        </div>
      </div>
    </div>
  )
}
