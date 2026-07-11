'use client'

import { useState, useMemo } from 'react'
import { cn } from '@salesos/ui'
import { Target, DollarSign, TrendingUp, Users, Activity, Search } from 'lucide-react'
import type { OpportunityListViewProps } from './types'
import { STAGE_LABEL, type OpportunityStage } from '@/application/revenue-execution/opportunity.dto'

const STAGES: OpportunityStage[] = ['identified', 'qualifying', 'developing', 'proposing', 'negotiating', 'closing']

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

export function OpportunityListView({ opportunities, onSelect }: OpportunityListViewProps) {
  const [filter, setFilter] = useState<OpportunityStage | 'all'>('all')
  const [searchText, setSearchText] = useState('')

  const filtered = useMemo(() => {
    let items = filter === 'all' ? opportunities : opportunities.filter((o) => o.stage === filter)
    if (searchText) {
      const lower = searchText.toLowerCase()
      items = items.filter((o) => o.companyName.toLowerCase().includes(lower) || o.title.toLowerCase().includes(lower))
    }
    return items.sort((a, b) => new Date(b.lastActivityAt ?? b.createdAt).getTime() - new Date(a.lastActivityAt ?? a.createdAt).getTime())
  }, [opportunities, filter, searchText])

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: opportunities.length }
    for (const s of STAGES) c[s] = opportunities.filter((o) => o.stage === s).length
    return c
  }, [opportunities])

  const totalValue = opportunities.reduce((s, o) => s + o.estimatedValue, 0)
  const activeCount = opportunities.filter((o) => !['won', 'lost'].includes(o.stage)).length

  return (
    <div role="region" aria-label="قائمة الفرص" className="space-y-3 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      {/* Metrics strip */}
      <div className="grid grid-cols-3 gap-2">
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[10px] text-[var(--text-muted)]">الفرص النشطة</p>
          <p className="text-lg font-bold text-[var(--text-primary)]">{activeCount}</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[10px] text-[var(--text-muted)]">إجمالي القيمة</p>
          <p className="text-lg font-bold text-[var(--text-primary)]">${totalValue >= 1_000_000 ? (totalValue / 1_000_000).toFixed(1) + 'M' : (totalValue / 1000).toFixed(0) + 'K'}</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[10px] text-[var(--text-muted)]">متوسط الثقة</p>
          <p className="text-lg font-bold text-[var(--text-primary)]">
            %{opportunities.length > 0 ? Math.round(opportunities.reduce((s, o) => s + o.confidence, 0) / opportunities.length * 100) : 0}
          </p>
        </div>
      </div>

      {/* Stage filters */}
      <div className="flex gap-1 overflow-x-auto pb-1">
        {[{ id: 'all' as const, label: 'الكل' }, ...STAGES.map((s) => ({ id: s, label: STAGE_LABEL[s] }))].map((stage) => (
          <button
            key={stage.id}
            onClick={() => setFilter(stage.id)}
            className={cn(
              'shrink-0 rounded-lg px-2 py-1 text-[10px] font-medium transition whitespace-nowrap',
              filter === stage.id ? 'bg-primary-500 text-white' : 'bg-[var(--bg-tertiary)] text-[var(--text-muted)] hover:bg-primary-50 dark:hover:bg-primary-900/20',
            )}
          >
            {stage.label} {counts[stage.id] > 0 && `(${counts[stage.id]})`}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="pointer-events-none absolute right-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--text-muted)]" />
        <input
          type="text"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          placeholder="ابحث في الفرص…"
          className="w-full rounded-lg border border-[var(--border-color)] bg-transparent px-2 py-1.5 pr-8 text-xs text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:border-primary-500 focus:outline-none dark:border-neutral-700"
        />
      </div>

      {/* List */}
      {opportunities.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <Target className="mb-2 h-8 w-8 text-[var(--text-muted)] opacity-30" />
          <p className="text-sm text-[var(--text-muted)]">لا توجد فرص بعد</p>
          <p className="text-xs text-[var(--text-muted)]">سيتم إنشاء الفرص من توصيات AI</p>
        </div>
      ) : filtered.length === 0 ? (
        <p className="py-4 text-center text-xs text-[var(--text-muted)]">لا توجد نتائج للفلتر المحدد</p>
      ) : (
        <div className="space-y-1">
          {filtered.map((opp) => (
            <div
              key={opp.id}
              onClick={() => onSelect?.(opp)}
              className={cn(
                'flex items-start gap-3 rounded-lg px-3 py-2.5 text-sm transition hover:bg-[var(--bg-tertiary)] cursor-pointer',
              )}
            >
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--bg-tertiary)] dark:bg-neutral-800">
                <Target className="h-4 w-4 text-[var(--text-muted)]" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="truncate font-medium text-[var(--text-primary)]">{opp.title}</span>
                  <span className={cn('mr-auto rounded px-1 py-0.5 text-[9px] font-medium', STAGE_STYLE[opp.stage] ?? STAGE_STYLE.identified)}>
                    {STAGE_LABEL[opp.stage]}
                  </span>
                </div>
                <div className="mt-0.5 flex items-center gap-1.5 text-[10px] text-[var(--text-muted)]">
                  <span className="truncate">{opp.companyName}</span>
                  <span>·</span>
                  <span className="flex items-center gap-0.5">
                    <DollarSign className="h-3 w-3" />
                    ${opp.estimatedValue >= 1_000_000 ? (opp.estimatedValue / 1_000_000).toFixed(1) + 'M' : (opp.estimatedValue / 1000).toFixed(0) + 'K'}
                  </span>
                  <span>·</span>
                  <span className={cn(RISK_S[opp.riskLevel])}>%{Math.round(opp.confidence * 100)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
