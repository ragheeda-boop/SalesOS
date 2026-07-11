'use client'

import { cn } from '@salesos/ui'
import type { CompanyDNAViewProps } from './types'

const TREND = { up: '↑', stable: '→', down: '↓' }
const TREND_C = { up: 'text-green-600 dark:text-green-400', stable: 'text-amber-600 dark:text-amber-400', down: 'text-red-600 dark:text-red-400' }

function Gauge({ label, value, max = 100, color }: { label: string; value: number; max?: number; color?: string }) {
  const pct = Math.min(100, (value / max) * 100)
  const bar = color ?? (pct >= 70 ? 'bg-green-500' : pct >= 40 ? 'bg-amber-500' : 'bg-red-500')
  return (
    <div>
      <div className="flex items-center justify-between text-[10px] text-[var(--text-muted)]">
        <span className="truncate">{label}</span>
        <span className="font-semibold text-[var(--text-primary)]">{value}{max === 100 ? '%' : ''}</span>
      </div>
      <div className="mt-0.5 h-1.5 w-full overflow-hidden rounded-full bg-[var(--bg-tertiary)] dark:bg-neutral-700">
        <div className={cn('h-full rounded-full transition-all', bar)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function Badge({ label, variant }: { label: string; variant: 'info' | 'success' | 'warning' | 'danger' | 'neutral' }) {
  const v = {
    info: 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    success: 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300',
    warning: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
    danger: 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300',
    neutral: 'bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400',
  }
  return <span className={cn('rounded-full px-1.5 py-0.5 text-[9px] font-medium', v[variant])}>{label}</span>
}

function MetricBox({ label, value, trend }: { label: string; value: string; trend?: 'up' | 'stable' | 'down' }) {
  return (
    <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
      <p className="text-[9px] text-[var(--text-muted)]">{label}</p>
      <p className="mt-0.5 text-xs font-bold text-[var(--text-primary)]">
        {value}
        {trend && <span className={cn('mr-0.5 text-[10px]', TREND_C[trend])}>{TREND[trend]}</span>}
      </p>
    </div>
  )
}

export function CompanyDNAView({ dna }: CompanyDNAViewProps) {
  if (!dna) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <span className="text-2xl" aria-hidden="true">🧬</span>
        <p className="mt-2 text-sm text-[var(--text-muted)]">جاري تحليل الشركة</p>
      </div>
    )
  }

  return (
    <div role="region" aria-label="الحمض النووي للشركة" className="space-y-2 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      {/* Row 1: Identity */}
      <div className="flex items-center gap-2">
        <Badge label={dna.industry} variant="info" />
        <Badge label={dna.businessModel} variant="neutral" />
        <Badge label={dna.size.label} variant={dna.size.label === 'enterprise' ? 'success' : 'warning'} />
        {dna.growthPattern === 'accelerating' && <Badge label="متسارع" variant="success" />}
      </div>

      {/* Row 2: Key Metrics */}
      <div className="grid grid-cols-3 gap-1.5">
        <MetricBox label="الموظفون" value={dna.size.employees.toLocaleString()} />
        <MetricBox label="الإيرادات" value={`$${dna.financialHealth.revenue >= 1e9 ? (dna.financialHealth.revenue / 1e9).toFixed(1) + 'B' : (dna.financialHealth.revenue / 1e6).toFixed(0) + 'M'}`} />
        <MetricBox label="النمو" value={`%${dna.financialHealth.growth}`} trend={dna.financialHealth.trend} />
      </div>

      {/* Row 3: Gauges */}
      <div className="space-y-1.5">
        <Gauge label="الصحة المالية" value={dna.financialHealth.score} />
        <Gauge label="نية الشراء" value={dna.buyingIntent.score} />
        <Gauge label="العلاقات" value={dna.relationshipStrength.score} />
        <Gauge label="النضج الشرائي" value={dna.procurementMaturity.score} />
        <Gauge label="الوجود الرقمي" value={dna.digitalPresence.score} />
        <Gauge label="التوسع المحتمل" value={dna.expansionPotential.score} />
        <Gauge label="جودة البيانات" value={dna.dataFreshness.score} />
      </div>

      {/* Row 4: Bottom bar */}
      <div className="flex items-center justify-between border-t border-[var(--border-color)] pt-1.5 text-[9px] text-[var(--text-muted)] dark:border-neutral-700">
        <span>ثقة: %{Math.round(dna.confidenceScore * 100)}</span>
        <span>مخاطرة: {dna.riskLevel.level}</span>
        <span>مصادر: {dna.goldenRecordStatus.sources}</span>
      </div>
    </div>
  )
}
