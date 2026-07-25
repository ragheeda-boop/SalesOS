"use client"

import { useState, useEffect, useMemo } from"react"
import Link from"next/link"
import api from"@/lib/api"
import { getTenantId } from"@/lib/hooks/useTenant"
import { useWorkflows, useWorkflowExecutions, type WorkflowExecution } from"@/lib/workflowQueries"
import { useTranslation } from"@/lib/i18n"
import { cn } from"@salesos/ui"
import { Badge, Button } from"@salesos/ui"
import { BarChart, LineChart, PieChart, MetricCard } from"@salesos/charts"
import {
 ArrowLeft,
 Workflow,
 CheckCircle,
 XCircle,
 Clock,
 TrendingUp,
 TrendingDown,
 Activity,
 AlertTriangle,
 RefreshCw,
 Play,
 BarChart3,
} from"lucide-react"

interface WorkflowAnalyticsSummary {
 total_workflows: number
 active_workflows: number
 draft_workflows: number
 total_executions: number
 successful_executions: number
 failed_executions: number
 completion_rate: number
 avg_duration_seconds: number
 failure_rate: number
 executions_over_time: { date: string; count: number; success: number; failed: number }[]
 top_workflows: { id: string; name: string; runs: number; success_rate: number }[]
 recent_executions: WorkflowExecution[]
}

function formatDuration(seconds: number): string {
 if (seconds < 60) return `${Math.round(seconds)}ث`
 if (seconds < 3600) return `${Math.round(seconds / 60)}د`
 return `${(seconds / 3600).toFixed(1)}س`
}

function formatDate(dateStr: string): string {
 try {
 return new Intl.DateTimeFormat("ar-SA", {
 month:"short",
 day:"numeric",
 hour:"2-digit",
 minute:"2-digit",
 }).format(new Date(dateStr))
 } catch {
 return dateStr
 }
}

function CompletionGauge({ rate }: { rate: number }) {
 const circumference = 2 * Math.PI * 60
 const offset = circumference - (rate / 100) * circumference
 const color = rate >= 80 ?"#10B981" : rate >= 50 ?"#F59E0B" :"#EF4444"

 return (
 <div className="flex flex-col items-center space-y-2">
 <h3 className="text-sm font-semibold text-[var(--text-primary)]">نسبة الإتمام</h3>
 <div className="relative">
 <svg width={140} height={140} viewBox="0 0 140 140">
 <circle
 cx={70}
 cy={70}
 r={60}
 fill="none"
 stroke="var(--bg-tertiary)"
 strokeWidth={10}
 />
 <circle
 cx={70}
 cy={70}
 r={60}
 fill="none"
 stroke={color}
 strokeWidth={10}
 strokeLinecap="round"
 strokeDasharray={circumference}
 strokeDashoffset={offset}
 transform="rotate(-90 70 70)"
 className="transition-all duration-1000"
 />
 </svg>
 <div className="absolute inset-0 flex flex-col items-center justify-center">
 <span className="text-2xl font-bold" style={{ color }}>{rate}%</span>
 <span className="text-[10px] text-[var(--text-muted)]">نسبة النجاح</span>
 </div>
 </div>
 </div>
 )
}

function FailureRateTrend({
 data,
}: {
 data: { date: string; count: number; success: number; failed: number }[]
}) {
 const chartData = data.map((d) => ({
 label: d.date,
 value: d.count > 0 ? Math.round((d.failed / d.count) * 100) : 0,
 }))

 return (
 <LineChart
 series={[{ name:"نسبة الفشل %", color:"#EF4444", data: chartData.map((d) => d.value) }]}
 title="معدل الفشل على مدار الوقت"
 height={220}
 />
 )
}

function ExecutionsOverTime({
 data,
}: {
 data: { date: string; count: number; success: number; failed: number }[]
}) {
 return (
 <BarChart
 data={data.map((d) => ({ label: d.date, value: d.success, color:"#10B981" }))}
 title="التنفيذات الناجحة"
 height={200}
 />
 )
}

function TopWorkflowsTable({
 workflows,
}: {
 workflows: { id: string; name: string; runs: number; success_rate: number }[]
}) {
 return (
 <div className="space-y-2">
 <h3 className="text-sm font-semibold text-[var(--text-primary)]">أكثر سير العمل استخداماً</h3>
 <div className="rounded-lg border border-[var(--border-default)] overflow-hidden">
 <table className="w-full text-sm">
 <thead>
 <tr className="bg-[var(--bg-secondary)] border-b border-[var(--border-default)]">
 <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">سير العمل</th>
 <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">التشغيلات</th>
 <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">نسبة النجاح</th>
 <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">الأداء</th>
 </tr>
 </thead>
 <tbody>
 {workflows.map((wf) => (
 <tr
 key={wf.id}
 className="border-b border-[var(--border-default)] last:border-0 hover:bg-[var(--bg-secondary)]"
 >
 <td className="px-3 py-2">
 <span className="text-sm font-medium text-[var(--text-primary)]">{wf.name}</span>
 </td>
 <td className="px-3 py-2 text-[var(--text-secondary)]">{wf.runs}</td>
 <td className="px-3 py-2">
 <Badge variant={wf.success_rate >= 80 ?"success" : wf.success_rate >= 50 ?"warning" :"danger"}>
 {wf.success_rate}%
 </Badge>
 </td>
 <td className="px-3 py-2">
 <div className="flex items-center gap-1">
 <div className="h-1.5 w-20 rounded-full bg-[var(--bg-tertiary)] overflow-hidden">
 <div
 className="h-full rounded-full transition-all duration-500"
 style={{
 width: `${wf.success_rate}%`,
 backgroundColor: wf.success_rate >= 80 ?"#10B981" : wf.success_rate >= 50 ?"#F59E0B" :"#EF4444",
 }}
 />
 </div>
 </div>
 </td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>
 </div>
 )
}

function ExecutionHistoryTable({
 executions,
}: {
 executions: WorkflowExecution[]
}) {
 const statusConfig: Record<string, { label: string; variant:"success" |"danger" |"warning" |"default" }> = {
 success: { label:"نجح", variant:"success" },
 failed: { label:"فشل", variant:"danger" },
 running: { label:"جاري", variant:"warning" },
 }

 return (
 <div className="space-y-2">
 <h3 className="text-sm font-semibold text-[var(--text-primary)]">سجل التنفيذ الأخير</h3>
 <div className="rounded-lg border border-[var(--border-default)] overflow-hidden">
 <table className="w-full text-sm">
 <thead>
 <tr className="bg-[var(--bg-secondary)] border-b border-[var(--border-default)]">
 <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">الحالة</th>
 <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">المُشغّل</th>
 <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">بدأ في</th>
 <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">انتهى في</th>
 </tr>
 </thead>
 <tbody>
 {executions.map((ex) => {
 const sc = statusConfig[ex.status] || statusConfig.running
 return (
 <tr
 key={ex.id}
 className="border-b border-[var(--border-default)] last:border-0 hover:bg-[var(--bg-secondary)]"
 >
 <td className="px-3 py-2">
 <Badge variant={sc.variant}>{sc.label}</Badge>
 </td>
 <td className="px-3 py-2 text-[var(--text-secondary)] text-xs">{ex.triggered_by}</td>
 <td className="px-3 py-2 text-[var(--text-muted)] text-xs">{formatDate(ex.started_at)}</td>
 <td className="px-3 py-2 text-[var(--text-muted)] text-xs">
 {ex.completed_at ? formatDate(ex.completed_at) :"—"}
 </td>
 </tr>
 )
 })}
 {executions.length === 0 && (
 <tr>
 <td colSpan={4} className="px-3 py-6 text-center text-xs text-[var(--text-muted)]">
 لا توجد تنفيذات بعد
 </td>
 </tr>
 )}
 </tbody>
 </table>
 </div>
 </div>
 )
}

export default function AutomationAnalyticsPage() {
 const { t } = useTranslation()
 const { data: workflows, isLoading: workflowsLoading } = useWorkflows()

 const [analytics, setAnalytics] = useState<WorkflowAnalyticsSummary | null>(null)
 const [loading, setLoading] = useState(true)
 const [error, setError] = useState<string | null>(null)

 useEffect(() => {
 const load = async () => {
 try {
 const res = await api.get("/api/v1/workflows/analytics", {
 headers: {"X-Tenant-Id": getTenantId() },
 })
 setAnalytics(res.data)
 } catch {
 // Fallback: derive basic analytics from workflow list
 if (workflows) {
 const active = workflows.filter((w) => w.status ==="active").length
 const draft = workflows.filter((w) => w.status ==="draft").length
 setAnalytics({
 total_workflows: workflows.length,
 active_workflows: active,
 draft_workflows: draft,
 total_executions: 0,
 successful_executions: 0,
 failed_executions: 0,
 completion_rate: 0,
 avg_duration_seconds: 0,
 failure_rate: 0,
 executions_over_time: [],
 top_workflows: workflows.map((w) => ({
 id: w.id,
 name: w.name,
 runs: 0,
 success_rate: 0,
 })),
 recent_executions: [],
 })
 } else {
 setError("Failed to load analytics")
 }
 } finally {
 setLoading(false)
 }
 }
 load()
 }, [workflows])

 if (loading || workflowsLoading) {
 return (
 <div className="space-y-6 animate-pulse p-6">
 <div className="h-8 w-48 rounded bg-[var(--bg-tertiary)]" />
 <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
 {[1, 2, 3, 4].map((i) => (
 <div key={i} className="h-24 rounded-xl bg-[var(--bg-tertiary)]" />
 ))}
 </div>
 <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
 <div className="h-80 rounded-xl bg-[var(--bg-tertiary)]" />
 <div className="h-80 rounded-xl bg-[var(--bg-tertiary)]" />
 </div>
 </div>
 )
 }

 if (error) {
 return (
 <div className="flex items-center justify-center py-20" style={{ color:"var(--color-error, #EF4444)" }}>
 {error}
 </div>
 )
 }

 return (
 <div className="space-y-6">
 {/* Header */}
 <div className="flex items-center gap-3">
 <Link
 href="/automation"
 className="rounded-lg p-1.5 hover:bg-[var(--bg-secondary)] transition-colors text-[var(--text-muted)]"
 >
 <ArrowLeft className="h-4 w-4" />
 </Link>
 <div>
 <h1 className="text-xl font-bold text-[var(--text-primary)]">تحليلات الأتمتة</h1>
 <p className="text-sm text-[var(--text-muted)]">معدلات الإتمام والمدة المتوسطة ونسبة الفشل</p>
 </div>
 </div>

 {/* Key Metrics */}
 <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
 <MetricCard
 label="سير العمل النشط"
 value={String(analytics?.active_workflows ?? 0)}
 icon={<Workflow className="h-4 w-4" />}
 />
 <MetricCard
 label="إجمالي التشغيلات"
 value={String(analytics?.total_executions ?? 0)}
 icon={<Play className="h-4 w-4" />}
 />
 <MetricCard
 label="نسبة النجاح"
 value={`${analytics?.completion_rate ?? 0}%`}
 icon={<CheckCircle className="h-4 w-4" />}
 />
 <MetricCard
 label="المدة المتوسطة"
 value={formatDuration(analytics?.avg_duration_seconds ?? 0)}
 icon={<Clock className="h-4 w-4" />}
 />
 </div>

 {/* Charts Grid */}
 <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
 {/* Completion Gauge */}
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-6 flex items-center justify-center">
 <CompletionGauge rate={analytics?.completion_rate ?? 0} />
 </div>

 {/* Executions Over Time */}
 <div className="lg:col-span-2 rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <ExecutionsOverTime data={analytics?.executions_over_time ?? []} />
 </div>
 </div>

 <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
 {/* Failure Rate Trend */}
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <FailureRateTrend data={analytics?.executions_over_time ?? []} />
 </div>

 {/* Top Workflows */}
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <TopWorkflowsTable workflows={analytics?.top_workflows ?? []} />
 </div>
 </div>

 {/* Recent Executions */}
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <ExecutionHistoryTable executions={analytics?.recent_executions ?? []} />
 </div>
 </div>
 )
}
