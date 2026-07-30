"use client"

import { Card, Badge, Spinner } from"@salesos/ui"
import { HeartPulse, CheckCircle, XCircle, Activity, Clock, Cpu } from"lucide-react"
import type { AdminHealthComponent, AdminHealthHistoryEntry } from"@/lib/api"
import { useTranslation } from "@/lib/i18n"

export interface HealthDashboardViewProps {
 health?: {
 overall_status: string
 uptime_seconds: number
 components: AdminHealthComponent[]
 } | null
 history?: AdminHealthHistoryEntry[] | null
 loading: boolean
}

export function HealthDashboardView({ health, history, loading }: HealthDashboardViewProps) {
 const { t, locale } = useTranslation()

 if (loading) {
 return <div className="py-20 text-center text-[var(--text-muted)]"><Spinner /> {t("common.loading")}</div>
 }

 return (
 <div className="space-y-6">
 <div className="flex items-center justify-between">
 <h2 className="text-xl font-bold">{t("admin.system_health")}</h2>
 {health && (
 <div className="flex items-center gap-2">
 <span className={`h-3 w-3 rounded-full ${health.overall_status ==="healthy" ?"bg-success-500" :"bg-danger-500"}`} />
 <span className="font-medium">{health.overall_status ==="healthy" ?t("admin.health.system_ok") :t("admin.health.issue_detected")}</span>
 </div>
 )}
 </div>

 <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <div className="flex items-center gap-2 mb-2">
 <HeartPulse className="h-5 w-5 text-success-500" />
 </div>
 <p className="text-2xl font-bold">{Math.floor((health?.uptime_seconds || 0) / 86400)}d</p>
 <p className="text-xs text-[var(--text-muted)]">{t("admin.health.uptime")}</p>
 </div>
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <div className="flex items-center gap-2 mb-2">
 <Cpu className="h-5 w-5 text-[var(--muhide-orange)]" />
 </div>
 <p className="text-2xl font-bold">{health?.components?.length || 0}</p>
 <p className="text-xs text-[var(--text-muted)]">{t("admin.health.system_components")}</p>
 </div>
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <div className="flex items-center gap-2 mb-2">
 <CheckCircle className="h-5 w-5 text-success-500" />
 </div>
 <p className="text-2xl font-bold">{health?.components?.filter((c: AdminHealthComponent) => c.status ==="healthy").length || 0}</p>
 <p className="text-xs text-[var(--text-muted)]">{t("admin.health.healthy_count")}</p>
 </div>
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <div className="flex items-center gap-2 mb-2">
 <Activity className="h-5 w-5 text-[var(--text-disabled)]" />
 </div>
 <p className="text-2xl font-bold">{history?.length || 0}</p>
 <p className="text-xs text-[var(--text-muted)]">{t("admin.health.past_checks")}</p>
 </div>
 </div>

 <Card className="p-4">
 <h3 className="font-semibold mb-3">{t("admin.health.component_status")}</h3>
 <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
 {health?.components?.map((comp: AdminHealthComponent) => (
 <div key={comp.component} className="flex items-start gap-3 p-3 rounded-lg border">
 <div className="mt-0.5">
 {comp.status ==="healthy" ? (
 <CheckCircle className="h-5 w-5 text-success-500" />
 ) : (
 <XCircle className="h-5 w-5 text-danger-500" />
 )}
 </div>
 <div className="flex-1">
 <div className="flex items-center justify-between">
 <p className="font-medium text-sm">{comp.component}</p>
 <Badge variant={comp.status ==="healthy" ?"success" :"danger"}>{comp.status}</Badge>
 </div>
 {comp.latency_ms != null && (
 <p className="text-xs text-[var(--text-muted)] mt-1">{t("admin.health.component_latency", { ms: comp.latency_ms })}</p>
 )}
 {comp.details && (
 <p className="text-xs text-[var(--text-disabled)] mt-0.5">{comp.details}</p>
 )}
 </div>
 </div>
 ))}
 </div>
 </Card>

 <Card className="p-4">
 <h3 className="font-semibold mb-3 flex items-center gap-2">
 <Clock className="h-4 w-4" />
 {t("admin.health.history_title")}
 </h3>
 {history?.length ? (
 <div className="space-y-2">
 {history.map((entry: AdminHealthHistoryEntry, i: number) => (
 <div key={i} className="flex items-center gap-3 p-2 rounded-lg border text-sm">
 <span className={`h-2 w-2 rounded-full shrink-0 ${entry.overall_status ==="healthy" ?"bg-success-500" :"bg-danger-500"}`} />
 <span className="text-xs text-[var(--text-muted)] font-mono w-32">
 {new Date(entry.timestamp).toLocaleTimeString(locale === "ar" ?"ar-SA" :"en-US")}
 </span>
 <Badge variant={entry.overall_status ==="healthy" ?"success" :"danger"}>{entry.overall_status}</Badge>
 <div className="flex gap-1 flex-wrap">
 {Object.entries(entry.components).map(([name, status]) => (
 <span key={name} className={`text-xs px-1.5 py-0.5 rounded ${
 status ==="healthy" ?"bg-success-50 text-success-700 dark:bg-success-900/20" :"bg-danger-50 text-danger-700 dark:bg-danger-900/20"
 }`}>
 {name}: {status}
 </span>
 ))}
 </div>
 </div>
 ))}
 </div>
 ) : (
 <p className="text-sm text-[var(--text-muted)] text-center py-4">{t("admin.health.no_history")}</p>
 )}
 </Card>
 </div>
 )
}
