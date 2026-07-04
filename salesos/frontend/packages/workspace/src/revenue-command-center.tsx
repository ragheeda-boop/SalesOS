import { useState } from 'react'
import { cn } from '@salesos/ui'
import { MetricCard, BarChart, type ChartDataPoint } from '@salesos/charts'
import type { ActivityEvent } from './global-activity-feed'
import { Clock, TrendingUp, Target, DollarSign, AlertCircle, Zap, Calendar, Users, BarChart3, ArrowUpRight } from 'lucide-react'

export interface RevenueMetrics {
  today: { revenue: number; meetings: number; deals: number; signals: number }
  pipeline: { total: number; atRisk: number; won: number; lost: number }
  forecast: { current: number; target: number; confidence: number }
  topAccounts: Array<{ name: string; revenue: number; probability: number; stage: string }>
  weeklyTrend: ChartDataPoint[]
  decisions: Array<{ id: string; title: string; impact: string; confidence: number; timestamp: number }>
}

interface RevenueCommandCenterProps {
  metrics: RevenueMetrics
  className?: string
  onViewAll?: (section: string) => void
}

export function RevenueCommandCenter({ metrics, className, onViewAll }: RevenueCommandCenterProps) {
  const [timeRange, setTimeRange] = useState<'day' | 'week' | 'month'>('day')

  const atRiskPercent = metrics.pipeline.total > 0
    ? Math.round((metrics.pipeline.atRisk / metrics.pipeline.total) * 100)
    : 0

  const forecastProgress = metrics.forecast.target > 0
    ? Math.round((metrics.forecast.current / metrics.forecast.target) * 100)
    : 0

  return (
    <div className={cn('space-y-6', className)}>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">مركز قيادة الإيرادات</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {new Date().toLocaleDateString('ar-SA', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>
        <div className="flex gap-1 rounded-lg border border-gray-200 p-0.5 dark:border-gray-700">
          {(['day', 'week', 'month'] as const).map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={cn(
                'rounded-md px-3 py-1 text-xs transition',
                timeRange === range
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              )}
            >
              {range === 'day' ? 'اليوم' : range === 'week' ? 'الأسبوع' : 'الشهر'}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard
          label="إيرادات اليوم"
          value={`$${metrics.today.revenue.toLocaleString()}`}
          trend={{ direction: 'up', percentage: 12 }}
          icon={<DollarSign className="h-4 w-4 text-green-600" />}
        />
        <MetricCard
          label="الاجتماعات"
          value={metrics.today.meetings.toString()}
          icon={<Calendar className="h-4 w-4 text-blue-600" />}
        />
        <MetricCard
          label="الصفقات النشطة"
          value={metrics.today.deals.toString()}
          icon={<Target className="h-4 w-4 text-amber-600" />}
        />
        <MetricCard
          label="الإشارات الجديدة"
          value={metrics.today.signals.toString()}
          trend={{ direction: 'up', percentage: 8 }}
          icon={<Zap className="h-4 w-4 text-purple-600" />}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="rounded-xl border bg-white p-5 dark:border-gray-700 dark:bg-gray-900 lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">الفرص حسب المرحلة</h3>
            <button onClick={() => onViewAll?.('pipeline')} className="text-xs text-blue-600 hover:underline">
              عرض الكل
            </button>
          </div>
          <MetricCard label="قيمة الأنابيب" value={`$${metrics.pipeline.total.toLocaleString()}`} />
          <div className="mt-4 grid grid-cols-3 gap-3">
            <div className="rounded-lg bg-amber-50 p-3 dark:bg-amber-900/20">
              <p className="text-xs text-amber-600 dark:text-amber-400">في خطر</p>
              <p className="text-lg font-bold text-amber-700 dark:text-amber-300">
                ${metrics.pipeline.atRisk.toLocaleString()}
              </p>
              <p className="text-[10px] text-amber-500">%{atRiskPercent} من الأنابيب</p>
            </div>
            <div className="rounded-lg bg-green-50 p-3 dark:bg-green-900/20">
              <p className="text-xs text-green-600 dark:text-green-400">مغلقة (فوز)</p>
              <p className="text-lg font-bold text-green-700 dark:text-green-300">
                ${metrics.pipeline.won.toLocaleString()}
              </p>
            </div>
            <div className="rounded-lg bg-red-50 p-3 dark:bg-red-900/20">
              <p className="text-xs text-red-600 dark:text-red-400">مغلقة (خسارة)</p>
              <p className="text-lg font-bold text-red-700 dark:text-red-300">
                ${metrics.pipeline.lost.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-xl border bg-white p-5 dark:border-gray-700 dark:bg-gray-900">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">التوقعات</h3>
            <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-medium text-blue-700 dark:bg-blue-900 dark:text-blue-300">
              %{metrics.forecast.confidence} ثقة
            </span>
          </div>
          <div className="relative pt-3">
            <div className="flex items-baseline justify-between">
              <span className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                ${metrics.forecast.current.toLocaleString()}
              </span>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                من ${metrics.forecast.target.toLocaleString()}
              </span>
            </div>
            <div className="mt-3 h-3 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
              <div
                className={cn(
                  'h-full rounded-full transition-all',
                  forecastProgress >= 100 ? 'bg-green-500' : forecastProgress >= 75 ? 'bg-blue-500' : forecastProgress >= 50 ? 'bg-amber-500' : 'bg-red-500'
                )}
                style={{ width: `${Math.min(forecastProgress, 100)}%` }}
              />
            </div>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">%{forecastProgress} من الهدف</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="rounded-xl border bg-white p-5 dark:border-gray-700 dark:bg-gray-900">
          <h3 className="mb-4 font-semibold text-gray-900 dark:text-gray-100">أولويات اليوم</h3>
          <div className="space-y-2">
            {[
              { label: 'مراجعة عقود تجديد', priority: 'high', account: 'شركة التقنية' },
              { label: 'متابعة صفقة الرياض', priority: 'critical', account: 'مؤسسة الرياض' },
              { label: 'اجتماع عرض منتج', priority: 'high', account: 'شركة المستقبل' },
              { label: 'تحديث بيانات العميل', priority: 'medium', account: 'مجموعة النور' },
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-3 rounded-lg border border-gray-100 p-3 dark:border-gray-800">
                <div className={cn(
                  'h-2 w-2 shrink-0 rounded-full',
                  item.priority === 'critical' ? 'bg-red-500' : item.priority === 'high' ? 'bg-amber-500' : 'bg-blue-500'
                )} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{item.label}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{item.account}</p>
                </div>
                <ArrowUpRight className="h-4 w-4 shrink-0 text-gray-400" />
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border bg-white p-5 dark:border-gray-700 dark:bg-gray-900 lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">الحسابات الساخنة</h3>
            <button onClick={() => onViewAll?.('accounts')} className="text-xs text-blue-600 hover:underline">
              عرض الكل
            </button>
          </div>
          <div className="space-y-2">
            {metrics.topAccounts.map((account, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg border border-gray-100 p-3 dark:border-gray-800">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{account.name}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{account.stage}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    ${account.revenue.toLocaleString()}
                  </span>
                  <span className={cn(
                    'rounded-full px-2 py-0.5 text-[10px] font-medium',
                    account.probability >= 70 ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
                    account.probability >= 40 ? 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300' :
                    'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                  )}>
                    %{account.probability}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border bg-white p-5 dark:border-gray-700 dark:bg-gray-900">
          <h3 className="mb-4 font-semibold text-gray-900 dark:text-gray-100">قرارات AI</h3>
          <div className="space-y-2">
            {metrics.decisions.slice(0, 5).map((decision) => (
              <div key={decision.id} className="flex items-start gap-3 border-b border-gray-100 pb-2 last:border-0 dark:border-gray-800">
                <Zap className="mt-0.5 h-4 w-4 shrink-0 text-purple-600" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900 dark:text-gray-100">{decision.title}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{decision.impact}</p>
                </div>
                <span className="shrink-0 rounded bg-purple-100 px-1.5 py-0.5 text-[10px] text-purple-700 dark:bg-purple-900 dark:text-purple-300">
                  %{decision.confidence}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border bg-white p-5 dark:border-gray-700 dark:bg-gray-900">
          <h3 className="mb-4 font-semibold text-gray-900 dark:text-gray-100">اتجاهات الإيرادات</h3>
          <BarChart
            data={metrics.weeklyTrend}
            height={180}
          />
        </div>
      </div>
    </div>
  )
}
