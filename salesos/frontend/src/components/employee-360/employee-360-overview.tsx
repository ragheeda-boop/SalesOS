"use client"

import { useEmployeeSignals, useEmployeeScore } from "@/lib/hooks/employeeQueries"
import { Skeleton, Avatar, Badge } from "@salesos/ui"
import { Phone, Mail, Users } from "lucide-react"
import { useTranslation } from "@/lib/i18n"
import { useEmployeeTimeline } from "@/lib/hooks/employeeQueries"
import { StatBox, ScoreBadge, formatRelativeTime, getActionConfig } from "./employee-360-shared"
import {
  RecentActivityFeed,
  OverviewSkeleton,
} from "./employee-360-expandable"

export { OverviewSkeleton }

function ProfileCard({ data, t }: {
  data: { profile: Record<string, unknown> }
  t: (k: string, vars?: Record<string, string | number>) => string
}) {
  const profile = data.profile as Record<string, unknown>
  const initials = String(profile.full_name || "").split("").map((n: string) => n[0]).join("").slice(0, 2).toUpperCase()

  return (
    <div className="overflow-hidden rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] shadow-muhide-1">
      <div className="h-20 bg-gradient-to-l from-info-600 via-purple-600 to-[var(--muhide-orange)]" />
      <div className="relative px-6 pb-5 pt-0">
        <div className="flex flex-wrap items-end gap-4 -mt-10">
          <Avatar
            src={(profile.avatar_url as string) || undefined}
            alt={profile.full_name as string}
            fallback={initials}
            size="lg"
            className="h-20 w-20 text-xl border-4 border-white shadow-muhide-3"
          />
          <div className="flex-1 pt-2">
            <h1 className="text-xl font-bold text-[var(--text-primary)]">
              {(profile.full_name_ar as string) || (profile.full_name as string)}
            </h1>
            <p className="text-sm text-[var(--text-muted)]">
              {profile.role as string}
              {profile.email && <span className="ms-2">· {profile.email as string}</span>}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={profile.is_active ? "success" : "default"}>
              {profile.is_active ? t("status.active") : t("status.inactive")}
            </Badge>
            {profile.phone && (
              <a href={`tel:${profile.phone}`} className="inline-flex items-center gap-1 rounded-lg border border-[var(--border-default)] px-2 py-1 text-xs text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]">
                <Phone className="h-3 w-3" /> {t("employee.call")}
              </a>
            )}
            {profile.email && (
              <a href={`mailto:${profile.email}`} className="inline-flex items-center gap-1 rounded-lg border border-[var(--border-default)] px-2 py-1 text-xs text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]">
                <Mail className="h-3 w-3" /> {t("employee.email_short")}
              </a>
            )}
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-4 border-t border-[var(--border-subtle)] pt-4">
          {profile.manager && (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-[var(--text-muted)]">{t("employee.manager")}</span>
              <span className="font-medium text-[var(--text-primary)]">
                {String((profile.manager as Record<string, unknown>).full_name || (profile.manager as Record<string, unknown>).name || t("employee.unknown"))}
              </span>
            </div>
          )}
          {Array.isArray(profile.team) && (profile.team as Record<string, unknown>[]).length > 0 && (
            <div className="flex items-center gap-2">
              <Users className="h-3.5 w-3.5 text-[var(--text-disabled)]" />
              <span className="text-xs text-[var(--text-muted)]">{t("employee.team", { count: (profile.team as Record<string, unknown>[]).length })}</span>
              <div className="flex -space-x-2">
                {(profile.team as Record<string, unknown>[]).slice(0, 5).map((member, i) => (
                  <span key={i} title={String(member.full_name || member.name)}>
                    <Avatar
                      size="sm"
                      fallback={String(member.full_name || member.name || "").split("").map((n: string) => n[0]).join("").slice(0, 2).toUpperCase()}
                      className="h-6 w-6 border-2 border-white text-[8px]"
                    />
                  </span>
                ))}
                {(profile.team as Record<string, unknown>[]).length > 5 && (
                  <div className="flex h-6 w-6 items-center justify-center rounded-full border-2 border-white bg-[var(--bg-tertiary)] text-[8px] font-bold text-[var(--text-secondary)]">
                    +{(profile.team as Record<string, unknown>[]).length - 5}
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
  data: { profile: Record<string, unknown> }
  signals: { total?: number } | undefined
  scoreData: { score?: number } | undefined
}) {
  const { t } = useTranslation()
  const riskLevel = scoreData && (scoreData.score ?? 0) < 40 ? "high" : scoreData && (scoreData.score ?? 0) < 70 ? "medium" : "low"
  const riskColor = riskLevel === "high" ? "text-danger-600" : riskLevel === "medium" ? "text-warning-600" : "text-success-600"
  const riskLabel = riskLevel === "high" ? t("emp360.risk.high") : riskLevel === "medium" ? t("emp360.risk.medium") : t("emp360.risk.low")

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      <StatBox icon={Mail} label={t("emp360.total_signals")} value={signals?.total ?? 0} color="bg-info-50 text-info-700 dark:bg-info-900/20 dark:text-info-400" />
      <StatBox icon={Users} label={t("emp360.current_score")} value={scoreData?.score ?? "-"} color="bg-[var(--chart-purple-bg)] text-[var(--text-secondary)] dark:bg-[var(--bg-primary)]/20 dark:text-[var(--chart-purple)]" />
      <StatBox icon={Users} label={t("emp360.risk_level")} value={<span className={riskColor}>{riskLabel}</span>} color={riskLevel === "high" ? "bg-danger-50 text-danger-700 dark:bg-danger-900/20 dark:text-danger-400" : riskLevel === "medium" ? "bg-warning-50 text-warning-700 dark:bg-warning-900/20 dark:text-warning-400" : "bg-success-50 text-success-700 dark:bg-success-900/20 dark:text-success-400"} />
      <StatBox icon={Users} label={t("emp360.tenure")} value={new Date((data.profile.created_at as string) || "").toLocaleDateString("en-US", { month: "short", year: "numeric" })} color="bg-[var(--bg-secondary)] text-[var(--text-secondary)]/50" />
    </div>
  )
}

export function EmployeeOverview({ employeeId, data }: {
  employeeId: string
  data: { profile: Record<string, unknown> } & Record<string, unknown>
}) {
  const { t } = useTranslation()
  const { data: signals, isLoading: signalsLoading } = useEmployeeSignals(employeeId)
  const { data: scoreData, isLoading: scoreLoading } = useEmployeeScore(employeeId)

  if (signalsLoading || scoreLoading) return <OverviewSkeleton />

  return (
    <div className="space-y-4">
      <ProfileCard data={data} t={t} />
      <QuickStatsRow data={data} signals={signals as { total?: number } | undefined} scoreData={scoreData as { score?: number } | undefined} />
      <RecentActivityFeed employeeId={employeeId} />
    </div>
  )
}
