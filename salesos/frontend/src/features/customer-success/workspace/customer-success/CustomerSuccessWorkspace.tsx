"use client"

import { useState } from "react"
import { cn } from "@salesos/ui"
import { useTelemetryOverview } from "@/lib/telemetryQueries"
import { HealthScoreCard } from "../../widgets/customer-success/HealthScoreCard"
import { AdoptionChart } from "../../widgets/customer-success/AdoptionChart"
import { ActiveUsersWidget } from "../../widgets/customer-success/ActiveUsersWidget"
import { SearchSuccessWidget } from "../../widgets/customer-success/SearchSuccessWidget"
import { NBAAcceptanceWidget } from "../../widgets/customer-success/NBAAcceptanceWidget"
import { TenantHealthList } from "../../widgets/customer-success/TenantHealthList"

export function CustomerSuccessWorkspace() {
  const [activeView, setActiveView] = useState<"overview" | "tenants">("overview")
  const { data, isLoading } = useTelemetryOverview()

  if (isLoading || !data) {
    return <div className="animate-pulse h-96 bg-neutral-100 rounded-xl" />
  }

  const { feature_adoption, search_success, nba_acceptance, active_users, avg_adoption_pct } = data

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-display text-[var(--text-primary)]">نجاح العملاء</h1>
        <div className="flex gap-2">
          {(["overview", "tenants"] as const).map((v) => (
            <button
              key={v}
              onClick={() => setActiveView(v)}
              className={cn(
                "px-3 py-1.5 text-sm rounded-lg",
                activeView === v
                  ? "bg-[var(--muhide-orange)] text-white"
                  : "text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]"
              )}
            >
              {v === "overview" ? "نظرة عامة" : "العملاء"}
            </button>
          ))}
        </div>
      </div>

      {activeView === "overview" && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <HealthScoreCard
              score={avg_adoption_pct}
              label="متوسط التبني"
              thresholds={{ green: 80, yellow: 50 }}
            />
            <ActiveUsersWidget
              dau={active_users.dau}
              wau={active_users.wau}
              mau={active_users.mau}
            />
            <SearchSuccessWidget
              total_searches={search_success.total_searches}
              searches_with_action={search_success.searches_with_action}
              success_rate={search_success.success_rate}
            />
            <NBAAcceptanceWidget
              nba_views={nba_acceptance.nba_views}
              nba_accepts={nba_acceptance.nba_accepts}
              nba_rejects={nba_acceptance.nba_rejects}
              acceptance_rate={nba_acceptance.acceptance_rate}
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">تبني الميزات</h3>
              <AdoptionChart data={feature_adoption} />
            </div>
            <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">صحة العملاء</h3>
              <TenantHealthList
                tenants={[
                  {
                    tenant_id: "current",
                    tenant_name: "المستأجر الحالي",
                    score: avg_adoption_pct,
                    status: avg_adoption_pct > 80 ? "healthy" : avg_adoption_pct > 50 ? "warning" : "critical",
                    color: avg_adoption_pct > 80 ? "green" : avg_adoption_pct > 50 ? "yellow" : "red",
                    components: { feature_adoption: { weight: 0.4, value: avg_adoption_pct, contribution: 0 }, search_success: { weight: 0.3, value: search_success.success_rate, contribution: 0 }, nba_acceptance: { weight: 0.3, value: nba_acceptance.acceptance_rate, contribution: 0 } },
                    user_count: active_users.mau,
                    last_active: null,
                    renewal_risk: false,
                    days_in_low_health: 0,
                  },
                ]}
              />
            </div>
          </div>
        </>
      )}

      {activeView === "tenants" && (
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">قائمة العملاء</h3>
          <TenantHealthList
            tenants={[
              {
                tenant_id: "current",
                tenant_name: "المستأجر الحالي",
                score: avg_adoption_pct,
                status: avg_adoption_pct > 80 ? "healthy" : avg_adoption_pct > 50 ? "warning" : "critical",
                color: avg_adoption_pct > 80 ? "green" : avg_adoption_pct > 50 ? "yellow" : "red",
                components: { feature_adoption: { weight: 0.4, value: avg_adoption_pct, contribution: 0 }, search_success: { weight: 0.3, value: search_success.success_rate, contribution: 0 }, nba_acceptance: { weight: 0.3, value: nba_acceptance.acceptance_rate, contribution: 0 } },
                user_count: active_users.mau,
                last_active: null,
                renewal_risk: false,
                days_in_low_health: 0,
              },
            ]}
          />
        </div>
      )}
    </div>
  )
}
