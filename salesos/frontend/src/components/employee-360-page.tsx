"use client"

import { useState, useCallback, useMemo, useRef, useEffect } from "react"
import { useEmployee360, useEmployeeSignals, useEmployeeScore, useEmployeeTimeline, useEmployeePerformance } from "@/lib/hooks/employeeQueries"
import {
  Tabs, TabsList, Tab, TabsPanel,
  Skeleton, EmptyState, Badge, Avatar, Card, CardContent, CardHeader, Button, cn,
} from "@salesos/ui"
import {
  User, Activity, Brain, Clock, TrendingUp, Mail, Phone,
  AlertTriangle, TrendingDown, Minus, ChevronDown, Filter, X,
  Calendar, BarChart3, CheckCircle, Users, Shield, Target,
} from "lucide-react"
import { ErrorFallback } from "@/components/foundation/error-boundary"
import { useTranslation } from "@/lib/i18n"
import { useDecisionScores } from "@/lib/decisionQueries"
import api from "@/lib/api"
import type { EmployeeTimelineParams } from "@/lib/api"
import type { Score } from "@salesos/decision-platform"

type TabId = "overview" | "signals" | "scoring" | "timeline" | "performance"

const TABS: { id: TabId; labelKey: string; icon: typeof Activity }[] = [
  { id: "overview", labelKey: "emp360.tabs.overview", icon: User },
  { id: "signals", labelKey: "emp360.tabs.signals", icon: Activity },
  { id: "scoring", labelKey: "emp360.tabs.scoring", icon: Brain },
  { id: "timeline", labelKey: "emp360.tabs.timeline", icon: Clock },
  { id: "performance", labelKey: "emp360.tabs.performance", icon: TrendingUp },
]

const SOURCE_OPTIONS = ["crm", "timeline", "workflow", "email", "calendar", "manual"]
const TYPE_OPTIONS = ["email_sent", "email_received", "meeting_created", "meeting_completed", "call", "task_created", "task_completed", "note_added", "contract_signed"]

const actionConfig: Record<string, { icon: typeof Mail; color: string }> = {
  email_sent: { icon: Mail, color: "text-info-600 bg-info-100 dark:text-info-400 dark:bg-info-900/50" },
  email_received: { icon: Mail, color: "text-info-600 bg-info-100 dark:text-info-400 dark:bg-info-900/50" },
  meeting_created: { icon: Calendar, color: "text-info-600 bg-info-100 dark:text-info-400 dark:bg-info-900/50" },
  meeting_completed: { icon: Calendar, color: "text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/50" },
  call: { icon: Phone, color: "text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/50" },
  task_created: { icon: CheckCircle, color: "text-warning-600 bg-warning-100 dark:text-warning-400 dark:bg-warning-900/50" },
  task_completed: { icon: CheckCircle, color: "text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/50" },
  note_added: { icon: Mail, color: "text-neutral-600 bg-neutral-100 dark:text-neutral-400 dark:bg-neutral-800" },
  contract_signed: { icon: CheckCircle, color: "text-purple-600 bg-purple-100 dark:text-purple-400 dark:bg-purple-900/50" },
}

function formatRelativeTime(timestamp: string): string {
  const diff = Date.now() - new Date(timestamp).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return "Just now"
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}d ago`
  return new Date(timestamp).toLocaleDateString("en-US", { month: "short", day: "numeric" })
}

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null || score === undefined) return <span className="text-neutral-400">-</span>
  const color = score >= 70 ? "bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400" :
    score >= 40 ? "bg-warning-100 text-warning-700 dark:bg-warning-900/30 dark:text-warning-400" :
    "bg-danger-100 text-danger-700 dark:bg-danger-900/30 dark:text-danger-400"
  return (
    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold ${color}`}>
      {score}
    </span>
  )
}

function StatBox({ icon: Icon, label, value, color }: { icon: React.ElementType; label: string; value: React.ReactNode; color: string }) {
  return (
    <div className={cn("flex items-center gap-3 rounded-xl p-3", color)}>
      <Icon className="h-5 w-5 shrink-0" />
      <div>
        <p className="text-[10px] opacity-70">{label}</p>
        <p className="text-lg font-bold">{value}</p>
      </div>
    </div>
  )
}

function OverviewSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-40" />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}
      </div>
      <Skeleton className="h-48" />
    </div>
  )
}

function ProfileCard({ data, t }: { data: NonNullable<ReturnType<typeof useEmployee360>["data"]>; t: (k: string, vars?: Record<string, string | number>) => string }) {
  const initials = data.profile.full_name.split(" ").map((n: string) => n[0]).join("").slice(0, 2).toUpperCase()

  return (
    <div className="overflow-hidden rounded-xl border border-neutral-200 bg-white shadow-muhide-1 dark:border-neutral-700 dark:bg-neutral-900">
      <div className="h-20 bg-gradient-to-l from-info-600 via-purple-600 to-[var(--muhide-orange)]" />
      <div className="relative px-6 pb-5 pt-0">
        <div className="flex flex-wrap items-end gap-4 -mt-10">
          <Avatar
            src={data.profile.avatar_url || undefined}
            alt={data.profile.full_name}
            fallback={initials}
            size="lg"
            className="h-20 w-20 text-xl border-4 border-white shadow-muhide-3 dark:border-neutral-900"
          />
          <div className="flex-1 pt-2">
            <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
              {data.profile.full_name_ar || data.profile.full_name}
            </h1>
            <p className="text-sm text-neutral-500 dark:text-neutral-400">
              {data.profile.role}
              {data.profile.email && <span className="ms-2">· {data.profile.email}</span>}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={data.profile.is_active ? "success" : "default"}>
              {data.profile.is_active ? t("status.active") : t("status.inactive")}
            </Badge>
            {data.profile.phone && (
              <a href={`tel:${data.profile.phone}`} className="inline-flex items-center gap-1 rounded-lg border border-neutral-200 px-2 py-1 text-xs text-neutral-600 hover:bg-neutral-50 dark:border-neutral-700 dark:text-neutral-400 dark:hover:bg-neutral-800">
                <Phone className="h-3 w-3" /> {t("employee.call")}
              </a>
            )}
            {data.profile.email && (
              <a href={`mailto:${data.profile.email}`} className="inline-flex items-center gap-1 rounded-lg border border-neutral-200 px-2 py-1 text-xs text-neutral-600 hover:bg-neutral-50 dark:border-neutral-700 dark:text-neutral-400 dark:hover:bg-neutral-800">
                <Mail className="h-3 w-3" /> {t("employee.email_short")}
              </a>
            )}
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-4 border-t border-neutral-100 pt-4 dark:border-neutral-700">
          {data.profile.manager && (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-neutral-500">{t("employee.manager")}</span>
              <span className="font-medium text-neutral-900 dark:text-neutral-100">
                {String(data.profile.manager.full_name || data.profile.manager.name || t("employee.unknown"))}
              </span>
            </div>
          )}
          {data.profile.team.length > 0 && (
            <div className="flex items-center gap-2">
              <Users className="h-3.5 w-3.5 text-neutral-400" />
              <span className="text-xs text-neutral-500">{t("employee.team", { count: data.profile.team.length })}</span>
              <div className="flex -space-x-2">
                {data.profile.team.slice(0, 5).map((member: Record<string, unknown>, i: number) => (
                  <span key={i} title={String(member.full_name || member.name)}>
                    <Avatar
                      size="sm"
                      fallback={String(member.full_name || member.name || "").split(" ").map((n: string) => n[0]).join("").slice(0, 2).toUpperCase()}
                      className="h-6 w-6 border-2 border-white text-[8px] dark:border-neutral-900"
                    />
                  </span>
                ))}
                {data.profile.team.length > 5 && (
                  <div className="flex h-6 w-6 items-center justify-center rounded-full border-2 border-white bg-neutral-200 text-[8px] font-bold text-neutral-600 dark:border-neutral-900 dark:bg-neutral-700 dark:text-neutral-300">
                    +{data.profile.team.length - 5}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function QuickStatsRow({ data, signals, scoreData }: {
  data: NonNullable<ReturnType<typeof useEmployee360>["data"]>
  signals: ReturnType<typeof useEmployeeSignals>["data"]
  scoreData: ReturnType<typeof useEmployeeScore>["data"]
}) {
  const { t } = useTranslation()
  const riskLevel = scoreData && scoreData.score < 40 ? "high" : scoreData && scoreData.score < 70 ? "medium" : "low"
  const riskColor = riskLevel === "high" ? "text-danger-600" : riskLevel === "medium" ? "text-warning-600" : "text-success-600"
  const riskLabel = riskLevel === "high" ? t("emp360.risk.high") : riskLevel === "medium" ? t("emp360.risk.medium") : t("emp360.risk.low")

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      <StatBox icon={Activity} label={t("emp360.total_signals")} value={signals?.total ?? 0} color="bg-info-50 text-info-700 dark:bg-info-900/20 dark:text-info-400" />
      <StatBox icon={Brain} label={t("emp360.current_score")} value={scoreData?.score ?? "-"} color="bg-purple-50 text-purple-700 dark:bg-purple-900/20 dark:text-purple-400" />
      <StatBox icon={Shield} label={t("emp360.risk_level")} value={<span className={riskColor}>{riskLabel}</span>} color={riskLevel === "high" ? "bg-danger-50 text-danger-700 dark:bg-danger-900/20 dark:text-danger-400" : riskLevel === "medium" ? "bg-warning-50 text-warning-700 dark:bg-warning-900/20 dark:text-warning-400" : "bg-success-50 text-success-700 dark:bg-success-900/20 dark:text-success-400"} />
      <StatBox icon={Clock} label={t("emp360.tenure")} value={new Date(data.profile.created_at).toLocaleDateString("en-US", { month: "short", year: "numeric" })} color="bg-neutral-50 text-neutral-700 dark:bg-neutral-800/50 dark:text-neutral-400" />
    </div>
  )
}

function RecentActivityFeed({ employeeId }: { employeeId: string }) {
  const { t } = useTranslation()
  const { data, isLoading } = useEmployeeTimeline(employeeId, { page_size: 5 })

  if (isLoading) {
    return (
      <Card>
        <CardHeader><h3 className="text-sm font-semibold">{t("emp360.recent_activity")}</h3></CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex gap-3 animate-pulse">
                <div className="h-8 w-8 rounded-full bg-neutral-200 dark:bg-neutral-700" />
                <div className="flex-1 space-y-1.5">
                  <div className="h-3 w-3/4 rounded bg-neutral-200 dark:bg-neutral-700" />
                  <div className="h-2 w-1/2 rounded bg-neutral-200 dark:bg-neutral-700" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  const events = data?.events || []

  if (events.length === 0) {
    return (
      <Card>
        <CardHeader><h3 className="text-sm font-semibold">{t("emp360.recent_activity")}</h3></CardHeader>
        <CardContent>
          <EmptyState icon={<Clock className="h-8 w-8" />} title={t("emp360.no_activity")} />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader><h3 className="text-sm font-semibold">{t("emp360.recent_activity")}</h3></CardHeader>
      <CardContent>
        <div className="space-y-0">
          {events.map((event, idx) => {
            const config = actionConfig[event.action] || { icon: Clock, color: "text-neutral-600 bg-neutral-100" }
            const Icon = config.icon
            return (
              <div key={event.id} className="relative flex gap-3 pb-4 last:pb-0">
                {idx < events.length - 1 && (
                  <div className="absolute right-[15px] top-10 bottom-0 w-px bg-neutral-200 dark:bg-neutral-700" />
                )}
                <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-full", config.color)}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">{event.title}</p>
                  <p className="mt-0.5 text-xs text-neutral-500 dark:text-neutral-400">
                    <span className="inline-flex items-center gap-1">
                      <Badge variant="default" className="text-[10px]">{event.source_label}</Badge>
                    </span>
                    <span className="mx-1.5">·</span>
                    {formatRelativeTime(event.timestamp)}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

function OverviewTab({ employeeId, data }: { employeeId: string; data: NonNullable<ReturnType<typeof useEmployee360>["data"]> }) {
  const { t } = useTranslation()
  const { data: signals, isLoading: signalsLoading } = useEmployeeSignals(employeeId)
  const { data: scoreData, isLoading: scoreLoading } = useEmployeeScore(employeeId)

  if (signalsLoading || scoreLoading) return <OverviewSkeleton />

  return (
    <div className="space-y-4">
      <ProfileCard data={data} t={t} />
      <QuickStatsRow data={data} signals={signals} scoreData={scoreData} />
      <RecentActivityFeed employeeId={employeeId} />
    </div>
  )
}

function SignalsTab({ employeeId }: { employeeId: string }) {
  const { t } = useTranslation()
  const { data: signals, isLoading, isError, error, refetch } = useEmployeeSignals(employeeId)

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-48 rounded-xl" />)}
      </div>
    )
  }

  if (isError) {
    return (
      <div className="py-12">
        <ErrorFallback title={t("emp360.signals_error")} message={(error as Error)?.message} onRetry={() => refetch()} />
      </div>
    )
  }

  if (!signals || signals.total === 0) {
    return (
      <div className="py-12">
        <EmptyState icon={<Activity className="h-10 w-10" />} title={t("emp360.no_signals")} description={t("emp360.no_signals_hint")} />
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-info-600" />
            <h3 className="text-sm font-semibold">{t("emp360.signals_by_type")}</h3>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {signals.by_type.map((s) => (
              <div key={s.type} className="flex items-center justify-between">
                <span className="text-sm text-neutral-700 dark:text-neutral-300">{s.label}</span>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-24 overflow-hidden rounded-full bg-neutral-100 dark:bg-neutral-800">
                    <div className="h-full rounded-full bg-info-500" style={{ width: `${Math.min(100, (s.count / signals.total) * 100)}%` }} />
                  </div>
                  <span className="text-xs font-medium text-neutral-900 dark:text-neutral-100 w-6 text-right">{s.count}</span>
                </div>
              </div>
            ))}
            {signals.by_type.length === 0 && <p className="text-xs text-neutral-400">{t("emp360.no_data")}</p>}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-purple-600" />
            <h3 className="text-sm font-semibold">{t("emp360.signals_by_source")}</h3>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {signals.by_source.map((s) => (
              <div key={s.source} className="flex items-center justify-between">
                <span className="text-sm text-neutral-700 dark:text-neutral-300">{s.label}</span>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-24 overflow-hidden rounded-full bg-neutral-100 dark:bg-neutral-800">
                    <div className="h-full rounded-full bg-purple-500" style={{ width: `${Math.min(100, (s.count / signals.total) * 100)}%` }} />
                  </div>
                  <span className="text-xs font-medium text-neutral-900 dark:text-neutral-100 w-6 text-right">{s.count}</span>
                </div>
              </div>
            ))}
            {signals.by_source.length === 0 && <p className="text-xs text-neutral-400">{t("emp360.no_data")}</p>}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-success-600" />
            <h3 className="text-sm font-semibold">{t("emp360.signals_trend")}</h3>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {signals.trend.map((p) => (
              <div key={p.date} className="flex items-center justify-between text-xs">
                <span className="text-neutral-500">{p.date}</span>
                <div className="flex items-center gap-1">
                  <div className="h-2 rounded-full bg-[var(--muhide-orange)]" style={{ width: `${Math.min(60, p.count * 6)}px` }} />
                  <span className="font-medium text-neutral-700 dark:text-neutral-300 w-6 text-right">{p.count}</span>
                </div>
              </div>
            ))}
            {signals.trend.length === 0 && <p className="text-xs text-neutral-400">{t("emp360.no_data")}</p>}
          </div>
          <p className="mt-3 text-center text-[10px] text-neutral-400">{t("emp360.signals_total", { count: signals.total })}</p>
        </CardContent>
      </Card>
    </div>
  )
}

function ScoringTab({ employeeId }: { employeeId: string }) {
  const { t } = useTranslation()
  const { data: decisionScores, isLoading: dpLoading } = useDecisionScores(employeeId, 'employee')
  const { data: scoreData, isLoading: domainLoading, isError, error, refetch } = useEmployeeScore(employeeId)

  const isLoading = dpLoading && domainLoading

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Skeleton className="h-48 rounded-xl" />
        <Skeleton className="h-48 rounded-xl md:col-span-2" />
      </div>
    )
  }

  if (isError && (!decisionScores || decisionScores.length === 0)) {
    return (
      <div className="py-12">
        <ErrorFallback title={t("emp360.score_error")} message={(error as Error)?.message} onRetry={() => refetch()} />
      </div>
    )
  }

  const hasDpScores = decisionScores && decisionScores.length > 0
  const hasDomainScore = scoreData !== null && scoreData !== undefined

  if (!hasDpScores && !hasDomainScore) {
    return (
      <div className="py-12">
        <EmptyState icon={<Brain className="h-10 w-10" />} title={t("emp360.no_score")} description={t("emp360.no_score_hint")} />
      </div>
    )
  }

  const gaugeScore = hasDomainScore ? scoreData.score : Math.round(decisionScores!.reduce((sum: number, s: Score) => sum + (typeof s.value === 'number' ? s.value : 0), 0) / decisionScores!.length * 100)
  const gaugeColor = gaugeScore >= 70 ? "stroke-success-500" : gaugeScore >= 40 ? "stroke-warning-500" : "stroke-danger-500"
  const trendIcon = hasDomainScore ? (
    scoreData.trend === "up" ? <TrendingUp className="h-4 w-4 text-success-500" /> :
    scoreData.trend === "down" ? <TrendingDown className="h-4 w-4 text-danger-500" /> :
    <Minus className="h-4 w-4 text-neutral-400" />
  ) : <Minus className="h-4 w-4 text-neutral-400" />

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      <Card className="flex flex-col items-center justify-center">
        <CardContent className="py-6">
          <div className="relative mb-3">
            <svg className="h-28 w-28 -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" strokeWidth="8" className="text-neutral-100 dark:text-neutral-800" />
              <circle cx="50" cy="50" r="42" fill="none" strokeWidth="8" strokeLinecap="round" className={gaugeColor} strokeDasharray={`${(gaugeScore / 100) * 263.9} 263.9`} />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">{gaugeScore}</span>
              <span className="text-[10px] text-neutral-500">{t("emp360.out_of_100")}</span>
            </div>
          </div>
          {hasDomainScore && (
            <>
              <div className="flex items-center justify-center gap-1.5 text-sm">
                <span className="text-neutral-500">{t("emp360.trend")}:</span>
                {trendIcon}
                <span className="text-xs text-neutral-400 capitalize">{scoreData.trend}</span>
              </div>
              <div className="mt-4 flex items-center gap-2 text-xs">
                <span className="text-neutral-500">{t("emp360.confidence")}:</span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-neutral-100 dark:bg-neutral-800">
                  <div className="h-full rounded-full bg-info-500" style={{ width: `${scoreData.confidence}%` }} />
                </div>
                <span className="font-medium text-neutral-700 dark:text-neutral-300">{Math.round(scoreData.confidence)}%</span>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card className="md:col-span-2">
        <CardHeader>
          <div className="flex items-center gap-2">
            {hasDpScores ? (
              <>
                <Brain className="h-4 w-4 text-purple-500" />
                <h3 className="text-sm font-semibold">{t("emp360.factors")}</h3>
                <Badge variant="primary" className="text-[10px]">Decision Platform</Badge>
              </>
            ) : (
              <>
                <BarChart3 className="h-4 w-4 text-neutral-500" />
                <h3 className="text-sm font-semibold">{t("emp360.factors")}</h3>
              </>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {hasDpScores ? (
              decisionScores.slice(0, 6).map((s: Score, i: number) => (
                <div key={s.name || String(i)}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-neutral-700 dark:text-neutral-300">{s.label || s.name}</span>
                    <span className="font-medium text-neutral-900 dark:text-neutral-100">{Math.round((typeof s.value === 'number' ? s.value : 0) * 100)}%</span>
                  </div>
                  <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-neutral-100 dark:bg-neutral-800">
                    <div className="h-full rounded-full bg-[var(--muhide-orange)]" style={{ width: `${Math.min(100, (typeof s.value === 'number' ? s.value : 0) * 100)}%` }} />
                  </div>
                </div>
              ))
            ) : hasDomainScore ? (
              scoreData.factors.map((f) => (
                <div key={f.name}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-neutral-700 dark:text-neutral-300">{f.label}</span>
                    <span className="font-medium text-neutral-900 dark:text-neutral-100">+{f.contribution}</span>
                  </div>
                  <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-neutral-100 dark:bg-neutral-800">
                    <div className="h-full rounded-full bg-[var(--muhide-orange)]" style={{ width: `${Math.min(100, f.contribution * 5)}%` }} />
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs text-neutral-400">{t("emp360.no_factors")}</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function TimelineTab({ employeeId }: { employeeId: string }) {
  const { t } = useTranslation()
  const [filters, setFilters] = useState<EmployeeTimelineParams>({ page_size: 20 })
  const [showFilters, setShowFilters] = useState(false)
  const [selectedSources, setSelectedSources] = useState<string[]>([])
  const [selectedTypes, setSelectedTypes] = useState<string[]>([])
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [allEvents, setAllEvents] = useState<NonNullable<ReturnType<typeof useEmployeeTimeline>["data"]>["events"]>([])
  const [cursorStack, setCursorStack] = useState<string[]>([])
  const listEndRef = useRef<HTMLDivElement>(null)

  const queryParams = useMemo(() => ({
    ...filters,
    source: selectedSources.length > 0 ? selectedSources : undefined,
    type: selectedTypes.length > 0 ? selectedTypes : undefined,
    from: dateFrom || undefined,
    to: dateTo || undefined,
  }), [filters, selectedSources, selectedTypes, dateFrom, dateTo])

  const { data, isLoading, isError, error, refetch } = useEmployeeTimeline(employeeId, queryParams)

  useEffect(() => {
    if (data?.events) {
      setAllEvents(data.events)
    }
  }, [data])

  const handleLoadMore = useCallback(() => {
    if (data?.next_cursor) {
      setCursorStack((prev) => [...prev, filters.cursor || ""])
      setFilters((prev) => ({ ...prev, cursor: data.next_cursor || undefined }))
    }
  }, [data, filters.cursor])

  const handleApplyFilters = useCallback(() => {
    setFilters((prev) => ({ ...prev, cursor: undefined }))
    setCursorStack([])
  }, [])

  const handleClearFilters = useCallback(() => {
    setSelectedSources([])
    setSelectedTypes([])
    setDateFrom("")
    setDateTo("")
    setFilters({ page_size: 20 })
    setCursorStack([])
  }, [])

  const handleToggleSource = useCallback((source: string) => {
    setSelectedSources((prev) => prev.includes(source) ? prev.filter((s) => s !== source) : [...prev, source])
  }, [])

  const handleToggleType = useCallback((type: string) => {
    setSelectedTypes((prev) => prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type])
  }, [])

  const hasActiveFilters = selectedSources.length > 0 || selectedTypes.length > 0 || dateFrom || dateTo

  if (isLoading && allEvents.length === 0) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-12 rounded-xl" />
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex gap-3 animate-pulse">
              <div className="h-8 w-8 rounded-full bg-neutral-200 dark:bg-neutral-700" />
              <div className="flex-1 space-y-1.5">
                <div className="h-3 w-3/4 rounded bg-neutral-200 dark:bg-neutral-700" />
                <div className="h-2 w-1/2 rounded bg-neutral-200 dark:bg-neutral-700" />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="py-12">
        <ErrorFallback title={t("emp360.timeline_error")} message={(error as Error)?.message} onRetry={() => refetch()} />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">{t("emp360.timeline_title")}</h3>
        <div className="flex items-center gap-2">
          {hasActiveFilters && (
            <button onClick={handleClearFilters} className="inline-flex items-center gap-1 text-xs text-[var(--muhide-orange)] hover:underline">
              <X className="h-3 w-3" /> {t("emp360.clear_filters")}
            </button>
          )}
          <Button
            variant="outline"
            size="sm"
            leftIcon={<Filter className="h-3 w-3" />}
            onClick={() => setShowFilters(!showFilters)}
          >
            {t("emp360.filters")}
            {hasActiveFilters && <Badge variant="primary" className="ml-1 text-[10px]">{selectedSources.length + selectedTypes.length + (dateFrom ? 1 : 0) + (dateTo ? 1 : 0)}</Badge>}
          </Button>
        </div>
      </div>

      {showFilters && (
        <Card>
          <CardContent className="py-4">
            <div className="space-y-4">
              <div>
                <label className="mb-2 block text-xs font-medium text-neutral-700 dark:text-neutral-300">{t("emp360.filter_source")}</label>
                <div className="flex flex-wrap gap-1.5">
                  {SOURCE_OPTIONS.map((source) => (
                    <button
                      key={source}
                      onClick={() => handleToggleSource(source)}
                      className={cn(
                        "inline-flex items-center rounded-lg px-2.5 py-1 text-xs font-medium transition-colors",
                        selectedSources.includes(source)
                          ? "bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] border border-[var(--muhide-orange)]/30"
                          : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200 dark:bg-neutral-800 dark:text-neutral-400 dark:hover:bg-neutral-700 border border-transparent"
                      )}
                    >
                      {source}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="mb-2 block text-xs font-medium text-neutral-700 dark:text-neutral-300">{t("emp360.filter_type")}</label>
                <div className="flex flex-wrap gap-1.5">
                  {TYPE_OPTIONS.map((type) => (
                    <button
                      key={type}
                      onClick={() => handleToggleType(type)}
                      className={cn(
                        "inline-flex items-center rounded-lg px-2.5 py-1 text-xs font-medium transition-colors",
                        selectedTypes.includes(type)
                          ? "bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] border border-[var(--muhide-orange)]/30"
                          : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200 dark:bg-neutral-800 dark:text-neutral-400 dark:hover:bg-neutral-700 border border-transparent"
                      )}
                    >
                      {type.replace(/_/g, " ")}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex gap-4">
                <div>
                  <label className="mb-1 block text-xs font-medium text-neutral-700 dark:text-neutral-300">{t("emp360.filter_from")}</label>
                  <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="rounded-lg border border-neutral-200 bg-white px-3 py-1.5 text-xs dark:border-neutral-700 dark:bg-neutral-800" />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-neutral-700 dark:text-neutral-300">{t("emp360.filter_to")}</label>
                  <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="rounded-lg border border-neutral-200 bg-white px-3 py-1.5 text-xs dark:border-neutral-700 dark:bg-neutral-800" />
                </div>
              </div>
              <Button size="sm" onClick={handleApplyFilters}>{t("emp360.apply_filters")}</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {allEvents.length === 0 && !isLoading ? (
        <div className="py-12">
          <EmptyState icon={<Clock className="h-10 w-10" />} title={t("emp360.no_timeline_events")} description={hasActiveFilters ? t("emp360.try_different_filters") : t("emp360.no_activity")} />
        </div>
      ) : (
        <div className="space-y-0">
          {allEvents.map((event, idx) => {
            const config = actionConfig[event.action] || { icon: Clock, color: "text-neutral-600 bg-neutral-100" }
            const Icon = config.icon
            return (
              <div key={event.id} className="relative flex gap-3 pb-4 last:pb-0">
                {idx < allEvents.length - 1 && (
                  <div className="absolute right-[15px] top-10 bottom-0 w-px bg-neutral-200 dark:bg-neutral-700" />
                )}
                <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-full", config.color)}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">{event.title}</p>
                  <p className="mt-0.5 text-xs text-neutral-500 dark:text-neutral-400">
                    <Badge variant="default" className="mr-1 text-[10px]">{event.source_label}</Badge>
                    {event.actor && <span className="mr-1">· {event.actor}</span>}
                    <span>· {formatRelativeTime(event.timestamp)}</span>
                  </p>
                </div>
              </div>
            )
          })}
          <div ref={listEndRef} />
        </div>
      )}

      {data?.has_next && (
        <div className="flex justify-center pt-2">
          <Button variant="outline" size="sm" onClick={handleLoadMore} leftIcon={<ChevronDown className="h-4 w-4" />}>
            {t("emp360.load_more")}
          </Button>
        </div>
      )}

      {data && !data.has_next && allEvents.length > 0 && (
        <p className="text-center text-xs text-neutral-400 pt-2">{t("emp360.all_events_loaded")}</p>
      )}
    </div>
  )
}

function PerformanceTab({ employeeId }: { employeeId: string }) {
  const { t } = useTranslation()
  const { data: performance, isLoading, isError, error, refetch } = useEmployeePerformance(employeeId)

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Skeleton className="h-64 rounded-xl" />
          <Skeleton className="h-64 rounded-xl" />
        </div>
        <Skeleton className="h-48 rounded-xl" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="py-12">
        <ErrorFallback title={t("emp360.performance_error")} message={(error as Error)?.message} onRetry={() => refetch()} />
      </div>
    )
  }

  if (!performance) {
    return (
      <div className="py-12">
        <EmptyState icon={<TrendingUp className="h-10 w-10" />} title={t("emp360.no_performance")} description={t("emp360.no_performance_hint")} />
      </div>
    )
  }

  const maxScore = Math.max(...performance.score_trend.map((p) => p.score), 100)
  const trendDirIcon = performance.score_trend_direction === "up" ? <TrendingUp className="h-4 w-4 text-success-500" /> :
    performance.score_trend_direction === "down" ? <TrendingDown className="h-4 w-4 text-danger-500" /> :
    <Minus className="h-4 w-4 text-neutral-400" />

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-success-600" />
                <h3 className="text-sm font-semibold">{t("emp360.score_trend")}</h3>
              </div>
              <div className="flex items-center gap-1 text-sm">
                {trendDirIcon}
                <span className="text-xs text-neutral-400 capitalize">{performance.score_trend_direction}</span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {performance.score_trend.length === 0 ? (
              <p className="text-xs text-neutral-400 text-center py-8">{t("emp360.no_trend_data")}</p>
            ) : (
              <div className="relative h-48 w-full">
                <svg className="h-full w-full" viewBox="0 0 400 150" preserveAspectRatio="none">
                  <defs>
                    <linearGradient id="trend-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stopColor="var(--muhide-orange)" stopOpacity="0.3" />
                      <stop offset="100%" stopColor="var(--muhide-orange)" stopOpacity="0.02" />
                    </linearGradient>
                  </defs>
                  <path
                    d={`M0,${150 - (performance.score_trend[0]?.score || 0) / maxScore * 140} ${performance.score_trend.map((p, i) => `L${(i / Math.max(1, performance.score_trend.length - 1)) * 400},${150 - p.score / maxScore * 140}`).join(" ")} L400,150 L0,150 Z`}
                    fill="url(#trend-gradient)"
                  />
                  <polyline
                    points={performance.score_trend.map((p, i) => `${(i / Math.max(1, performance.score_trend.length - 1)) * 400},${150 - p.score / maxScore * 140}`).join(" ")}
                    fill="none"
                    stroke="var(--muhide-orange)"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  {performance.score_trend.map((p, i) => (
                    <circle
                      key={i}
                      cx={(i / Math.max(1, performance.score_trend.length - 1)) * 400}
                      cy={150 - p.score / maxScore * 140}
                      r="3"
                      fill="var(--muhide-orange)"
                    />
                  ))}
                </svg>
                <div className="absolute bottom-0 left-0 right-0 flex justify-between text-[10px] text-neutral-400">
                  <span>{performance.score_trend[0]?.date}</span>
                  <span>{performance.score_trend[performance.score_trend.length - 1]?.date}</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-purple-600" />
              <h3 className="text-sm font-semibold">{t("emp360.peer_comparison")}</h3>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {performance.peer_comparison.map((p) => {
                const maxVal = Math.max(p.employee_value, p.department_avg, 1)
                return (
                  <div key={p.metric}>
                    <p className="mb-1.5 text-xs font-medium text-neutral-700 dark:text-neutral-300">{p.label}</p>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="w-16 text-[10px] text-neutral-500">{t("emp360.you")}</span>
                        <div className="h-3 flex-1 overflow-hidden rounded-full bg-neutral-100 dark:bg-neutral-800">
                          <div className="h-full rounded-full bg-[var(--muhide-orange)]" style={{ width: `${(p.employee_value / maxVal) * 100}%` }} />
                        </div>
                        <span className="w-8 text-right text-[10px] font-medium text-neutral-900 dark:text-neutral-100">{Math.round(p.employee_value)}%</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="w-16 text-[10px] text-neutral-500">{t("emp360.dept_avg")}</span>
                        <div className="h-3 flex-1 overflow-hidden rounded-full bg-neutral-100 dark:bg-neutral-800">
                          <div className="h-full rounded-full bg-neutral-400 dark:bg-neutral-600" style={{ width: `${(p.department_avg / maxVal) * 100}%` }} />
                        </div>
                        <span className="w-8 text-right text-[10px] font-medium text-neutral-900 dark:text-neutral-100">{Math.round(p.department_avg)}%</span>
                      </div>
                    </div>
                  </div>
                )
              })}
              {performance.peer_comparison.length === 0 && (
                <p className="text-xs text-neutral-400 text-center py-4">{t("emp360.no_comparison")}</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {performance.risk_flags.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-warning-600" />
              <h3 className="text-sm font-semibold">{t("emp360.risk_flags")}</h3>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              {performance.risk_flags.map((flag) => {
                const severityConfig = {
                  high: { bg: "bg-danger-50 dark:bg-danger-900/20", border: "border-danger-200 dark:border-danger-800", icon: <AlertTriangle className="h-4 w-4 text-danger-600" />, badge: "danger" as const },
                  medium: { bg: "bg-warning-50 dark:bg-warning-900/20", border: "border-warning-200 dark:border-warning-800", icon: <Target className="h-4 w-4 text-warning-600" />, badge: "warning" as const },
                  low: { bg: "bg-success-50 dark:bg-success-900/20", border: "border-success-200 dark:border-success-800", icon: <CheckCircle className="h-4 w-4 text-success-600" />, badge: "success" as const },
                }
                const cfg = severityConfig[flag.severity]
                return (
                  <div key={flag.type} className={cn("flex items-start gap-3 rounded-lg border p-3", cfg.bg, cfg.border)}>
                    {cfg.icon}
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">{flag.label}</span>
                        <Badge variant={cfg.badge} className="text-[10px]">{flag.severity}</Badge>
                      </div>
                      <p className="mt-0.5 text-xs text-neutral-600 dark:text-neutral-400">{flag.description}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {performance.factors.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-neutral-500" />
              <h3 className="text-sm font-semibold">{t("emp360.factors_breakdown")}</h3>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {performance.factors.map((f) => (
                <div key={f.name}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-neutral-700 dark:text-neutral-300">{f.label}</span>
                    <span className="font-medium text-neutral-900 dark:text-neutral-100">+{f.contribution}</span>
                  </div>
                  <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-neutral-100 dark:bg-neutral-800">
                    <div className="h-full rounded-full bg-[var(--muhide-orange)]" style={{ width: `${Math.min(100, f.contribution * 5)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

interface Employee360PageProps {
  employeeId: string
}

export function Employee360Page({ employeeId }: Employee360PageProps) {
  const { t } = useTranslation()
  const { data, isLoading, isError, error, refetch } = useEmployee360(employeeId)
  const [activeTab, setActiveTab] = useState<TabId>("overview")

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-40" />
        <div className="h-10 rounded-lg bg-neutral-100 dark:bg-neutral-800" />
        <OverviewSkeleton />
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="py-20">
        <EmptyState
          icon={<User className="h-12 w-12" />}
          title={t("emp360.load_error")}
          description={(error as Error)?.message || t("emp360.load_error_hint")}
          action={{ label: t("common.back"), onClick: () => window.history.back() }}
        />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabId)}>
        <TabsList className="flex items-center gap-1 overflow-x-auto rounded-xl border border-neutral-200 bg-white px-2 py-1 dark:border-neutral-700 dark:bg-neutral-900">
          {TABS.map((tab) => {
            const Icon = tab.icon
            return (
              <Tab
                key={tab.id}
                value={tab.id}
                className="flex items-center gap-1.5 whitespace-nowrap rounded-lg border-b-0 px-3 py-2 data-[state=active]:bg-[var(--muhide-orange)]/10 data-[state=active]:text-[var(--muhide-orange)] data-[state=active]:border-b-0 dark:data-[state=active]:bg-[var(--muhide-orange)]/20 dark:data-[state=active]:text-orange-300"
              >
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{t(tab.labelKey)}</span>
              </Tab>
            )
          })}
        </TabsList>

        <TabsPanel value="overview">
          <OverviewTab employeeId={employeeId} data={data} />
        </TabsPanel>

        <TabsPanel value="signals">
          <SignalsTab employeeId={employeeId} />
        </TabsPanel>

        <TabsPanel value="scoring">
          <ScoringTab employeeId={employeeId} />
        </TabsPanel>

        <TabsPanel value="timeline">
          <TimelineTab employeeId={employeeId} />
        </TabsPanel>

        <TabsPanel value="performance">
          <PerformanceTab employeeId={employeeId} />
        </TabsPanel>
      </Tabs>
    </div>
  )
}
