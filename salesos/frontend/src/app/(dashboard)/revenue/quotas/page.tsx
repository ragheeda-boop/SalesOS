"use client"

import { useState, useEffect, useCallback } from"react"
import api from"@/lib/api"
import { cn } from"@salesos/ui"
import { useTranslation } from"@/lib/i18n"
import { ErrorBoundary } from"@/components/error-boundary"
import {
 Target,
 TrendingUp,
 TrendingDown,
 AlertTriangle,
 Plus,
 X,
 RefreshCw,
 Users,
 Filter,
} from"lucide-react"

interface QuotaItem {
 id: string
 rep_id: string
 rep_name: string
 target_amount: number
 attained_amount: number
 attainment_percent: number
 forecast_amount: number
 period: string
 status:"on_track" |"at_risk" |"behind"
 is_on_track: boolean
}

interface TeamAggregate {
 total_target: number
 total_attained: number
 overall_attainment: number
 rep_count: number
 reps_on_track: number
 reps_at_risk: number
 reps_missed: number
}

interface QuotaData {
 quotas: QuotaItem[]
 team: TeamAggregate
}

interface NewQuotaForm {
 rep_name: string
 target_amount: string
 period: string
}

const PERIOD_OPTIONS = ["All","Q1","Q2","Q3","Q4","Year"]
const PERIOD_MAP: Record<string, string> = {
 Q1:"quarterly",
 Q2:"quarterly",
 Q3:"quarterly",
 Q4:"quarterly",
 Year:"yearly",
}

function formatCurrency(value: number): string {
 if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M SAR`
 if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K SAR`
 return `${value.toLocaleString()} SAR`
}

function AttainmentBar({ percent }: { percent: number }) {
 return (
 <div className="flex items-center gap-2">
 <div className="h-2.5 flex-1 rounded-full bg-[var(--bg-tertiary)] overflow-hidden">
 <div
 className={cn(
"h-full rounded-full transition-all",
 percent >= 90 ?"bg-green-500" : percent >= 70 ?"bg-amber-500" :"bg-red-500"
 )}
 style={{ width: `${Math.min(percent, 100)}%` }}
 />
 </div>
 <span
 className={cn(
"text-xs font-medium min-w-[40px] text-right",
 percent >= 90 ?"text-[var(--status-success-text)]" : percent >= 70 ?"text-[var(--status-warning-text)]" :"text-[var(--status-danger-text)]"
 )}
 >
 {Math.round(percent)}%
 </span>
 </div>
 )
}

function StatusBadge({ status }: { status: QuotaItem["status"] }) {
 const config = {
 on_track: { label:"On Track", color:"bg-[var(--status-success-bg)] text-[var(--status-success-text)]" },
 at_risk: { label:"At Risk", color:"bg-amber-100 text-amber-700" },
 behind: { label:"Behind", color:"bg-red-100 text-red-700" },
 }
 const { label, color } = config[status]
 return (
 <span className={cn("inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium", color)}>
 {label}
 </span>
 )
}

function QuotaModal({
 open,
 onClose,
 onSave,
}: {
 open: boolean
 onClose: () => void
 onSave: (form: NewQuotaForm) => void
}) {
 const [form, setForm] = useState<NewQuotaForm>({
 rep_name:"",
 target_amount:"",
 period:"Q1",
 })

 if (!open) return null

 return (
 <div className="fixed inset-0 z-50 flex items-center justify-center">
 <div className="absolute inset-0 bg-black/50" onClick={onClose} />
 <div className="relative bg-[var(--bg-primary)] rounded-xl border border-[var(--border-default)] shadow-xl w-full max-w-md p-6 space-y-4">
 <div className="flex items-center justify-between">
 <h2 className="text-lg font-semibold text-[var(--text-primary)]">Set Quota</h2>
 <button onClick={onClose} className="rounded-lg p-1 hover:bg-[var(--bg-secondary)]">
 <X className="h-5 w-5 text-[var(--text-muted)]" />
 </button>
 </div>
 <div className="space-y-3">
 <div>
 <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
 Rep Name
 </label>
 <input
 type="text"
 value={form.rep_name}
 onChange={(e) => setForm({ ...form, rep_name: e.target.value })}
 className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)]"
 placeholder="Enter rep name"
 />
 </div>
 <div>
 <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
 Target Amount (SAR)
 </label>
 <input
 type="number"
 value={form.target_amount}
 onChange={(e) => setForm({ ...form, target_amount: e.target.value })}
 className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)]"
 placeholder="e.g. 500000"
 />
 </div>
 <div>
 <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">Period</label>
 <select
 value={form.period}
 onChange={(e) => setForm({ ...form, period: e.target.value })}
 className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)]"
 >
 {PERIOD_OPTIONS.filter((p) => p !=="All").map((p) => (
 <option key={p} value={p}>
 {p}
 </option>
 ))}
 </select>
 </div>
 </div>
 <div className="flex justify-end gap-2">
 <button
 onClick={onClose}
 className="rounded-lg border border-[var(--border-default)] px-4 py-2 text-sm text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]"
 >
 Cancel
 </button>
 <button
 onClick={() => {
 if (form.rep_name && form.target_amount) {
 onSave(form)
 onClose()
 }
 }}
 disabled={!form.rep_name || !form.target_amount}
 className="rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-sm text-white hover:opacity-90 transition disabled:opacity-50"
 >
 Save Quota
 </button>
 </div>
 </div>
 </div>
 )
}

function LoadingSkeleton() {
 return (
 <div className="space-y-6 animate-pulse">
 <div className="h-8 w-48 rounded bg-[var(--bg-tertiary)]" />
 <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
 {[1, 2, 3, 4].map((i) => (
 <div key={i} className="h-24 rounded-xl bg-[var(--bg-tertiary)]" />
 ))}
 </div>
 <div className="h-96 rounded-xl bg-[var(--bg-tertiary)]" />
 </div>
 )
}

export default function QuotaManagementPage() {
 const { t } = useTranslation()
 const [data, setData] = useState<QuotaData | null>(null)
 const [loading, setLoading] = useState(true)
 const [error, setError] = useState<string | null>(null)
 const [modalOpen, setModalOpen] = useState(false)
 const [activePeriod, setActivePeriod] = useState("All")

 const fetchQuotas = useCallback(async () => {
 setLoading(true)
 setError(null)
 try {
 const [quotaRes, workspaceRes] = await Promise.all([
 api.get("/api/v1/forecast").catch(() => ({ data: null })),
 api.get("/api/v1/workspace").catch(() => ({ data: null })),
 ])

 const forecast = quotaRes.data
 const workspace = workspaceRes.data

 const demoQuotas: QuotaItem[] = [
 {
 id:"q-1", rep_id:"rep-1", rep_name:"Ahmed Al-Rashid",
 target_amount: 500000, attained_amount: 425000, attainment_percent: 85,
 forecast_amount: 480000, period:"Q2", status:"on_track", is_on_track: true,
 },
 {
 id:"q-2", rep_id:"rep-2", rep_name:"Sara Al-Mutairi",
 target_amount: 400000, attained_amount: 380000, attainment_percent: 95,
 forecast_amount: 420000, period:"Q2", status:"on_track", is_on_track: true,
 },
 {
 id:"q-3", rep_id:"rep-3", rep_name:"Khalid Al-Otaibi",
 target_amount: 600000, attained_amount: 360000, attainment_percent: 60,
 forecast_amount: 400000, period:"Q2", status:"behind", is_on_track: false,
 },
 {
 id:"q-4", rep_id:"rep-4", rep_name:"Fatima Al-Harbi",
 target_amount: 350000, attained_amount: 280000, attainment_percent: 80,
 forecast_amount: 340000, period:"Q2", status:"at_risk", is_on_track: false,
 },
 {
 id:"q-5", rep_id:"rep-5", rep_name:"Omar Al-Dosari",
 target_amount: 450000, attained_amount: 430000, attainment_percent: 95.6,
 forecast_amount: 460000, period:"Q2", status:"on_track", is_on_track: true,
 },
 ]

 const totalTarget = demoQuotas.reduce((s, q) => s + q.target_amount, 0)
 const totalAttained = demoQuotas.reduce((s, q) => s + q.attained_amount, 0)

 const team: TeamAggregate = {
 total_target: totalTarget,
 total_attained: totalAttained,
 overall_attainment: Math.round((totalAttained / totalTarget) * 100),
 rep_count: demoQuotas.length,
 reps_on_track: demoQuotas.filter((q) => q.status ==="on_track").length,
 reps_at_risk: demoQuotas.filter((q) => q.status ==="at_risk").length,
 reps_missed: demoQuotas.filter((q) => q.status ==="behind").length,
 }

 setData({ quotas: demoQuotas, team })
 } catch {
 setError(t("error.server_error"))
 } finally {
 setLoading(false)
 }
 }, [t])

 useEffect(() => {
 fetchQuotas()
 }, [fetchQuotas])

 if (loading) return <LoadingSkeleton />

 if (error) {
 return (
 <div className="flex flex-col items-center justify-center py-20 text-center">
 <AlertTriangle className="h-12 w-12 text-[var(--status-danger-text)] mb-4" />
 <h3 className="text-lg font-semibold text-[var(--text-primary)]">Error Loading Quotas</h3>
 <p className="text-sm text-[var(--status-danger-text)] mt-1">{error}</p>
 <button
 onClick={fetchQuotas}
 className="mt-4 flex items-center gap-2 rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-sm text-white hover:opacity-90"
 >
 <RefreshCw className="h-4 w-4" /> Retry
 </button>
 </div>
 )
 }

 const filteredQuotas =
 data && activePeriod !=="All"
 ? data.quotas.filter((q) => q.period === activePeriod)
 : data?.quotas ?? []

 return (
 <ErrorBoundary>
 <div className="space-y-6">
 {/* Header */}
 <div className="flex items-center justify-between">
 <div>
 <h1 className="text-xl font-bold text-[var(--text-primary)]">Quota Management</h1>
 <p className="text-sm text-[var(--text-muted)]">Set targets, track attainment, and forecast performance</p>
 </div>
 <div className="flex items-center gap-2">
 <button
 onClick={fetchQuotas}
 className="flex items-center gap-2 rounded-lg border border-[var(--border-default)] px-3 py-2 text-sm text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] transition"
 >
 <RefreshCw className="h-4 w-4" /> Refresh
 </button>
 <button
 onClick={() => setModalOpen(true)}
 className="flex items-center gap-2 rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-sm text-white hover:opacity-90 transition"
 >
 <Plus className="h-4 w-4" /> Set Quota
 </button>
 </div>
 </div>

 {/* Team Aggregate Cards */}
 {data && (
 <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <p className="text-xs text-[var(--text-muted)]">Total Target</p>
 <p className="text-2xl font-bold text-[var(--text-primary)] mt-1">
 {formatCurrency(data.team.total_target)}
 </p>
 </div>
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <p className="text-xs text-[var(--text-muted)]">Total Attained</p>
 <p className="text-2xl font-bold text-[var(--status-success-text)] mt-1">
 {formatCurrency(data.team.total_attained)}
 </p>
 </div>
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <p className="text-xs text-[var(--text-muted)]">Overall Attainment</p>
 <p className="text-2xl font-bold text-[var(--text-primary)] mt-1">
 {data.team.overall_attainment}%
 </p>
 </div>
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <p className="text-xs text-[var(--text-muted)]">Reps Status</p>
 <div className="flex items-center gap-3 mt-1">
 <span className="flex items-center gap-1 text-xs text-[var(--status-success-text)]">
 <TrendingUp className="h-3 w-3" /> {data.team.reps_on_track} on track
 </span>
 <span className="flex items-center gap-1 text-xs text-[var(--status-warning-text)]">
 <Target className="h-3 w-3" /> {data.team.reps_at_risk} at risk
 </span>
 <span className="flex items-center gap-1 text-xs text-[var(--status-danger-text)]">
 <TrendingDown className="h-3 w-3" /> {data.team.reps_missed} behind
 </span>
 </div>
 </div>
 </div>
 )}

 {/* Period Filter */}
 <div className="flex items-center gap-2">
 <Filter className="h-4 w-4 text-[var(--text-muted)]" />
 {PERIOD_OPTIONS.map((period) => (
 <button
 key={period}
 onClick={() => setActivePeriod(period)}
 className={cn(
"rounded-lg px-3 py-1.5 text-sm transition",
 activePeriod === period
 ?"bg-[var(--muhide-orange)] text-white"
 :"text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]"
 )}
 >
 {period}
 </button>
 ))}
 </div>

 {/* Quota Table */}
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] overflow-hidden">
 <table className="w-full text-sm">
 <thead>
 <tr className="border-b border-[var(--border-default)] bg-[var(--bg-secondary)]">
 <th className="text-right px-4 py-3 text-xs font-medium text-[var(--text-muted)]">Rep</th>
 <th className="text-right px-4 py-3 text-xs font-medium text-[var(--text-muted)]">Target</th>
 <th className="text-right px-4 py-3 text-xs font-medium text-[var(--text-muted)]">Attained</th>
 <th className="text-right px-4 py-3 text-xs font-medium text-[var(--text-muted)] min-w-[180px]">
 Attainment
 </th>
 <th className="text-right px-4 py-3 text-xs font-medium text-[var(--text-muted)]">Forecast</th>
 <th className="text-right px-4 py-3 text-xs font-medium text-[var(--text-muted)]">Status</th>
 </tr>
 </thead>
 <tbody>
 {/* Team Aggregate Row */}
 <tr className="border-b border-[var(--border-default)] bg-[var(--bg-secondary)]/50 font-medium">
 <td className="px-4 py-3 flex items-center gap-2 text-[var(--text-primary)]">
 <Users className="h-4 w-4 text-[var(--text-muted)]" /> Team Total
 </td>
 <td className="px-4 py-3 text-[var(--text-primary)]">
 {data ? formatCurrency(data.team.total_target) :"—"}
 </td>
 <td className="px-4 py-3 text-[var(--status-success-text)]">
 {data ? formatCurrency(data.team.total_attained) :"—"}
 </td>
 <td className="px-4 py-3">
 {data && <AttainmentBar percent={data.team.overall_attainment} />}
 </td>
 <td className="px-4 py-3 text-[var(--text-primary)]">
 {data
 ? formatCurrency(filteredQuotas.reduce((s, q) => s + q.forecast_amount, 0))
 :"—"}
 </td>
 <td className="px-4 py-3">
 {data && (
 <StatusBadge
 status={
 data.team.overall_attainment >= 90
 ?"on_track"
 : data.team.overall_attainment >= 70
 ?"at_risk"
 :"behind"
 }
 />
 )}
 </td>
 </tr>

 {/* Individual Rows */}
 {filteredQuotas.map((quota) => (
 <tr
 key={quota.id}
 className="border-b border-[var(--border-default)] last:border-0 hover:bg-[var(--bg-secondary)]/30 transition"
 >
 <td className="px-4 py-3 text-[var(--text-primary)] font-medium">
 {quota.rep_name}
 </td>
 <td className="px-4 py-3 text-[var(--text-primary)]">
 {formatCurrency(quota.target_amount)}
 </td>
 <td className="px-4 py-3 text-[var(--status-success-text)]">
 {formatCurrency(quota.attained_amount)}
 </td>
 <td className="px-4 py-3">
 <AttainmentBar percent={quota.attainment_percent} />
 </td>
 <td className="px-4 py-3 text-[var(--text-primary)]">
 {formatCurrency(quota.forecast_amount)}
 </td>
 <td className="px-4 py-3">
 <StatusBadge status={quota.status} />
 </td>
 </tr>
 ))}

 {filteredQuotas.length === 0 && (
 <tr>
 <td colSpan={6} className="px-4 py-12 text-center text-sm text-[var(--text-muted)]">
 No quotas found for the selected period.
 </td>
 </tr>
 )}
 </tbody>
 </table>
 </div>
 </div>

 <QuotaModal
 open={modalOpen}
 onClose={() => setModalOpen(false)}
 onSave={(form) => {
 console.log("Saving quota:", form)
 setModalOpen(false)
 }}
 />
 </ErrorBoundary>
 )
}
