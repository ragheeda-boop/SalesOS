"use client"

import { HealthScoreCard } from "./HealthScoreCard"
import { ActiveUsersWidget } from "./ActiveUsersWidget"
import { AdoptionChart } from "./AdoptionChart"
import { NBAAcceptanceWidget } from "./NBAAcceptanceWidget"
import { SearchSuccessWidget } from "./SearchSuccessWidget"
import { TenantHealthList } from "./TenantHealthList"

interface CustomerSuccessData {
  health_score: number
  dau: number
  wau: number
  mau: number
  adoption: { feature: string; label: string; user_count: number; total_users: number; adoption_pct: number }[]
  nba_views: number
  nba_accepts: number
  nba_rejects: number
  acceptance_rate: number
  total_searches: number
  searches_with_action: number
  success_rate: number
  tenants: { tenant_id: string; tenant_name: string; score: number; status: string; color: string; components: Record<string, { weight: number; value: number; contribution: number }>; user_count: number; last_active: string | null; renewal_risk: boolean; days_in_low_health: number }[]
}

interface CustomerSuccessViewProps {
  data: CustomerSuccessData
}

export function CustomerSuccessView({ data }: CustomerSuccessViewProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <HealthScoreCard score={data.health_score} label="الصحة العامة" thresholds={{ green: 80, yellow: 50 }} />
        <ActiveUsersWidget dau={data.dau} wau={data.wau} mau={data.mau} />
        <NBAAcceptanceWidget nba_views={data.nba_views} nba_accepts={data.nba_accepts} nba_rejects={data.nba_rejects} acceptance_rate={data.acceptance_rate} />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <p className="text-xs text-[var(--text-muted)] mb-3"> تبني الميزات</p>
          <AdoptionChart data={data.adoption} />
        </div>
        <SearchSuccessWidget total_searches={data.total_searches} searches_with_action={data.searches_with_action} success_rate={data.success_rate} />
      </div>

      <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
        <p className="text-xs text-[var(--text-muted)] mb-3">صحة العملاء</p>
        <TenantHealthList tenants={data.tenants} />
      </div>
    </div>
  )
}
