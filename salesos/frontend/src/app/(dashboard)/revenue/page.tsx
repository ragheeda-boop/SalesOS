"use client"

import { useState, useEffect } from"react"
import api from"@/lib/api"
import { cn } from"@salesos/ui"
import { useTranslation } from"@/lib/i18n"
import { ErrorBoundary } from"@/components/error-boundary"
import {
 DollarSign,
 TrendingUp,
 TrendingDown,
 Users,
 AlertTriangle,
 RefreshCw,
 Target,
 BarChart3,
} from"lucide-react"

interface RevenueMetrics {
 arr: number
 arr_trend: number
 nrr: number
 nrr_trend: number
 churn_rate: number
 churn_trend: number
 expansion_revenue: number
 expansion_trend: number
 total_pipe: number
 forecast: number
}

interface TrendPoint {
 month: string
 value: number
}

interface ForecastVsActual {
 month: string
 forecast: number
 actual: number
}

interface RepLeaderboardEntry {
 rep_id: string
 rep_name: string
 revenue: number
 quota_attainment: number
 deals_closed: number
}

interface DashboardData {
 metrics: RevenueMetrics
 trends: {
 arr: TrendPoint[]
 nrr: TrendPoint[]
 churn: TrendPoint[]
 expansion: TrendPoint[]
 }
 forecast_vs_actual: ForecastVsActual[]
 leaderboard: RepLeaderboardEntry[]
}

function MetricCard({
 label,
 value,
 trend,
 icon,
 trendLabel,
}: {
 label: string
 value: string
 trend?: number
 icon: React.ReactNode
 trendLabel?: string
}) {
 const trendColor =
 trend === undefined
 ?"text-[var(--text-muted)]"
 : trend >= 0
 ?"text-[var(--status-success-text)]"
 :"text-[var(--status-danger-text)]"
 return (
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <div className="flex items-center justify-between">
 <p className="text-xs text-[var(--text-muted)]">{label}</p>
 <span className="text-[var(--text-muted)]">{icon}</span>
 </div>
 <p className="text-2xl font-bold text-[var(--text-primary)] mt-1">{value}</p>
 {trend !== undefined && (
 <div className={cn("flex items-center gap-1 mt-1 text-xs", trendColor)}>
 {trend >= 0 ? (
 <TrendingUp className="h-3 w-3" />
 ) : (
 <TrendingDown className="h-3 w-3" />
 )}
 <span>
 {Math.abs(trend).toFixed(1)}%
 {trendLabel && <span className="text-[var(--text-muted)] ml-1">{trendLabel}</span>}
 </span>
 </div>
 )}
 </div>
 )
}

function MiniTrendChart({
 data,
 color,
 height = 60,
}: {
 data: TrendPoint[]
 color: string
 height?: number
}) {
 if (!data.length) return null
 const values = data.map((d) => d.value)
 const min = Math.min(...values)
 const max = Math.max(...values)
 const range = max - min || 1
 const points = values
 .map(
 (v, i) =>
 `${(i / (values.length - 1)) * 100},${100 - ((v - min) / range) * 80}`
 )
 .join("")

 return (
 <svg viewBox="0 0 100 100" className="w-full" style={{ height }} preserveAspectRatio="none">
 <polyline fill="none" stroke={color} strokeWidth="2" points={points} />
 </svg>
 )
}

function ForecastVsActualChart({ data }: { data: ForecastVsActual[] }) {
 if (!data.length) return null
 const maxVal = Math.max(...data.map((d) => Math.max(d.forecast, d.actual)), 1)

 return (
 <div className="space-y-2">
 {data.map((d) => (
 <div key={d.month} className="space-y-1">
 <div className="flex items-center justify-between text-xs text-[var(--text-muted)]">
 <span>{d.month}</span>
 <span>
 Actual: {formatCurrency(d.actual)} / Forecast: {formatCurrency(d.forecast)}
 </span>
 </div>
 <div className="relative h-5 rounded bg-[var(--bg-tertiary)] overflow-hidden">
 <div
                className="absolute inset-y-0 start-0 rounded bg-green-500/60 transition-all"
 style={{ width: `${(d.actual / maxVal) * 100}%` }}
 />
 <div
 className="absolute inset-y-0 start-0 rounded border-2 border-dashed border-[var(--muhide-orange)]"
 style={{ width: `${(d.forecast / maxVal) * 100}%` }}
 />
 </div>
 </div>
 ))}
 <div className="flex items-center gap-4 text-xs text-[var(--text-muted)]">
 <span className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-sm bg-green-500/60" /> Actual
 </span>
 <span className="flex items-center gap-1">
 <span className="h-2 w-2 rounded-sm border border-dashed border-[var(--muhide-orange)]" /> Forecast
 </span>
 </div>
 </div>
 )
}

function formatCurrency(value: number): string {
 if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M SAR`
 if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K SAR`
 return `${value.toLocaleString()} SAR`
}

function LoadingSkeleton() {
 return (
 <div className="space-y-6 animate-pulse">
 <div className="h-8 w-48 rounded bg-[var(--bg-tertiary)]" />
 <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
 {[1, 2, 3, 4].map((i) => (
 <div key={i} className="h-28 rounded-xl bg-[var(--bg-tertiary)]" />
 ))}
 </div>
 <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
 <div className="h-64 rounded-xl bg-[var(--bg-tertiary)]" />
 <div className="h-64 rounded-xl bg-[var(--bg-tertiary)]" />
 </div>
 <div className="h-64 rounded-xl bg-[var(--bg-tertiary)]" />
 </div>
 )
}

function EmptyStateComponent({ onRetry }: { onRetry: () => void }) {
 return (
 <div className="flex flex-col items-center justify-center py-20 text-center">
 <BarChart3 className="h-12 w-12 text-[var(--text-muted)] mb-4" />
 <h3 className="text-lg font-semibold text-[var(--text-primary)]">No Revenue Data</h3>
 <p className="text-sm text-[var(--text-muted)] mt-1 max-w-md">
 Revenue metrics will appear here once opportunities and contracts are processed.
 </p>
 <button
 onClick={onRetry}
 className="mt-4 flex items-center gap-2 rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-sm text-white hover:opacity-90 transition"
 >
 <RefreshCw className="h-4 w-4" /> Refresh
 </button>
 </div>
 )
}

export default function RevenueDashboardPage() {
 const { t } = useTranslation()
 const [data, setData] = useState<DashboardData | null>(null)
 const [loading, setLoading] = useState(true)
 const [error, setError] = useState<string | null>(null)

 const fetchDashboard = async () => {
 setLoading(true)
 setError(null)
 try {
 const [dashboardRes, forecastRes, analyticsRes, leaderboardRes] = await Promise.all([
 api.get("/api/v1/revenue/dashboard"),
 api.get("/api/v1/forecast").catch(() => ({ data: null })),
 api.get("/api/v1/analytics/kpis").catch(() => ({ data: null })),
 api.get("/api/v1/workspace").catch(() => ({ data: null })),
 ])

 const dash = dashboardRes.data
 const forecast = forecastRes.data
 const analytics = analyticsRes.data
 const workspace = leaderboardRes.data

 const metrics: RevenueMetrics = {
 arr: workspace?.kpis?.revenue?.value ?? workspace?.opportunities?.total_value ?? dash?.total_value ?? 0,
 arr_trend: workspace?.kpis?.revenue?.change ?? 0,
 nrr: workspace?.kpis?.nrr?.value ?? 0,
 nrr_trend: workspace?.kpis?.nrr?.change ?? 0,
 churn_rate: workspace?.kpis?.churn?.value ?? 0,
 churn_trend: workspace?.kpis?.churn?.change ?? 0,
 expansion_revenue: workspace?.kpis?.forecast?.value ?? 0,
 expansion_trend: workspace?.kpis?.forecast?.change ?? 0,
 total_pipe: dash?.total_value ?? workspace?.opportunities?.total_value ?? 0,
 forecast: forecast?.total_weighted ?? workspace?.forecast?.total_weighted ?? 0,
 }

 // No synthetic trend invention — empty series until time-series API exists
 const trends = { arr: [] as {month:string;value:number}[], nrr: [] as {month:string;value:number}[], churn: [] as {month:string;value:number}[], expansion: [] as {month:string;value:number}[] }
 const forecastVsActual: ForecastVsActual[] = []

 const activeOpps = dash?.active_opportunities ?? workspace?.opportunities?.recent ?? []
 const leaderboard: RepLeaderboardEntry[] = (activeOpps as Array<{ id: string; name: string; value: number }>).slice(0, 5).map(
 (o, i: number) => ({
 rep_id: o.id || `opp-${i}`,
 rep_name: o.name || "Opportunity",
 revenue: Number(o.value) || 0,
 quota_attainment: 0,
 deals_closed: 0,
 })
 )

 setData({ metrics, trends, forecast_vs_actual: forecastVsActual, leaderboard })
 void analytics
 } catch (err) {
 setError(t("error.server_error"))
 } finally {
 setLoading(false)
 }
 }

 useEffect(() => {
 fetchDashboard()
 // eslint-disable-next-line react-hooks/exhaustive-deps
 }, [])

 if (loading) return <LoadingSkeleton />

 if (error) {
 return (
 <div className="flex flex-col items-center justify-center py-20 text-center">
 <AlertTriangle className="h-12 w-12 text-[var(--status-danger-text)] mb-4" />
 <h3 className="text-lg font-semibold text-[var(--text-primary)]">Error Loading Dashboard</h3>
 <p className="text-sm text-[var(--status-danger-text)] mt-1">{error}</p>
 <button
 onClick={fetchDashboard}
 className="mt-4 flex items-center gap-2 rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-sm text-white hover:opacity-90 transition"
 >
 <RefreshCw className="h-4 w-4" /> Retry
 </button>
 </div>
 )
 }

 if (!data) return <EmptyStateComponent onRetry={fetchDashboard} />

 return (
 <ErrorBoundary>
 <div className="space-y-6">
 {/* Header */}
 <div className="flex items-center justify-between">
 <div>
 <h1 className="text-xl font-bold text-[var(--text-primary)]">Revenue Dashboard</h1>
 <p className="text-sm text-[var(--text-muted)]">Key metrics, trends, and forecast tracking</p>
 </div>
 <button
 onClick={fetchDashboard}
 className="flex items-center gap-2 rounded-lg border border-[var(--border-default)] px-3 py-2 text-sm text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] transition"
 >
 <RefreshCw className="h-4 w-4" /> Refresh
 </button>
 </div>

 {/* Key Metrics */}
 <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
 <MetricCard
 label="ARR (Annual Recurring Revenue)"
 value={formatCurrency(data.metrics.arr)}
 trend={data.metrics.arr_trend}
 trendLabel="vs last period"
 icon={<DollarSign className="h-4 w-4" />}
 />
 <MetricCard
 label="NRR (Net Revenue Retention)"
 value={`${data.metrics.nrr}%`}
 trend={data.metrics.nrr_trend}
 trendLabel="vs last period"
 icon={<Target className="h-4 w-4" />}
 />
 <MetricCard
 label="Churn Rate"
 value={`${data.metrics.churn_rate}%`}
 trend={data.metrics.churn_trend}
 trendLabel="vs last period"
 icon={<TrendingDown className="h-4 w-4" />}
 />
 <MetricCard
 label="Expansion Revenue"
 value={formatCurrency(data.metrics.expansion_revenue)}
 trend={data.metrics.expansion_trend}
 trendLabel="vs last period"
 icon={<TrendingUp className="h-4 w-4" />}
 />
 </div>

 {/* Trend Charts */}
 <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
 {[
 { label:"ARR Trend", data: data.trends.arr, color:"#3B82F6", format: formatCurrency },
 { label:"NRR Trend", data: data.trends.nrr, color:"#10B981", format: (v: number) => `${v}%` },
 { label:"Churn Trend", data: data.trends.churn, color:"#EF4444", format: (v: number) => `${v}%` },
 { label:"Expansion Trend", data: data.trends.expansion, color:"#8B5CF6", format: formatCurrency },
 ].map((item) => (
 <div
 key={item.label}
 className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4"
 >
 <p className="text-xs text-[var(--text-muted)] mb-2">{item.label}</p>
 <MiniTrendChart data={item.data} color={item.color} height={50} />
 <div className="flex justify-between text-[10px] text-[var(--text-muted)] mt-1">
 <span>{item.data[0]?.month}</span>
 <span className="font-medium text-[var(--text-primary)]">
 {item.format(item.data[item.data.length - 1]?.value ?? 0)}
 </span>
 <span>{item.data[item.data.length - 1]?.month}</span>
 </div>
 </div>
 ))}
 </div>

 {/* Forecast vs Actual + Leaderboard */}
 <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
 {/* Forecast vs Actual */}
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
 Forecast vs Actual
 </h3>
 <ForecastVsActualChart data={data.forecast_vs_actual} />
 </div>

 {/* Rep Leaderboard */}
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
 Rep Leaderboard
 </h3>
 {data.leaderboard.length === 0 ? (
 <div className="flex items-center justify-center py-8 text-sm text-[var(--text-muted)]">
 <Users className="h-4 w-4 mr-2" /> No rep data available
 </div>
 ) : (
 <div className="space-y-2">
 {data.leaderboard.map((rep, i) => (
 <div
 key={rep.rep_id}
 className="flex items-center gap-3 rounded-lg px-3 py-2 hover:bg-[var(--bg-secondary)] transition"
 >
 <span
 className={cn(
"flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold",
 i === 0
 ?"bg-yellow-100 text-yellow-700"
 : i === 1
 ?"bg-gray-100 text-gray-600"
 : i === 2
 ?"bg-orange-100 text-orange-700"
 :"bg-[var(--bg-tertiary)] text-[var(--text-muted)]"
 )}
 >
 {i + 1}
 </span>
 <div className="flex-1 min-w-0">
 <p className="text-sm font-medium text-[var(--text-primary)] truncate">
 {rep.rep_name}
 </p>
 <p className="text-xs text-[var(--text-muted)]">
 {rep.deals_closed} deals closed
 </p>
 </div>
 <div className="text-right">
 <p className="text-sm font-medium text-[var(--text-primary)]">
 {formatCurrency(rep.revenue)}
 </p>
 <div className="flex items-center gap-1 justify-end">
 <div className="h-1.5 w-16 rounded-full bg-[var(--bg-tertiary)] overflow-hidden">
 <div
 className={cn(
"h-full rounded-full transition-all",
 rep.quota_attainment >= 100
 ?"bg-green-500"
 : rep.quota_attainment >= 75
 ?"bg-amber-500"
 :"bg-red-500"
 )}
 style={{ width: `${Math.min(rep.quota_attainment, 100)}%` }}
 />
 </div>
 <span className="text-[10px] text-[var(--text-muted)]">
 {rep.quota_attainment}%
 </span>
 </div>
 </div>
 </div>
 ))}
 </div>
 )}
 </div>
 </div>
 </div>
 </ErrorBoundary>
 )
}
