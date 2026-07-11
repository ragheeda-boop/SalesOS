'use client'

import { Card, CardContent, cn } from '@salesos/ui'
import { Target, AlertTriangle, TrendingUp, Building2, Activity } from 'lucide-react'
import { MissionMetric } from './MissionMetric'
import { MissionAction } from './MissionAction'
import { MissionProgress } from './MissionProgress'
import type { MissionCenterViewProps } from './types'

function deriveActions(props: MissionCenterViewProps) {
  const actions: { id: string; title: string; priority: 'high' | 'medium' | 'low'; companyName?: string }[] = []

  if (props.signalsToday > 0) {
    actions.push({
      id: 'review-signals',
      title: `مراجعة ${props.signalsToday} إشارة شرائية`,
      priority: 'high',
    })
  }

  if (props.decisionsPending > 0) {
    actions.push({
      id: 'pending-decisions',
      title: `${props.decisionsPending} قرارات معلقة تحتاج اتخاذ`,
      priority: 'high',
    })
  }

  if (props.activeDeals > 0) {
    actions.push({
      id: 'active-deals',
      title: `متابعة ${props.activeDeals} صفقة نشطة`,
      priority: 'medium',
    })
  }

  if (props.companiesTracked > 10) {
    actions.push({
      id: 'new-companies',
      title: `مراجعة ${props.companiesTracked} شركة تحت المراقبة`,
      priority: 'low',
    })
  }

  return actions.slice(0, 5)
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center" role="status">
      <Building2 className="h-8 w-8 text-[var(--text-muted)] mb-2" aria-hidden="true" />
      <p className="text-sm font-medium text-[var(--text-primary)]">لا توجد بيانات بعد</p>
      <p className="text-xs text-[var(--text-muted)] mt-1">قم بإضافة شركات لبدء التتبع</p>
    </div>
  )
}

function SummaryBanner({ metrics }: { metrics: { label: string; value: number }[] }) {
  const activeMetrics = metrics.filter((m) => m.value > 0)
  return (
    <div className="text-xs text-[var(--text-muted)]" aria-live="polite" aria-atomic="true">
      {activeMetrics.length > 0
        ? `${activeMetrics.map((m) => `${m.value} ${m.label}`).join('، ')}`
        : 'لا توجد مؤشرات نشطة حالياً'}
    </div>
  )
}

export function MissionCenterView(props: MissionCenterViewProps) {
  const isAllZero = props.companiesTracked === 0 && props.activeDeals === 0 && props.pipelineValue === 0 && props.signalsToday === 0 && props.decisionsPending === 0
  const actions = !isAllZero ? deriveActions(props) : []
  const pipelineCompletion = props.pipelineValue > 0
    ? Math.min(Math.round((props.activeDeals * 100000) / props.pipelineValue * 100), 100)
    : 0

  if (isAllZero) {
    return (
      <div className="flex flex-col gap-4" role="region" aria-label="Mission Center Dashboard">
        <SummaryBanner metrics={[
          { label: 'شركات', value: props.companiesTracked },
          { label: 'صفقات', value: props.activeDeals },
          { label: 'إشارات', value: props.signalsToday },
        ]} />
        <EmptyState />
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4" role="region" aria-label="Mission Center Dashboard">
      <SummaryBanner metrics={[
        { label: 'شركات', value: props.companiesTracked },
        { label: 'صفقات', value: props.activeDeals },
        { label: 'إشارات', value: props.signalsToday },
      ]} />

      {/* Metrics Grid */}
      <div
        className="grid gap-3"
        style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))' }}
        role="list"
        aria-label="Key metrics"
      >
        <div role="listitem">
          <MissionMetric
            label="شركات تحت المراقبة"
            value={props.companiesTracked}
            valueClassName="text-info-600 dark:text-info-400"
            ariaLabel={`${props.companiesTracked} شركات تحت المراقبة`}
          />
        </div>
        <div role="listitem">
          <MissionMetric
            label="صفقات نشطة"
            value={props.activeDeals}
            valueClassName="text-[var(--muhide-orange)]"
            ariaLabel={`${props.activeDeals} صفقات نشطة`}
          />
        </div>
        <div role="listitem">
          <MissionMetric
            label="قيمة الأنابيب"
            value={`${(props.pipelineValue / 1000000).toFixed(1)}M`}
            valueClassName="text-success-600 dark:text-success-400"
            ariaLabel={`قيمة الأنابيب ${props.pipelineValue.toLocaleString()} ريال`}
          />
        </div>
        <div role="listitem">
          <MissionMetric
            label="إشارات اليوم"
            value={props.signalsToday}
            valueClassName="text-info-600 dark:text-info-400"
            icon="📡"
            ariaLabel={`${props.signalsToday} إشارة جديدة اليوم`}
          />
        </div>
        <div role="listitem">
          <MissionMetric
            label="قرارات معلقة"
            value={props.decisionsPending}
            valueClassName="text-danger-600 dark:text-danger-400"
            icon="⚡"
            ariaLabel={`${props.decisionsPending} قرارات معلقة`}
          />
        </div>
      </div>

      {/* Priority Actions */}
      {actions.length > 0 && (
        <Card className="border-0 shadow-none bg-[var(--bg-secondary)]">
          <CardContent className="p-3">
            <div className="flex items-center gap-1.5 mb-2">
              <AlertTriangle className="h-3.5 w-3.5 text-warning-500" aria-hidden="true" />
              <span className="text-xs font-semibold text-[var(--text-primary)]">Priorities</span>
            </div>
            <div className="flex flex-col gap-1.5" role="list" aria-label="Priority actions">
              {actions.map((action) => (
                <div key={action.id} role="listitem">
                  <MissionAction
                    id={action.id}
                    title={action.title}
                    priority={action.priority}
                    companyName={action.companyName}
                  />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Revenue & Progress row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <Card className="border-0 shadow-none bg-gradient-to-br from-success-50 to-emerald-50 dark:from-success-950/30 dark:to-emerald-950/30">
          <CardContent className="p-3">
            <div className="flex items-center gap-1.5 mb-1">
              <TrendingUp className="h-3.5 w-3.5 text-success-600" aria-hidden="true" />
              <span className="text-xs font-semibold text-success-700 dark:text-success-300">Revenue Opportunity</span>
            </div>
            <p className="text-lg font-bold text-success-800 dark:text-success-200">
              SAR {props.pipelineValue.toLocaleString()}
            </p>
            <p className="text-[10px] text-success-600 dark:text-success-400">
              {props.activeDeals} صفقات نشطة
            </p>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-none bg-[var(--bg-secondary)]">
          <CardContent className="p-3">
            <MissionProgress
              value={props.activeDeals * 2 + props.signalsToday + props.decisionsPending}
              max={100}
              label="Completion"
              barClassName="bg-[var(--muhide-orange)]"
            />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
