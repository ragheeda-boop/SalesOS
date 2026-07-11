'use client'

import { cn } from '@salesos/ui'
import { Target, DollarSign, TrendingUp, Users, Activity, Shield, Calendar } from 'lucide-react'
import type { OpportunityDetailViewProps } from './types'
import { STAGE_LABEL, STAGES, type OpportunityStage } from '@/application/revenue-execution/opportunity.dto'

const STAGE_STYLE: Record<string, string> = {
  identified: 'bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300',
  qualifying: 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300',
  developing: 'bg-purple-50 text-purple-700 dark:bg-purple-900/20 dark:text-purple-300',
  proposing: 'bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-300',
  negotiating: 'bg-orange-50 text-orange-700 dark:bg-orange-900/20 dark:text-orange-300',
  closing: 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-300',
  won: 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-300',
  lost: 'bg-neutral-100 text-neutral-500 dark:bg-neutral-800 dark:text-neutral-400',
}

const RISK_S = { low: 'text-green-600', medium: 'text-amber-600', high: 'text-red-600' }
const STAGE_IDS: OpportunityStage[] = ['identified', 'qualifying', 'developing', 'proposing', 'negotiating', 'closing']

function Gauge({ label, value, color }: { label: string; value: number; color?: string }) {
  const pct = Math.min(100, value * 100)
  const bar = color ?? (pct >= 70 ? 'bg-green-500' : pct >= 40 ? 'bg-amber-500' : 'bg-red-500')
  return (
    <div>
      <div className="flex items-center justify-between text-[10px] text-[var(--text-muted)]">
        <span>{label}</span>
        <span className="font-semibold text-[var(--text-primary)]">%{Math.round(pct)}</span>
      </div>
      <div className="mt-0.5 h-1.5 w-full overflow-hidden rounded-full bg-[var(--bg-tertiary)] dark:bg-neutral-700">
        <div className={cn('h-full rounded-full transition-all', bar)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export function OpportunityDetailView({ opportunity, onStageChange }: OpportunityDetailViewProps) {
  if (!opportunity) {
    return (
      <div className="flex flex-col items-center justify-center py-10 text-center">
        <Target className="mb-3 h-10 w-10 text-[var(--text-muted)] opacity-30" />
        <p className="text-sm text-[var(--text-muted)]">اختر فرصة لعرض التفاصيل</p>
      </div>
    )
  }

  const opp = opportunity
  const currentIdx = STAGE_IDS.indexOf(opp.stage)

  return (
    <div role="region" aria-label={`تفاصيل الفرصة: ${opp.title}`} className="space-y-3 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <Target className="h-5 w-5 text-primary-600" />
          <h3 className="text-sm font-bold text-[var(--text-primary)]">{opp.title}</h3>
          <span className={cn('mr-auto rounded px-1.5 py-0.5 text-[10px] font-medium', STAGE_STYLE[opp.stage])}>{STAGE_LABEL[opp.stage]}</span>
        </div>
        <p className="mt-0.5 text-xs text-[var(--text-muted)]">{opp.companyName}</p>
      </div>

      {/* Value + Confidence */}
      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <div className="flex items-center gap-1 text-[10px] text-[var(--text-muted)]">
            <DollarSign className="h-3 w-3" /> القيمة المقدرة
          </div>
          <p className="text-lg font-bold text-[var(--text-primary)]">
            ${opp.estimatedValue >= 1_000_000 ? (opp.estimatedValue / 1_000_000).toFixed(1) + 'M' : (opp.estimatedValue / 1000).toFixed(0) + 'K'}
          </p>
        </div>
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <div className="flex items-center gap-1 text-[10px] text-[var(--text-muted)]">
            <TrendingUp className="h-3 w-3" /> احتمالية الفوز
          </div>
          <p className="text-lg font-bold text-green-600 dark:text-green-400">%{Math.round(opp.winProbability * 100)}</p>
        </div>
      </div>

      {/* Stage progress */}
      <div>
        <p className="mb-1 text-[10px] font-medium text-[var(--text-muted)]">مراحل الفرصة</p>
        <div className="flex items-center justify-between">
          {STAGE_IDS.map((stage, i) => {
            const isActive = i === currentIdx
            const isPast = i < currentIdx
            return (
              <button
                key={stage}
                onClick={() => onStageChange?.(opp.id, stage)}
                disabled={isPast}
                className={cn(
                  'flex h-6 w-6 items-center justify-center rounded-full text-[9px] font-bold transition',
                  isActive ? 'bg-primary-500 text-white ring-2 ring-primary-300' :
                  isPast ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-300' :
                  'bg-[var(--bg-tertiary)] text-[var(--text-muted)] dark:bg-neutral-800 hover:bg-primary-50',
                )}
                title={STAGE_LABEL[stage]}
              >
                {i + 1}
              </button>
            )
          })}
        </div>
      </div>

      {/* Intelligence */}
      <div className="space-y-1.5">
        <p className="text-[10px] font-medium text-[var(--text-muted)]">الذكاء</p>
        <Gauge label="نية الشراء" value={opp.buyingIntent} />
        <Gauge label="قوة العلاقة" value={opp.relationshipStrength} />
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-[var(--text-muted)]">مستوى المخاطرة</span>
          <span className={cn('text-xs font-medium', RISK_S[opp.riskLevel])}>
            {opp.riskLevel === 'low' ? 'منخفض' : opp.riskLevel === 'medium' ? 'متوسط' : 'عالي'}
          </span>
        </div>
      </div>

      {/* Dates */}
      <div className="space-y-0.5 text-[10px] text-[var(--text-muted)]">
        <div className="flex items-center gap-1">
          <Calendar className="h-3 w-3" /> تم الإنشاء: {new Date(opp.createdAt).toLocaleDateString('ar-SA')}
        </div>
        {opp.lastActivityAt && (
          <div className="flex items-center gap-1">
            <Activity className="h-3 w-3" /> آخر نشاط: {new Date(opp.lastActivityAt).toLocaleDateString('ar-SA')}
          </div>
        )}
      </div>

      {/* Notes */}
      {opp.notes.length > 0 && (
        <div>
          <p className="mb-1 text-[10px] font-medium text-[var(--text-muted)]">الملاحظات ({opp.notes.length})</p>
          <div className="space-y-1">
            {opp.notes.map((note) => (
              <div key={note.id} className="rounded-lg bg-[var(--bg-tertiary)] px-2 py-1.5 dark:bg-neutral-800">
                <p className="text-[10px] text-[var(--text-primary)]">{note.text}</p>
                <p className="mt-0.5 text-[9px] text-[var(--text-muted)]">{note.author} · {new Date(note.createdAt).toLocaleDateString('ar-SA')}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
