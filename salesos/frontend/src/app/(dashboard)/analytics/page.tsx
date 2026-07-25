"use client"

import { useState, useEffect } from"react"
import Link from"next/link"
import api from"@/lib/api"
import { cn } from"@salesos/ui"
import { Badge } from"@salesos/ui"
import { BarChart, LineChart, PieChart, MetricCard } from"@salesos/charts"
import { useExecutiveDashboard } from"@/lib/hooks/executiveQueries"
import { ExportShareBar } from"@/components/analytics"
import {
 DollarSign,
 TrendingUp,
 Target,
 BarChart3,
 Users,
 Workflow,
 ArrowLeft,
 RefreshCw,
 Download,
 Share2,
 FileText,
 Calendar,
 ChevronRight,
 AlertTriangle,
} from"lucide-react"

interface OverviewMetrics {
 total_revenue: number
 revenue_trend: number
 total_pipeline: number
 pipeline_trend: number
 win_rate: number
 win_rate_trend: number
 active_employees: number
 employees_trend: number
 active_workflows: number
 workflows_trend: number
 conversion_rate: number
}

interface DomainCard {
 title: string
 description: string
 href: string
 icon: React.ReactNode
 metric: string
 metric_label: string
 color: string
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
 <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
 {[1, 2, 3, 4, 5, 6].map((i) => (
 <div key={i} className="h-40 rounded-xl bg-[var(--bg-tertiary)]" />
 ))}
 </div>
 </div>
 )
}

export default function AnalyticsOverviewPage() {
 const { data: execData, isLoading: execLoading, error: execError } = useExecutiveDashboard()
 const [loading, setLoading] = useState(true)
 const [error, setError] = useState<string | null>(null)

 useEffect(() => {
 if (!execLoading) {
 setLoading(false)
 if (execError) setError("Failed to load analytics overview")
 }
 }, [execLoading, execError])

 if (loading || execLoading) return <LoadingSkeleton />

 if (error || execError) {
 return (
 <div className="flex flex-col items-center justify-center py-20 text-center">
 <AlertTriangle className="h-12 w-12 text-[var(--danger-500)] mb-4" />
 <p className="text-sm text-[var(--danger-500)] mb-4">{error ||"Failed to load analytics"}</p>
 <button
 onClick={() => window.location.reload()}
 className="flex items-center gap-2 rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-sm text-white hover:opacity-90 transition"
 >
 <RefreshCw className="h-4 w-4" /> Retry
 </button>
 </div>
 )
 }

 const { revenue, pipeline, team } = execData ?? {}

 const overviewMetrics: OverviewMetrics = {
 total_revenue: revenue?.total_booked ?? 0,
 revenue_trend: revenue?.growth_percent ?? 0,
 total_pipeline: pipeline?.total_value ?? 0,
 pipeline_trend: 0,
 win_rate: pipeline?.win_rate ?? 0,
 win_rate_trend: 0,
 active_employees: team?.active_employees ?? 0,
 employees_trend: 0,
 active_workflows: 0,
 workflows_trend: 0,
 conversion_rate: pipeline && pipeline.total_deals > 0 ? Math.round((pipeline.won_deals / pipeline.total_deals) * 100) : 0,
 }

 const domains: DomainCard[] = [
 {
 title:"Sales Analytics",
 description:"Revenue, deals, and rep performance",
 href:"/analytics/sales",
 icon: <DollarSign className="h-5 w-5" />,
 metric: formatCurrency(overviewMetrics.total_revenue),
 metric_label:"Total Revenue",
 color:"text-[var(--status-success-text)]",
 },
 {
 title:"Revenue Analytics",
 description:"ARR, NRR, churn, and forecast",
 href:"/analytics/revenue",
 icon: <TrendingUp className="h-5 w-5" />,
 metric: formatCurrency(overviewMetrics.total_pipeline),
 metric_label:"Total Pipeline",
 color:"text-blue-600",
 },
 {
 title:"Pipeline Analytics",
 description:"Conversion, velocity, and health",
 href:"/analytics/pipeline",
 icon: <BarChart3 className="h-5 w-5" />,
 metric: `${overviewMetrics.win_rate}%`,
 metric_label:"Win Rate",
 color:"text-[var(--chart-purple)]",
 },
 {
 title:"Employee Analytics",
 description:"Performance scores and signals",
 href:"/analytics/employees",
 icon: <Users className="h-5 w-5" />,
 metric: String(overviewMetrics.active_employees),
 metric_label:"Active Employees",
 color:"text-[var(--status-warning-text)]",
 },
 {
 title:"Automation Analytics",
 description:"Workflow execution and performance",
 href:"/analytics/automation",
 icon: <Workflow className="h-5 w-5" />,
 metric: String(overviewMetrics.active_workflows),
 metric_label:"Active Workflows",
 color:"text-indigo-600",
 },
 ]

 return (
 <div className="space-y-6">
 {/* Header */}
 <div className="flex items-center justify-between">
 <div>
 <h1 className="text-xl font-bold text-[var(--text-primary)]">Analytics Overview</h1>
 <p className="text-sm text-[var(--text-muted)]">Key metrics across all domains</p>
 </div>
 <div className="flex items-center gap-2">
 <Link
 href="/analytics/reports/builder"
 className="flex items-center gap-2 rounded-lg border border-[var(--border-default)] px-3 py-2 text-sm text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] transition"
 >
 <FileText className="h-4 w-4" /> Report Builder
 </Link>
 <ExportShareBar reportName="Analytics Overview" />
 </div>
 </div>

 {/* Key Metrics */}
 <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
 <MetricCard
 label="Total Revenue"
 value={formatCurrency(overviewMetrics.total_revenue)}
 trend={{ direction: overviewMetrics.revenue_trend >= 0 ?"up" :"down", percentage: Math.abs(overviewMetrics.revenue_trend) }}
 icon={<DollarSign className="h-4 w-4" />}
 />
 <MetricCard
 label="Pipeline Value"
 value={formatCurrency(overviewMetrics.total_pipeline)}
 icon={<TrendingUp className="h-4 w-4" />}
 />
 <MetricCard
 label="Win Rate"
 value={`${overviewMetrics.win_rate}%`}
 icon={<Target className="h-4 w-4" />}
 />
 <MetricCard
 label="Conversion Rate"
 value={`${overviewMetrics.conversion_rate}%`}
 icon={<BarChart3 className="h-4 w-4" />}
 />
 </div>

 {/* Domain Dashboards */}
 <div>
 <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Domain Dashboards</h2>
 <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
 {domains.map((domain) => (
 <Link
 key={domain.href}
 href={domain.href}
 className="group rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4 hover:border-[var(--muhide-orange)]/30 hover:shadow-sm transition-all"
 >
 <div className="flex items-start justify-between mb-3">
 <div className={cn("p-2 rounded-lg bg-[var(--bg-secondary)]", domain.color)}>
 {domain.icon}
 </div>
 <ChevronRight className="h-4 w-4 text-[var(--text-muted)] group-hover:text-[var(--muhide-orange)] transition" />
 </div>
 <h3 className="text-sm font-semibold text-[var(--text-primary)]">{domain.title}</h3>
 <p className="text-xs text-[var(--text-muted)] mt-1">{domain.description}</p>
 <div className="mt-3 pt-3 border-t border-[var(--border-default)]">
 <p className="text-lg font-bold text-[var(--text-primary)]">{domain.metric}</p>
 <p className="text-[10px] text-[var(--text-muted)]">{domain.metric_label}</p>
 </div>
 </Link>
 ))}
 </div>
 </div>

 {/* Quick Insights */}
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Quick Insights</h3>
 <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
 <div className="rounded-lg bg-[var(--bg-secondary)] p-3">
 <p className="text-xs text-[var(--text-muted)]">Revenue Growth</p>
 <p className={cn("text-lg font-bold", overviewMetrics.revenue_trend >= 0 ?"text-[var(--status-success-text)]" :"text-[var(--status-danger-text)]")}>
 {overviewMetrics.revenue_trend >= 0 ?"+" :""}{overviewMetrics.revenue_trend}%
 </p>
 <p className="text-[10px] text-[var(--text-muted)]">vs last period</p>
 </div>
 <div className="rounded-lg bg-[var(--bg-secondary)] p-3">
 <p className="text-xs text-[var(--text-muted)]">Team Performance</p>
 <p className="text-lg font-bold text-[var(--text-primary)]">
 {overviewMetrics.active_employees} active
 </p>
 <p className="text-[10px] text-[var(--text-muted)]">employees this period</p>
 </div>
 <div className="rounded-lg bg-[var(--bg-secondary)] p-3">
 <p className="text-xs text-[var(--text-muted)]">Pipeline Health</p>
 <p className="text-lg font-bold text-[var(--text-primary)]">
 {overviewMetrics.conversion_rate}% conversion
 </p>
 <p className="text-[10px] text-[var(--text-muted)]">lead to close rate</p>
 </div>
 </div>
 </div>
 </div>
 )
}
