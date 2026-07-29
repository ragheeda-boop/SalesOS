"use client"

import { useState, useEffect, useCallback } from"react"
import api from"@/lib/api"
import { cn } from"@salesos/ui"
import { useTranslation } from"@/lib/i18n"
import { ErrorBoundary } from"@/components/error-boundary"
import {
 Globe,
 MapPin,
 Users,
 AlertTriangle,
 RefreshCw,
 ArrowLeftRight,
 X,
 Filter,
 BarChart3,
} from"lucide-react"

interface TerritoryAccount {
 id: string
 name: string
 value: number
 status:"assigned" |"unassigned"
 rep_name?: string
}

interface Territory {
 id: string
 name: string
 rep_name: string
 rep_id: string
 account_count: number
 total_value: number
 accounts: TerritoryAccount[]
}

interface CoverageGap {
 region: string
 unassigned_accounts: number
 potential_value: number
 reason: string
}

interface TerritoryData {
 territories: Territory[]
 gaps: CoverageGap[]
 total_accounts: number
 unassigned_accounts: number
}

interface RebalanceSuggestion {
 from_territory: string
 to_territory: string
 account_name: string
 reason: string
}

function formatCurrency(value: number): string {
 if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M SAR`
 if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K SAR`
 return `${value.toLocaleString()} SAR`
}

function CoverageIndicator({ assigned, total }: { assigned: number; total: number }) {
 const percent = total > 0 ? (assigned / total) * 100 : 0
 return (
 <div className="flex items-center gap-2">
 <div className="h-2 flex-1 rounded-full bg-[var(--bg-tertiary)] overflow-hidden">
 <div
 className={cn(
"h-full rounded-full transition-all",
 percent >= 90 ?"bg-green-500" : percent >= 70 ?"bg-amber-500" :"bg-red-500"
 )}
 style={{ width: `${percent}%` }}
 />
 </div>
 <span className="text-xs text-[var(--text-muted)]">
 {assigned}/{total}
 </span>
 </div>
 )
}

function AssignModal({
 open,
 onClose,
 territories,
 accountName,
}: {
 open: boolean
 onClose: () => void
 territories: Territory[]
 accountName: string
}) {
 const [selectedRep, setSelectedRep] = useState("")

 if (!open) return null

 return (
 <div className="fixed inset-0 z-50 flex items-center justify-center">
 <div className="absolute inset-0 bg-black/50" onClick={onClose} />
 <div className="relative bg-[var(--bg-primary)] rounded-xl border border-[var(--border-default)] shadow-xl w-full max-w-md p-6 space-y-4">
 <div className="flex items-center justify-between">
 <h2 className="text-lg font-semibold text-[var(--text-primary)]">
 Assign Account: {accountName}
 </h2>
 <button onClick={onClose} className="rounded-lg p-1 hover:bg-[var(--bg-secondary)]">
 <X className="h-5 w-5 text-[var(--text-muted)]" />
 </button>
 </div>
 <div>
 <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
 Select Rep / Territory
 </label>
 <select
 value={selectedRep}
 onChange={(e) => setSelectedRep(e.target.value)}
 className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)]"
 >
 <option value="">Choose a rep...</option>
 {territories.map((t) => (
 <option key={t.id} value={t.rep_id}>
 {t.rep_name} ({t.name})
 </option>
 ))}
 </select>
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
 if (selectedRep) {
 console.log("Assigning account to:", selectedRep)
 onClose()
 }
 }}
 disabled={!selectedRep}
 className="rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-sm text-white hover:opacity-90 transition disabled:opacity-50"
 >
 Assign
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
 <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
 {[1, 2, 3].map((i) => (
 <div key={i} className="h-24 rounded-xl bg-[var(--bg-tertiary)]" />
 ))}
 </div>
 <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
 {[1, 2, 3, 4].map((i) => (
 <div key={i} className="h-48 rounded-xl bg-[var(--bg-tertiary)]" />
 ))}
 </div>
 </div>
 )
}

export default function TerritoryMapPage() {
 const { t } = useTranslation()
 const [data, setData] = useState<TerritoryData | null>(null)
 const [loading, setLoading] = useState(true)
 const [error, setError] = useState<string | null>(null)
 const [assignModalOpen, setAssignModalOpen] = useState(false)
 const [selectedAccount, setSelectedAccount] = useState<string>("")
 const [rebalanceSuggestions, setRebalanceSuggestions] = useState<RebalanceSuggestion[]>([])

 const fetchTerritories = useCallback(async () => {
 setLoading(true)
 setError(null)
 try {
 const [workspaceRes, decisionRes] = await Promise.all([
 api.get("/api/v1/workspace").catch(() => ({ data: null })),
 api.get("/api/v1/decision/evaluate?target_type=territory").catch(() => ({ data: null })),
 ])

 const workspace = workspaceRes.data

 // Honest empty / pipeline-derived — never invent Aramco/SABIC demo territories
 const recent = (workspace?.opportunities?.recent || []) as Array<{
  id: string
  name: string
  value: number
  company_id?: string
 }>
 const territories: Territory[] = recent.length
  ? [
     {
      id: "pipeline",
      name: "Open pipeline",
      rep_name: "Unassigned",
      rep_id: "none",
      account_count: recent.length,
      total_value: recent.reduce((s, o) => s + (Number(o.value) || 0), 0),
      accounts: recent.map((o) => ({
       id: o.company_id || o.id,
       name: o.name || "Opportunity",
       value: Number(o.value) || 0,
       status: "assigned" as const,
       rep_name: "Unassigned",
      })),
     },
    ]
  : []

 const allAccounts = territories.flatMap((t) => t.accounts)
 const gaps: CoverageGap[] = []

 setData({
 territories,
 gaps,
 total_accounts: allAccounts.length,
 unassigned_accounts: allAccounts.length,
 })

 setRebalanceSuggestions([])
 void decisionRes
 } catch {
 setError(t("error.server_error"))
 } finally {
 setLoading(false)
 }
 }, [t])

 useEffect(() => {
 fetchTerritories()
 }, [fetchTerritories])

 if (loading) return <LoadingSkeleton />

 if (error) {
 return (
 <div className="flex flex-col items-center justify-center py-20 text-center">
 <AlertTriangle className="h-12 w-12 text-[var(--status-danger-text)] mb-4" />
 <h3 className="text-lg font-semibold text-[var(--text-primary)]">Error Loading Territories</h3>
 <p className="text-sm text-[var(--status-danger-text)] mt-1">{error}</p>
 <button
 onClick={fetchTerritories}
 className="mt-4 flex items-center gap-2 rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-sm text-white hover:opacity-90"
 >
 <RefreshCw className="h-4 w-4" /> Retry
 </button>
 </div>
 )
 }

 return (
 <ErrorBoundary>
 <div className="space-y-6">
 {/* Header */}
 <div className="flex items-center justify-between">
 <div>
 <h1 className="text-xl font-bold text-[var(--text-primary)]">Territory Map</h1>
 <p className="text-sm text-[var(--text-muted)]">
 Account assignment, coverage gaps, and load balancing
 </p>
 </div>
 <button
 onClick={fetchTerritories}
 className="flex items-center gap-2 rounded-lg border border-[var(--border-default)] px-3 py-2 text-sm text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] transition"
 >
 <RefreshCw className="h-4 w-4" /> Refresh
 </button>
 </div>

 {/* Summary Cards */}
 {data && (
 <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <div className="flex items-center gap-2">
 <Globe className="h-4 w-4 text-[var(--muhide-orange)]" />
 <p className="text-xs text-[var(--text-muted)]">Territories</p>
 </div>
 <p className="text-2xl font-bold text-[var(--text-primary)] mt-1">
 {data.territories.length}
 </p>
 <p className="text-xs text-[var(--text-muted)] mt-1">
 {formatCurrency(data.territories.reduce((s, t) => s + t.total_value, 0))} total value
 </p>
 </div>
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <div className="flex items-center gap-2">
 <Users className="h-4 w-4 text-[var(--status-success-text)]" />
 <p className="text-xs text-[var(--text-muted)]">Total Accounts</p>
 </div>
 <p className="text-2xl font-bold text-[var(--text-primary)] mt-1">{data.total_accounts}</p>
 <CoverageIndicator
 assigned={data.total_accounts - data.unassigned_accounts}
 total={data.total_accounts}
 />
 </div>
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <div className="flex items-center gap-2">
 <AlertTriangle className="h-4 w-4 text-[var(--status-warning-text)]" />
 <p className="text-xs text-[var(--text-muted)]">Unassigned</p>
 </div>
 <p className="text-2xl font-bold text-[var(--status-warning-text)] mt-1">{data.unassigned_accounts}</p>
 <p className="text-xs text-[var(--text-muted)] mt-1">
 {formatCurrency(data.gaps.reduce((s, g) => s + g.potential_value, 0))} at risk
 </p>
 </div>
 </div>
 )}

 {/* Territory Cards */}
 {data && (
 <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
 {data.territories.map((territory) => (
 <div
 key={territory.id}
 className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4 space-y-3"
 >
 {/* Territory Header */}
 <div className="flex items-center justify-between">
 <div className="flex items-center gap-2">
 <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--muhide-orange)]/10">
 <MapPin className="h-4 w-4 text-[var(--muhide-orange)]" />
 </div>
 <div>
 <h3 className="text-sm font-semibold text-[var(--text-primary)]">
 {territory.name}
 </h3>
 <p className="text-xs text-[var(--text-muted)]">{territory.rep_name}</p>
 </div>
 </div>
 <div className="text-right">
 <p className="text-sm font-bold text-[var(--text-primary)]">
 {formatCurrency(territory.total_value)}
 </p>
 <p className="text-xs text-[var(--text-muted)]">
 {territory.account_count} accounts
 </p>
 </div>
 </div>

 {/* Account List */}
 <div className="space-y-1.5">
 {territory.accounts.map((account) => (
 <div
 key={account.id}
 className="flex items-center justify-between rounded-lg px-3 py-2 hover:bg-[var(--bg-secondary)] transition"
 >
 <div className="flex items-center gap-2">
 <BarChart3 className="h-3.5 w-3.5 text-[var(--text-muted)]" />
 <span className="text-sm text-[var(--text-primary)]">{account.name}</span>
 </div>
 <div className="flex items-center gap-2">
 <span className="text-xs text-[var(--text-muted)]">
 {formatCurrency(account.value)}
 </span>
 <button
 onClick={() => {
 setSelectedAccount(account.name)
 setAssignModalOpen(true)
 }}
 className="rounded p-1 hover:bg-[var(--bg-tertiary)] transition text-[var(--text-muted)]"
 title="Reassign"
 >
 <ArrowLeftRight className="h-3.5 w-3.5" />
 </button>
 </div>
 </div>
 ))}
 </div>
 </div>
 ))}
 </div>
 )}

 {/* Coverage Gaps */}
 {data && data.gaps.length > 0 && (
 <div className="rounded-xl border border-[var(--status-warning-border)] bg-[var(--status-warning-bg)]/50 p-4 space-y-3">
 <div className="flex items-center gap-2">
 <AlertTriangle className="h-4 w-4 text-[var(--status-warning-text)]" />
 <h3 className="text-sm font-semibold text-[var(--text-primary)]">Coverage Gaps</h3>
 </div>
 <div className="space-y-2">
 {data.gaps.map((gap, i) => (
 <div
 key={i}
 className="flex items-center justify-between rounded-lg bg-[var(--bg-primary)]/50/50 px-3 py-2"
 >
 <div>
 <p className="text-sm font-medium text-[var(--text-primary)]">{gap.region}</p>
 <p className="text-xs text-[var(--text-muted)]">{gap.reason}</p>
 </div>
 <div className="text-right">
 <p className="text-sm font-medium text-[var(--status-warning-text)]">
 {gap.unassigned_accounts} unassigned
 </p>
 <p className="text-xs text-[var(--text-muted)]">
 {formatCurrency(gap.potential_value)}
 </p>
 </div>
 </div>
 ))}
 </div>
 </div>
 )}

 {/* Rebalance Suggestions */}
 {rebalanceSuggestions.length > 0 && (
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4 space-y-3">
 <div className="flex items-center justify-between">
 <div className="flex items-center gap-2">
 <ArrowLeftRight className="h-4 w-4 text-[var(--muhide-orange)]" />
 <h3 className="text-sm font-semibold text-[var(--text-primary)]">
 Load Balancing Suggestions
 </h3>
 </div>
 <button className="flex items-center gap-2 rounded-lg bg-[var(--muhide-orange)] px-3 py-1.5 text-xs text-white hover:opacity-90 transition">
 <ArrowLeftRight className="h-3 w-3" /> Rebalance
 </button>
 </div>
 <div className="space-y-2">
 {rebalanceSuggestions.map((suggestion, i) => (
 <div
 key={i}
 className="flex items-center gap-3 rounded-lg bg-[var(--bg-secondary)] px-3 py-2"
 >
 <ArrowLeftRight className="h-4 w-4 text-[var(--text-muted)] shrink-0" />
 <div className="flex-1 min-w-0">
 <p className="text-sm text-[var(--text-primary)]">
 <span className="font-medium">{suggestion.account_name}</span>
 {" →"}
 <span className="text-[var(--muhide-orange)]">{suggestion.to_territory}</span>
 </p>
 <p className="text-xs text-[var(--text-muted)]">{suggestion.reason}</p>
 </div>
 </div>
 ))}
 </div>
 </div>
 )}
 </div>

 <AssignModal
 open={assignModalOpen}
 onClose={() => setAssignModalOpen(false)}
 territories={data?.territories ?? []}
 accountName={selectedAccount}
 />
 </ErrorBoundary>
 )
}
