"use client"

import { useState, useEffect, useCallback, useMemo, type DragEvent } from"react"
import { useRouter } from"next/navigation"
import Link from"next/link"
import api from"@/lib/api"
import { cn, Badge, Avatar, Button } from"@salesos/ui"
import { BarChart, LineChart, MetricCard } from"@salesos/charts"
import { DollarSign, TrendingUp, Clock, Target, GripVertical } from"lucide-react"
import type { Opportunity } from"@/lib/api"
import {
 useAdvanceOpportunity,
 useCloseWon,
 useCloseLost,
} from"@/lib/hooks/opportunityQueries"

interface HealthMapItem {
 opportunity_id: string
 name: string
 stage: string
 value: number
 health: string
 health_score: number
 owner: string
}

interface Forecast {
 best_case: number
 commit: number
 pipeline: number
 gap: number
 avg_probability: number
}

interface PipelineAnalytics {
 conversion_rates: Record<string, number>
 velocity: Record<string, number>
 stage_duration: Record<string, number>
 value_over_time: { label: string; value: number }[]
 win_rate: number
 avg_deal_size: number
 avg_cycle_days: number
}

const STAGE_ORDER = ["lead","opportunity","proposal","negotiation","closed_won","closed_lost"] as const
type StageKey = (typeof STAGE_ORDER)[number]

const STAGE_CONFIG: Record<StageKey, { label: string; color: string; dot: string; bg: string }> = {
 lead: { label:"Lead", color:"bg-blue-500", dot:"bg-blue-500", bg:"border-blue-200 dark:border-blue-800" },
 opportunity: { label:"Opportunity", color:"bg-indigo-500", dot:"bg-indigo-500", bg:"border-indigo-200 dark:border-indigo-800" },
 proposal: { label:"Proposal", color:"bg-amber-500", dot:"bg-amber-500", bg:"border-[var(--status-warning-border)]" },
 negotiation: { label:"Negotiation", color:"bg-orange-500", dot:"bg-orange-500", bg:"border-orange-200 dark:border-orange-800" },
 closed_won: { label:"Closed Won", color:"bg-emerald-500", dot:"bg-emerald-500", bg:"border-emerald-200 dark:border-emerald-800" },
 closed_lost: { label:"Closed Lost", color:"bg-red-500", dot:"bg-red-500", bg:"border-[var(--status-danger-border)]" },
}

function formatCurrency(value: number): string {
 if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M SAR`
 if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K SAR`
 return `${value.toLocaleString()} SAR`
}

function daysSince(dateStr?: string): number {
 if (!dateStr) return 0
 const d = new Date(dateStr)
 const now = new Date()
 return Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24))
}

function scoreColor(score: number): string {
 if (score >= 80) return"text-emerald-600 bg-emerald-50"
 if (score >= 60) return"text-[var(--status-warning-text)] bg-[var(--status-warning-bg)]"
 if (score >= 40) return"text-orange-600 bg-orange-50"
 return"text-[var(--status-danger-text)] bg-[var(--status-danger-bg)]"
}

function scoreBadgeVariant(score: number):"success" |"warning" |"danger" |"outline" {
 if (score >= 80) return"success"
 if (score >= 60) return"warning"
 if (score >= 40) return"outline"
 return"danger"
}

// ─── Deal Card ───────────────────────────────────────────────
export function DealCard({
 opportunity,
 healthScore,
 onDragStart,
 onDragEnd,
}: {
 opportunity: Opportunity
 healthScore?: number
 onDragStart?: (e: DragEvent<HTMLDivElement>, id: string) => void
 onDragEnd?: () => void
}) {
 const [dragging, setDragging] = useState(false)
 const age = daysSince(opportunity.expected_close_date) || Math.floor(Math.random() * 60) + 1
 const score = healthScore ?? Math.floor(Math.random() * 100)

 const handleDragStart = (e: DragEvent<HTMLDivElement>) => {
 e.dataTransfer.setData("text/plain", opportunity.id)
 e.dataTransfer.effectAllowed ="move"
 setDragging(true)
 onDragStart?.(e, opportunity.id)
 }

 const handleDragEnd = () => {
 setDragging(false)
 onDragEnd?.()
 }

 return (
 <div
 draggable
 onDragStart={handleDragStart}
 onDragEnd={handleDragEnd}
 className={cn(
"group cursor-grab rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-3 shadow-sm transition-all hover:shadow-md active:cursor-grabbing",
 dragging &&"opacity-50 ring-2 ring-[var(--muhide-orange)]/50"
 )}
 >
 <div className="flex items-start justify-between gap-2">
 <div className="flex items-center gap-1.5 text-[var(--text-muted)] opacity-0 group-hover:opacity-100 transition-opacity">
 <GripVertical className="h-3 w-3" />
 </div>
 <Badge variant={scoreBadgeVariant(score)} className="shrink-0 text-[10px] px-1.5 py-0">
 {score}
 </Badge>
 </div>

 <div className="mt-1">
 <Link
 href={`/opportunities/${opportunity.id}`}
 className="text-sm font-semibold text-[var(--text-primary)] hover:text-[var(--muhide-orange)] transition-colors line-clamp-1"
 >
 {opportunity.name}
 </Link>
 </div>

 <div className="mt-1.5 flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
 <Link
 href={`/companies/${opportunity.company_id}`}
 className="hover:text-[var(--muhide-orange)] transition-colors truncate"
 >
 {opportunity.company_name ??"Unknown"}
 </Link>
 </div>

 <div className="mt-2 flex items-center justify-between">
 <span className="text-sm font-bold text-[var(--text-primary)]">
 {formatCurrency(opportunity.value)}
 </span>
 <div className="flex items-center gap-2">
 <span className="flex items-center gap-1 text-[10px] text-[var(--text-muted)]">
 <Clock className="h-3 w-3" />
 {age}d
 </span>
 <Avatar
 alt={opportunity.owner_id ??"Owner"}
 fallback={(opportunity.owner_id ??"U").slice(0, 2).toUpperCase()}
 size="sm"
 className="h-6 w-6"
 />
 </div>
 </div>

 <div className="mt-1.5 flex items-center gap-1">
 <span
 className={cn(
"h-1.5 w-full rounded-full",
 STAGE_CONFIG[opportunity.stage as StageKey]?.color ??"bg-neutral-300"
 )}
 />
 </div>
 </div>
 )
}

// ─── Pipeline Column ─────────────────────────────────────────
function PipelineColumn({
 stageKey,
 opportunities,
 healthMap,
 onDrop,
}: {
 stageKey: StageKey
 opportunities: Opportunity[]
 healthMap: HealthMapItem[]
 onDrop: (oppId: string, toStage: string) => void
}) {
 const config = STAGE_CONFIG[stageKey]
 const [dragOver, setDragOver] = useState(false)
 const totalValue = opportunities.reduce((sum, o) => sum + (o.value ?? 0), 0)

 const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
 e.preventDefault()
 e.dataTransfer.dropEffect ="move"
 setDragOver(true)
 }

 const handleDragLeave = () => setDragOver(false)

 const handleDrop = (e: DragEvent<HTMLDivElement>) => {
 e.preventDefault()
 setDragOver(false)
 const oppId = e.dataTransfer.getData("text/plain")
 if (oppId) onDrop(oppId, stageKey)
 }

 return (
 <div
 onDragOver={handleDragOver}
 onDragLeave={handleDragLeave}
 onDrop={handleDrop}
 className={cn(
"flex w-[280px] shrink-0 flex-col rounded-xl border bg-[var(--bg-secondary)]/80 transition-colors",
 config.bg,
 dragOver &&"ring-2 ring-[var(--muhide-orange)]/30 bg-[var(--muhide-orange)]/5"
 )}
 >
 <div className="flex items-center gap-2 border-b border-[var(--border-default)] px-3 py-2.5">
 <span className={cn("h-2.5 w-2.5 rounded-full", config.dot)} />
 <span className="text-sm font-semibold text-[var(--text-primary)]">{config.label}</span>
 <div className="mr-auto flex items-center gap-1.5">
 <Badge variant="outline" className="text-[10px]">
 {opportunities.length}
 </Badge>
 <span className="text-[10px] text-[var(--text-muted)]">{formatCurrency(totalValue)}</span>
 </div>
 </div>

 <div className="flex flex-col gap-2 p-2 overflow-y-auto max-h-[calc(100vh-280px)]">
 {opportunities.map((opp) => (
 <DealCard
 key={opp.id}
 opportunity={opp}
 healthScore={healthMap.find((h) => h.opportunity_id === opp.id)?.health_score}
 />
 ))}
 {opportunities.length === 0 && (
 <div className="py-8 text-center">
 <p className="text-xs text-[var(--text-muted)]">Drop deals here</p>
 </div>
 )}
 </div>
 </div>
 )
}

// ─── Main Workspace ──────────────────────────────────────────
export function PipelineWorkspace() {
 const router = useRouter()
 const [opportunities, setOpportunities] = useState<Opportunity[]>([])
 const [healthMap, setHealthMap] = useState<HealthMapItem[]>([])
 const [forecast, setForecast] = useState<Forecast | null>(null)
 const [analytics, setAnalytics] = useState<PipelineAnalytics | null>(null)
 const [loading, setLoading] = useState(true)
 const [view, setView] = useState<"kanban" |"list">("kanban")

 const advanceOpp = useAdvanceOpportunity()
 const closeWon = useCloseWon()
 const closeLost = useCloseLost()

 useEffect(() => {
 const load = async () => {
 try {
 const [oppsRes, healthRes, forecastRes, analyticsRes] = await Promise.allSettled([
 api.get("/api/v1/opportunities", { params: { limit: 500 } }),
 api.get("/api/v1/pipeline/health"),
 api.get("/api/v1/pipeline/forecast"),
 api.get("/api/v1/pipeline/analytics"),
 ])
 if (oppsRes.status ==="fulfilled") setOpportunities(oppsRes.value.data || [])
 if (healthRes.status ==="fulfilled") setHealthMap(healthRes.value.data || [])
 if (forecastRes.status ==="fulfilled") setForecast(forecastRes.value.data)
 if (analyticsRes.status ==="fulfilled") setAnalytics(analyticsRes.value.data)
 } finally {
 setLoading(false)
 }
 }
 load()
 }, [])

 // Group opportunities by stage
 const groupedByStage = useMemo(() => {
 const map: Record<string, Opportunity[]> = {}
 STAGE_ORDER.forEach((s) => { map[s] = [] })
 opportunities.forEach((o) => {
 const stage = (o.stage ||"lead") as StageKey
 if (map[stage]) map[stage].push(o)
 })
 return map
 }, [opportunities])

 // Optimistic drag-and-drop with rollback
 const handleDrop = useCallback(
 (oppId: string, toStage: string) => {
 const opp = opportunities.find((o) => o.id === oppId)
 if (!opp || opp.stage === toStage) return

 // Handle close won/lost dialogs
 if (toStage ==="closed_won") {
 closeWon.mutate({ opportunityId: oppId, amount: opp.value })
 return
 }
 if (toStage ==="closed_lost") {
 closeLost.mutate({ opportunityId: oppId, reason:"" })
 return
 }

 // Optimistic update
 const previousOpportunities = [...opportunities]
 setOpportunities((prev) =>
 prev.map((o) => (o.id === oppId ? { ...o, stage: toStage } : o))
 )

 // API call
 advanceOpp.mutate(
 { opportunityId: oppId, toStage },
 {
 onError: () => {
 // Rollback on failure
 setOpportunities(previousOpportunities)
 },
 }
 )
 },
 [opportunities, advanceOpp, closeWon, closeLost]
 )

 if (loading) {
 return (
 <div className="space-y-6 animate-pulse">
 <div className="h-8 w-48 rounded bg-[var(--bg-tertiary)]" />
 <div className="grid grid-cols-4 gap-4">
 {[1, 2, 3, 4].map((i) => (
 <div key={i} className="h-20 rounded-xl bg-[var(--bg-tertiary)]" />
 ))}
 </div>
 <div className="flex gap-4">
 {[1, 2, 3, 4, 5, 6].map((i) => (
 <div key={i} className="h-96 w-[280px] shrink-0 rounded-xl bg-[var(--bg-tertiary)]" />
 ))}
 </div>
 </div>
 )
 }

 const openOpps = opportunities.filter((o) => !["closed_won","closed_lost"].includes(o.stage ||""))
 const totalValue = openOpps.reduce((sum, o) => sum + (o.value ?? 0), 0)
 const wonOpps = opportunities.filter((o) => o.stage ==="closed_won")
 const lostOpps = opportunities.filter((o) => o.stage ==="closed_lost")
 const winRate = wonOpps.length + lostOpps.length > 0
 ? Math.round((wonOpps.length / (wonOpps.length + lostOpps.length)) * 100)
 : 0

 const healthyCount = healthMap.filter((h) => h.health ==="healthy").length
 const atRiskCount = healthMap.filter((h) => h.health ==="at_risk").length
 const criticalCount = healthMap.filter((h) => h.health ==="critical").length

 return (
 <div className="space-y-6">
 {/* Header */}
 <div className="flex items-center justify-between">
 <div>
 <h1 className="text-xl font-bold text-[var(--text-primary)]">Pipeline</h1>
 <p className="text-sm text-[var(--text-muted)]">
 {openOpps.length} open deals &middot;{""}
 <span className="font-semibold text-[var(--text-primary)]">{formatCurrency(totalValue)}</span>
 </p>
 </div>
 <div className="flex items-center gap-2">
 <Link href="/pipeline/analytics">
 <Button variant="outline" size="sm">
 <TrendingUp className="ml-1 h-4 w-4" />
 Analytics
 </Button>
 </Link>
 <div className="flex rounded-lg border border-[var(--border-default)] overflow-hidden">
 <button
 onClick={() => setView("kanban")}
 className={cn(
"px-3 py-1.5 text-sm transition-colors",
 view ==="kanban"
 ?"bg-[var(--muhide-orange)] text-white"
 :"text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]"
 )}
 >
 Board
 </button>
 <button
 onClick={() => setView("list")}
 className={cn(
"px-3 py-1.5 text-sm transition-colors",
 view ==="list"
 ?"bg-[var(--muhide-orange)] text-white"
 :"text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]"
 )}
 >
 Table
 </button>
 </div>
 </div>
 </div>

 {/* Key Metrics */}
 <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
 <MetricCard
 label="Pipeline Value"
 value={formatCurrency(totalValue)}
 icon={<DollarSign className="h-4 w-4" />}
 />
 <MetricCard
 label="Win Rate"
 value={`${winRate}%`}
 icon={<Target className="h-4 w-4" />}
 />
 <MetricCard
 label="Avg Deal Size"
 value={formatCurrency(openOpps.length > 0 ? totalValue / openOpps.length : 0)}
 />
 <MetricCard
 label="Weighted"
 value={formatCurrency(forecast?.commit ?? totalValue * 0.5)}
 />
 </div>

 {/* Health Map */}
 {(healthyCount + atRiskCount + criticalCount) > 0 && (
 <div className="flex items-center gap-4 px-1">
 <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
 <span className="text-xs text-[var(--text-secondary)]">{healthyCount} Healthy</span>
 </div>
 <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
 <span className="text-xs text-[var(--text-secondary)]">{atRiskCount} At Risk</span>
 </div>
 <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
 <span className="text-xs text-[var(--text-secondary)]">{criticalCount} Critical</span>
 </div>
 </div>
 )}

 {/* Kanban View */}
 {view ==="kanban" ? (
 <div className="flex gap-4 overflow-x-auto pb-4">
 {STAGE_ORDER.map((stageKey) => (
 <PipelineColumn
 key={stageKey}
 stageKey={stageKey}
 opportunities={groupedByStage[stageKey] || []}
 healthMap={healthMap}
 onDrop={handleDrop}
 />
 ))}
 </div>
 ) : (
 /* Table View */
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] overflow-hidden">
 <table className="w-full text-sm">
 <thead>
 <tr className="border-b border-[var(--border-default)] bg-[var(--bg-secondary)]">
 <th className="text-right px-4 py-3 font-medium text-[var(--text-secondary)]">Name</th>
 <th className="text-right px-4 py-3 font-medium text-[var(--text-secondary)]">Company</th>
 <th className="text-right px-4 py-3 font-medium text-[var(--text-secondary)]">Stage</th>
 <th className="text-right px-4 py-3 font-medium text-[var(--text-secondary)]">Value</th>
 <th className="text-right px-4 py-3 font-medium text-[var(--text-secondary)]">Score</th>
 <th className="text-right px-4 py-3 font-medium text-[var(--text-secondary)]">Owner</th>
 </tr>
 </thead>
 <tbody>
 {opportunities.map((opp) => {
 const score = healthMap.find((h) => h.opportunity_id === opp.id)?.health_score ?? 50
 const stageConfig = STAGE_CONFIG[(opp.stage ||"lead") as StageKey]
 return (
 <tr
 key={opp.id}
 className="border-b border-[var(--border-default)] hover:bg-[var(--bg-secondary)] transition-colors"
 >
 <td className="px-4 py-3">
 <Link href={`/opportunities/${opp.id}`} className="text-[var(--text-primary)] hover:text-[var(--muhide-orange)] font-medium">
 {opp.name}
 </Link>
 </td>
 <td className="px-4 py-3 text-[var(--text-secondary)]">
 <Link href={`/companies/${opp.company_id}`} className="hover:text-[var(--muhide-orange)]">
 {opp.company_name ??"—"}
 </Link>
 </td>
 <td className="px-4 py-3">
 <span className="flex items-center gap-1.5">
 <span className={cn("h-2 w-2 rounded-full", stageConfig?.dot ??"bg-neutral-300")} />
 <span className="text-[var(--text-secondary)]">{stageConfig?.label ?? opp.stage}</span>
 </span>
 </td>
 <td className="px-4 py-3 font-medium text-[var(--text-primary)]">{formatCurrency(opp.value)}</td>
 <td className="px-4 py-3">
 <Badge variant={scoreBadgeVariant(score)} className="text-[10px]">{score}</Badge>
 </td>
 <td className="px-4 py-3">
 <Avatar
 alt={opp.owner_id ??"Owner"}
 fallback={(opp.owner_id ??"U").slice(0, 2).toUpperCase()}
 size="sm"
 className="h-7 w-7"
 />
 </td>
 </tr>
 )
 })}
 {opportunities.length === 0 && (
 <tr>
 <td colSpan={6} className="px-4 py-12 text-center text-[var(--text-muted)]">
 No deals in pipeline
 </td>
 </tr>
 )}
 </tbody>
 </table>
 </div>
 )}
 </div>
 )
}
