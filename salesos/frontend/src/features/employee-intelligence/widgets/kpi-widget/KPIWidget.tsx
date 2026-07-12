'use client'

import { createWorkspaceWidget } from '@salesos/workspace'
import { useWorkspaceContext } from '../../workspace/EmployeeWorkspace'
import type { EmployeeKPIs } from '@/lib/api'
import { TrendingUp, Target, Activity, PieChart, BarChart3, LineChart } from 'lucide-react'
import { cn } from '@salesos/ui'

interface KPIItem {
  key: string
  label: string
  value: string
  icon: React.ReactNode
  color: string
  progress?: number
}

export function KPIView({ data }: { data: EmployeeKPIs }) {
  const kpis: KPIItem[] = [
    { key: 'revenue', label: 'الإيرادات', value: `${data.revenue.toLocaleString()}`, icon: <TrendingUp className="h-4 w-4" />, color: 'text-success-600 bg-success-50', progress: data.revenue > 0 ? Math.min(100, (data.revenue / (data.forecast || 1)) * 100) : 0 },
    { key: 'pipeline', label: 'خط التصفية', value: `${data.pipeline.toLocaleString()}`, icon: <Target className="h-4 w-4" />, color: 'text-info-600 bg-info-50', progress: data.pipeline > 0 ? 60 : 0 },
    { key: 'winRate', label: 'نسبة الفوز', value: `${Math.round(data.win_rate * 100)}%`, icon: <Activity className="h-4 w-4" />, color: data.win_rate >= 0.5 ? 'text-success-600 bg-success-50' : 'text-warning-600 bg-warning-50', progress: data.win_rate * 100 },
    { key: 'productivity', label: 'الإنتاجية', value: `${Math.round(data.productivity * 100)}%`, icon: <BarChart3 className="h-4 w-4" />, color: 'text-purple-600 bg-purple-50', progress: Math.min(100, data.productivity * 100) },
    { key: 'forecast', label: 'التوقعات', value: `${data.forecast.toLocaleString()}`, icon: <LineChart className="h-4 w-4" />, color: 'text-cyan-600 bg-cyan-50', progress: data.forecast > 0 ? 70 : 0 },
    { key: 'activities', label: 'النشاطات', value: `${data.activities}`, icon: <PieChart className="h-4 w-4" />, color: 'text-rose-600 bg-rose-50', progress: data.activities > 0 ? Math.min(100, (data.activities / 50) * 100) : 0 },
  ]

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2">
        {kpis.slice(0, 4).map((kpi) => (
          <div key={kpi.key} className="rounded-lg border border-[var(--border-subtle)] p-2.5">
            <div className="flex items-center gap-1.5 mb-1">
              <span className={cn('flex items-center justify-center w-6 h-6 rounded', kpi.color.split(' ')[1])}>
                <span className={kpi.color.split(' ')[0]}>{kpi.icon}</span>
              </span>
            </div>
            <p className="text-base font-semibold text-[var(--text-primary)]">{kpi.value}</p>
            <p className="text-[9px] text-[var(--text-muted)]">{kpi.label}</p>
            {kpi.progress !== undefined && (
              <div className="mt-1 h-1 w-full rounded-full bg-[var(--bg-secondary)] overflow-hidden">
                <div
                  className={cn('h-full rounded-full transition-all', kpi.color.split(' ')[0].replace('text-', 'bg-'))}
                  style={{ width: `${kpi.progress}%` }}
                />
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-2">
        {kpis.slice(4).map((kpi) => (
          <div key={kpi.key} className="rounded-lg bg-[var(--bg-secondary)] p-2.5 text-center">
            <p className="text-lg font-semibold text-[var(--text-primary)]">{kpi.value}</p>
            <p className="text-[9px] text-[var(--text-muted)]">{kpi.label}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export const KPIWidget = createWorkspaceWidget(
  { id: 'employeeKPIs', minHeight: '320px' },
  useWorkspaceContext,
  (widgets) => widgets.kpis,
  {
    metadata: { title: 'مؤشرات الأداء' },
    render: ({ data }) => <KPIView data={data} />,
  },
)
